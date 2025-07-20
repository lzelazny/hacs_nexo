"""Nexwell Nexo web socket connectivity integration."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .nexoBridge import NEXO_INIT_TIMEOUT, NexoBridge

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
    """Inicjalizacja integracji na podstawie wpisu z UI."""
    ip = dict(entry.data)[CONF_HOST]
    if not ip:
        _LOGGER.error("No IP address found in the entry configuration")
        return False

    client = NexoBridge(hass, ip)
    await client.start()

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][entry.entry_id] = client

    await client.async_wait_for_initial_resources_load(NEXO_INIT_TIMEOUT)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Integration '%s' started", DOMAIN)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop the integration and disconnect the WebSocket client."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    client: NexoBridge = hass.data[DOMAIN].pop(entry.entry_id, None)
    if client:
        await client.stop()

    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    _LOGGER.info("Integracja '%s' zatrzymana", DOMAIN)
    return unload_ok
