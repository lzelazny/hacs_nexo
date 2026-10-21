"""Nexwell Nexo web socket connectivity integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_PORT, DOMAIN
from .nexoBridge import NexoBridge

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

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
    Platform.WEATHER,
    Platform.BUTTON,
]


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Register the shared JSON inspector and its admin API."""
    # Load frontend support only during integration setup.
    from .inspector import async_setup_inspector  # pylint: disable=import-outside-toplevel

    await async_setup_inspector(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NexoBridge instance and initiate connectivity."""
    if entry.title == "Name of the device":
        hass.config_entries.async_update_entry(entry, title="Karta MM")
    nexo = None
    try:
        ip = dict(entry.data)[CONF_HOST]
        nexo = NexoBridge(ip, entry.data.get(CONF_PORT, DEFAULT_PORT))
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = nexo
        _LOGGER.info("Connecting to multimedia card on IP: %s", ip)

        await nexo.connect()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))
        return True
    except (TimeoutError, OSError) as err:
        if nexo is not None:
            await nexo.disconnect()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        raise ConfigEntryNotReady("Unable to load resources from Nexo") from err
    except asyncio.CancelledError:
        if nexo is not None:
            await nexo.disconnect()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        raise
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Connection Error")
        if nexo is not None:
            await nexo.disconnect()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        nexo = hass.data[DOMAIN].pop(entry.entry_id)
        await nexo.disconnect()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply changes to the configured external commands."""
    await hass.config_entries.async_reload(entry.entry_id)
