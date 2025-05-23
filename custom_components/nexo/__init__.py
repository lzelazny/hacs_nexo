"""Nexwell Nexo web socket connectivity integration."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)
PLATFORMS: list[Platform | str] = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.LIGHT,
    Platform.LOCK,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NexoBridge instance and initiate connectivity."""
    try:
        ip = dict(entry.data)[CONF_HOST]
        nexo = hass.data.setdefault(DOMAIN, {})[entry.entry_id] = NexoBridge(ip)
        _LOGGER.info("Connecting to multimedia card on IP: %s", ip)

        await nexo.connect()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Connection Error")

    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
