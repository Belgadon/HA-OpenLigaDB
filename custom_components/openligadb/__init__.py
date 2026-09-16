"""The OpenLigaDB integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ENTRY_TYPE,
    CONF_LEAGUE_SHORTCUT,
    CONF_SEASON,
    CONF_TEAM_NAME,
    DOMAIN,
)
from .coordinator import OpenLigaDBDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenLigaDB from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    league_shortcut = entry.data.get(CONF_LEAGUE_SHORTCUT, "bl1")
    season = str(entry.data.get(CONF_SEASON, "2024"))
    entry_type = entry.data.get(CONF_ENTRY_TYPE)

    league_shortcuts = {(league_shortcut, season)}
    team_filters = set()

    if entry_type == "team":
        team_name = entry.data.get(CONF_TEAM_NAME, "")
        if team_name:
            team_filters.add((league_shortcut, season, team_name))

    # Reuse or create coordinator for this entry
    coordinator = OpenLigaDBDataUpdateCoordinator(
        hass,
        league_shortcuts=league_shortcuts,
        team_filters=team_filters,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
