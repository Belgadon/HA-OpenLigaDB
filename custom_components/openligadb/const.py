"""Constants for the OpenLigaDB integration."""
from typing import Final

DOMAIN: Final = "openligadb"
DEFAULT_NAME: Final = "OpenLigaDB"

# Update intervals
DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 15
LIVE_UPDATE_INTERVAL_SECONDS: Final = 60

# API Endpoints
API_BASE_URL: Final = "https://api.openligadb.de"
API_URL_TABLE: Final = f"{API_BASE_URL}/getbltable/{{league_shortcut}}/{{season}}"
API_URL_CURRENT_GROUP: Final = f"{API_BASE_URL}/getcurrentgroup/{{league_shortcut}}"
API_URL_SEASON_MATCHES: Final = f"{API_BASE_URL}/getmatchdata/{{league_shortcut}}/{{season}}"
API_URL_MATCHES_TEAM: Final = f"{API_BASE_URL}/getmatchdata/{{league_shortcut}}/{{season}}/{{team_filter}}"
API_URL_NEXT_MATCH: Final = f"{API_BASE_URL}/getnextmatchbyleagueteam/{{league_id}}/{{team_id}}"
API_URL_AVAILABLE_TEAMS: Final = f"{API_BASE_URL}/getavailableteams/{{league_shortcut}}/{{season}}"

# Configuration keys
CONF_ENTRY_TYPE: Final = "entry_type"
CONF_ENTRY_TYPE_TEAM: Final = "team"
CONF_ENTRY_TYPE_LEAGUE: Final = "league"

CONF_LEAGUE_SHORTCUT: Final = "league_shortcut"
CONF_SEASON: Final = "season"
CONF_TEAM_ID: Final = "team_id"
CONF_TEAM_NAME: Final = "team_name"
CONF_LEAGUE_NAME: Final = "league_name"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Predefined leagues (football leagues listed on https://www.openligadb.de/)
PREDEFINED_LEAGUES: Final[dict[str, str]] = {
    # Germany - men
    "bl1": "1. Bundesliga (bl1)",
    "bl2": "2. Bundesliga (bl2)",
    "bl3": "3. Liga (bl3)",
    "dfb": "DFB-Pokal (dfb)",
    "rln": "Regionalliga Nord (rln)",
    "rlno": "Regionalliga Nordost (rlno)",
    "ol1": "Oberliga Niederrhein (OL1)",
    # Germany - women
    "ffb1": "Frauen-Bundesliga (ffb1)",
    # National teams
    "dfbn": "DFB Nationalspiele (DFBN)",
    "nla": "UEFA Nations League A (nla)",
    # European club competitions
    "ucl": "UEFA Champions League (ucl)",
    "uel2026": "UEFA Europa League 2026/27 (uel2026)",
    "uecl2026": "UEFA Conference League 2026/27 (uecl2026)",
    # International leagues
    "pl": "Premier League ENG (pl)",
    "la1": "LaLiga ESP (la1)",
    "atbl1": "Admiral Bundesliga AT (atbl1)",
    "chsl": "Super League CH (chsl)",
}

# Events
EVENT_OPENLIGADB_GOAL: Final = "openligadb_goal"
EVENT_OPENLIGADB_MATCH_START: Final = "openligadb_match_start"
EVENT_OPENLIGADB_MATCH_END: Final = "openligadb_match_end"
