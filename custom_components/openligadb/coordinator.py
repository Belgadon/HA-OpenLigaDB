"""Data update coordinator for OpenLigaDB."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_URL_CURRENT_GROUP,
    API_URL_SEASON_MATCHES,
    API_URL_TABLE,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    EVENT_OPENLIGADB_GOAL,
    EVENT_OPENLIGADB_MATCH_END,
    EVENT_OPENLIGADB_MATCH_START,
    LIVE_UPDATE_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


def parse_match_date(date_str: str) -> datetime | None:
    """Parse OpenLigaDB ISO datetime string."""
    if not date_str:
        return None
    try:
        # Handle 'Z' or trailing offset if present
        cleaned = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            # Assume UTC / German local time fallback
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception as err:
        _LOGGER.debug("Error parsing date '%s': %s", date_str, err)
        return None


class OpenLigaDBDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching OpenLigaDB data."""

    def __init__(
        self,
        hass: HomeAssistant,
        league_shortcuts: set[tuple[str, str]],
        team_filters: set[tuple[str, str, str]],  # (league_shortcut, season, team_name/id)
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MINUTES),
        )
        self.session = async_get_clientsession(hass)
        self.league_shortcuts = league_shortcuts
        self.team_filters = team_filters
        self._previous_goals: dict[int, int] = {}  # match_id -> count of goals
        self._previous_live_matches: set[int] = set()  # set of live match_ids

    async def _async_fetch_json(self, url: str) -> Any:
        """Fetch JSON data from URL safely."""
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    return await resp.json()
                _LOGGER.warning("OpenLigaDB API returned HTTP %s for %s", resp.status, url)
                return None
        except Exception as err:
            _LOGGER.error("Failed to fetch %s: %s", url, err)
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from OpenLigaDB for leagues and teams."""
        data: dict[str, Any] = {
            "leagues": {},
            "teams": {},
        }

        now = datetime.now(timezone.utc)
        has_active_live_match = False

        # 1. Fetch League Data (Tables & Current Group)
        for league_shortcut, season in self.league_shortcuts:
            table_url = API_URL_TABLE.format(league_shortcut=league_shortcut, season=season)
            group_url = API_URL_CURRENT_GROUP.format(league_shortcut=league_shortcut)

            table_data = await self._async_fetch_json(table_url)
            group_data = await self._async_fetch_json(group_url)

            processed_table = []
            if isinstance(table_data, list):
                for idx, item in enumerate(table_data, start=1):
                    processed_table.append(
                        {
                            "rank": idx,
                            "team_id": item.get("teamInfoId"),
                            "team_name": item.get("teamName"),
                            "short_name": item.get("shortName"),
                            "team_icon_url": item.get("teamIconUrl"),
                            "points": item.get("points"),
                            "matches": item.get("matches"),
                            "won": item.get("won"),
                            "draw": item.get("draw"),
                            "lost": item.get("lost"),
                            "goals": item.get("goals"),
                            "opponent_goals": item.get("opponentGoals"),
                            "goal_diff": item.get("goalDiff"),
                        }
                    )

            data["leagues"][(league_shortcut, season)] = {
                "league_shortcut": league_shortcut,
                "season": season,
                "current_group": group_data if isinstance(group_data, dict) else {},
                "table": processed_table,
            }

        # 2. Fetch Matches for Teams & Process Matches
        for league_shortcut, season, team_identifier in self.team_filters:
            matches_url = API_URL_SEASON_MATCHES.format(
                league_shortcut=league_shortcut, season=season
            )
            matches = await self._async_fetch_json(matches_url)

            if not isinstance(matches, list):
                _LOGGER.warning(
                    "No matches returned for %s / %s", league_shortcut, season
                )
                continue

            # Filter matches involving this team
            team_matches = []
            matched_team_name = team_identifier
            matched_team_id = None
            team_icon = None

            for m in matches:
                t1 = m.get("team1", {})
                t2 = m.get("team2", {})

                is_t1 = (
                    str(t1.get("teamId")) == str(team_identifier)
                    or team_identifier.lower() in str(t1.get("teamName", "")).lower()
                    or team_identifier.lower() in str(t1.get("shortName", "")).lower()
                )
                is_t2 = (
                    str(t2.get("teamId")) == str(team_identifier)
                    or team_identifier.lower() in str(t2.get("teamName", "")).lower()
                    or team_identifier.lower() in str(t2.get("shortName", "")).lower()
                )

                if is_t1 or is_t2:
                    team_matches.append(m)
                    if is_t1:
                        matched_team_name = t1.get("teamName", team_identifier)
                        matched_team_id = t1.get("teamId")
                        team_icon = t1.get("teamIconUrl")
                    elif is_t2:
                        matched_team_name = t2.get("teamName", team_identifier)
                        matched_team_id = t2.get("teamId")
                        team_icon = t2.get("teamIconUrl")

            # Parse and categorize matches: finished (last), current (live), next (upcoming)
            last_match = None
            current_match = None
            next_match = None

            # Sort matches by date
            sorted_matches = sorted(
                team_matches,
                key=lambda x: parse_match_date(x.get("matchDateTime"))
                or datetime.min.replace(tzinfo=timezone.utc),
            )

            for m in sorted_matches:
                m_date = parse_match_date(m.get("matchDateTime"))
                is_finished = m.get("matchIsFinished", False)

                # Determine if match is currently live
                # OpenLigaDB marks matches as not finished, and if current time is around kick-off (+2h window)
                is_live = False
                if m_date and not is_finished:
                    # Live if started within last 2.5 hours or currently happening
                    time_diff = (now - m_date).total_seconds()
                    if -900 <= time_diff <= 9000:  # 15 mins before kick-off to 2.5 hours after
                        is_live = True
                        has_active_live_match = True

                t1 = m.get("team1", {})
                t2 = m.get("team2", {})
                is_home = (
                    matched_team_id == t1.get("teamId")
                    or matched_team_name == t1.get("teamName")
                )
                opponent = t2 if is_home else t1

                # Extract latest score
                match_results = m.get("matchResults", [])
                score_t1 = 0
                score_t2 = 0
                if match_results:
                    # Get highest resultOrderID (final result)
                    final_res = max(match_results, key=lambda r: r.get("resultOrderID", 0))
                    score_t1 = final_res.get("pointsTeam1", 0)
                    score_t2 = final_res.get("pointsTeam2", 0)

                goals_info = [
                    {
                        "minute": g.get("matchMinute"),
                        "player": g.get("goalGetterName"),
                        "score": f"{g.get('scoreTeam1')}:{g.get('scoreTeam2')}",
                        "is_penalty": g.get("isPenalty", False),
                        "is_own_goal": g.get("isOwnGoal", False),
                    }
                    for g in m.get("goals", [])
                ]

                match_dict = {
                    "match_id": m.get("matchID"),
                    "date": m.get("matchDateTime"),
                    "group": m.get("group", {}).get("groupName"),
                    "is_home": is_home,
                    "opponent_name": opponent.get("teamName"),
                    "opponent_short_name": opponent.get("shortName"),
                    "opponent_icon": opponent.get("teamIconUrl"),
                    "score_home": score_t1,
                    "score_away": score_t2,
                    "score_team": score_t1 if is_home else score_t2,
                    "score_opponent": score_t2 if is_home else score_t1,
                    "score_str": f"{score_t1} - {score_t2}" if (match_results or is_finished or is_live) else "-:-",
                    "is_finished": is_finished,
                    "is_live": is_live,
                    "goals": goals_info,
                    "location": f"{m.get('location', {}).get('locationStadium', '')}, {m.get('location', {}).get('locationCity', '')}".strip(", "),
                }

                # Check for Goal & Match Start/End Events
                match_id = m.get("matchID")
                if is_live:
                    current_match = match_dict
                    if match_id not in self._previous_live_matches:
                        self._previous_live_matches.add(match_id)
                        self.hass.bus.async_fire(
                            EVENT_OPENLIGADB_MATCH_START,
                            {
                                "team": matched_team_name,
                                "opponent": opponent.get("teamName"),
                                "match_id": match_id,
                            },
                        )

                    # Check for new goals
                    goals_count = len(goals_info)
                    prev_goals = self._previous_goals.get(match_id, 0)
                    if goals_count > prev_goals and goals_info:
                        latest_goal = goals_info[-1]
                        self._previous_goals[match_id] = goals_count
                        self.hass.bus.async_fire(
                            EVENT_OPENLIGADB_GOAL,
                            {
                                "team": matched_team_name,
                                "opponent": opponent.get("teamName"),
                                "score": match_dict["score_str"],
                                "goal_getter": latest_goal.get("player"),
                                "minute": latest_goal.get("minute"),
                                "match_id": match_id,
                            },
                        )
                elif is_finished:
                    if match_id in self._previous_live_matches:
                        self._previous_live_matches.remove(match_id)
                        self.hass.bus.async_fire(
                            EVENT_OPENLIGADB_MATCH_END,
                            {
                                "team": matched_team_name,
                                "opponent": opponent.get("teamName"),
                                "score": match_dict["score_str"],
                                "match_id": match_id,
                            },
                        )
                    if m_date and m_date <= now:
                        last_match = match_dict
                elif m_date and m_date > now and next_match is None:
                    next_match = match_dict

            data["teams"][(league_shortcut, season, team_identifier)] = {
                "team_name": matched_team_name,
                "team_id": matched_team_id,
                "team_icon": team_icon,
                "league_shortcut": league_shortcut,
                "season": season,
                "last_match": last_match,
                "current_match": current_match,
                "next_match": next_match,
            }

        # Dynamically adjust polling interval based on live matches
        if has_active_live_match:
            _LOGGER.debug("Live match detected. Switching update interval to 60s.")
            self.update_interval = timedelta(seconds=LIVE_UPDATE_INTERVAL_SECONDS)
        else:
            self.update_interval = timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MINUTES)

        return data
