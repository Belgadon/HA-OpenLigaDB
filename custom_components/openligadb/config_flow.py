"""Config flow for OpenLigaDB integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    API_URL_AVAILABLE_TEAMS,
    CONF_ENTRY_TYPE,
    CONF_ENTRY_TYPE_LEAGUE,
    CONF_ENTRY_TYPE_TEAM,
    CONF_LEAGUE_SHORTCUT,
    CONF_SEASON,
    CONF_TEAM_NAME,
    DOMAIN,
    PREDEFINED_LEAGUES,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SEASON = "2024"


class OpenLigaDBConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenLigaDB."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow state."""
        self._entry_type: str | None = None
        self._league_shortcut: str = "bl1"
        self._season: str = DEFAULT_SEASON

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 1: Select whether to add a Team or a League Table."""
        if user_input is not None:
            self._entry_type = user_input[CONF_ENTRY_TYPE]
            if self._entry_type == CONF_ENTRY_TYPE_LEAGUE:
                return await self.async_step_league()
            return await self.async_step_team_league_select()

        schema = vol.Schema(
            {
                vol.Required(CONF_ENTRY_TYPE, default=CONF_ENTRY_TYPE_TEAM): vol.In(
                    {
                        CONF_ENTRY_TYPE_TEAM: "Team Sensor (Next/Last Match, Status)",
                        CONF_ENTRY_TYPE_LEAGUE: "League Sensor (Standings & Matchday)",
                    }
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_league(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Configure a League Table sensor."""
        errors: dict[str, str] = {}

        if user_input is not None:
            shortcut = user_input[CONF_LEAGUE_SHORTCUT].lower().strip()
            season = str(user_input[CONF_SEASON]).strip()

            await self.async_set_unique_id(f"openligadb_league_{shortcut}_{season}")
            self._abort_if_unique_id_configured()

            title = f"League: {shortcut.upper()} ({season})"
            return self.async_create_entry(
                title=title,
                data={
                    CONF_ENTRY_TYPE: CONF_ENTRY_TYPE_LEAGUE,
                    CONF_LEAGUE_SHORTCUT: shortcut,
                    CONF_SEASON: season,
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_LEAGUE_SHORTCUT, default="bl1"): vol.In(
                    PREDEFINED_LEAGUES
                ),
                vol.Required(CONF_SEASON, default=DEFAULT_SEASON): str,
            }
        )

        return self.async_show_form(
            step_id="league", data_schema=schema, errors=errors
        )

    async def async_step_team_league_select(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Select league and season before choosing the team."""
        if user_input is not None:
            self._league_shortcut = user_input[CONF_LEAGUE_SHORTCUT].lower().strip()
            self._season = str(user_input[CONF_SEASON]).strip()
            return await self.async_step_team_select()

        schema = vol.Schema(
            {
                vol.Required(CONF_LEAGUE_SHORTCUT, default="bl1"): vol.In(
                    PREDEFINED_LEAGUES
                ),
                vol.Required(CONF_SEASON, default=DEFAULT_SEASON): str,
            }
        )

        return self.async_show_form(
            step_id="team_league_select", data_schema=schema
        )

    async def async_step_team_select(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Select or enter specific team name."""
        errors: dict[str, str] = {}

        if user_input is not None:
            team_name = user_input[CONF_TEAM_NAME].strip()

            unique_id = f"openligadb_team_{self._league_shortcut}_{self._season}_{team_name}".lower().replace(" ", "_")
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            title = f"Team: {team_name} ({self._league_shortcut.upper()})"
            return self.async_create_entry(
                title=title,
                data={
                    CONF_ENTRY_TYPE: CONF_ENTRY_TYPE_TEAM,
                    CONF_LEAGUE_SHORTCUT: self._league_shortcut,
                    CONF_SEASON: self._season,
                    CONF_TEAM_NAME: team_name,
                },
            )

        # Try fetching available teams for dropdown selection
        teams_dropdown: dict[str, str] = {}
        session = async_get_clientsession(self.hass)
        url = API_URL_AVAILABLE_TEAMS.format(
            league_shortcut=self._league_shortcut, season=self._season
        )

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    team_list = await resp.json()
                    if isinstance(team_list, list):
                        for t in team_list:
                            if isinstance(t, dict):
                                name = t.get("teamName", "").strip()
                                if name:
                                    teams_dropdown[name] = name
        except Exception as err:
            _LOGGER.debug("Could not fetch team dropdown list: %s", err)

        if teams_dropdown:
            schema = vol.Schema(
                {
                    vol.Required(CONF_TEAM_NAME): vol.In(teams_dropdown),
                }
            )
        else:
            schema = vol.Schema(
                {
                    vol.Required(CONF_TEAM_NAME, default="Bayern"): str,
                }
            )

        return self.async_show_form(
            step_id="team_select", data_schema=schema, errors=errors
        )
