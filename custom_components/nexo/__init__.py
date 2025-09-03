"""Nexwell Nexo web socket connectivity integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Final

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_EXT_COMMANDS
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)

# YAML: nexo:
#   ext_commands:
#     - brama
#     - gn.ogr.
#     - testHA
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_EXT_COMMANDS, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

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


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Read YAML options (ext_commands) as a fallback."""
    yaml_cfg = config.get(DOMAIN) or {}
    yaml_cmds = yaml_cfg.get(CONF_EXT_COMMANDS, [])
    hass.data.setdefault(DOMAIN, {})["yaml_ext_commands"] = yaml_cmds
    if yaml_cmds:
        _LOGGER.info("Loaded %d ext_commands from YAML", len(yaml_cmds))
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NexoBridge instance and initiate connectivity."""
    try:
        ip = dict(entry.data)[CONF_HOST]
        nexo = hass.data.setdefault(DOMAIN, {})[entry.entry_id] = NexoBridge(ip)
        _LOGGER.info("Connecting to multimedia card on IP: %s", ip)
        await nexo.connect()
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Register a helper service to send arbitrary 'ext_command' to Nexo
        async def _handle_send_ext_command(call):
            cmd = call.data.get("cmd")
            bridge: NexoBridge = hass.data[DOMAIN][entry.entry_id]
            import json
            try:
                bridge.ws.send(json.dumps({"type": "ext_command", "cmd": cmd}))
            except Exception as e:
                _LOGGER.error("Failed to send ext_command %s: %s", cmd, e)

        hass.services.async_register(DOMAIN, "send_ext_command", _handle_send_ext_command)

        return True

    except (asyncio.TimeoutError, OSError) as e:
        _LOGGER.error("Connection error to %s: %s", entry.data.get(CONF_HOST), e)
    except Exception:
        _LOGGER.exception("Unexpected error while setting up Nexo")
    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


# Opcjonalny mostek do OptionsFlow (jeśli kiedyś UI zacznie działać):
async def async_get_options_flow(entry: ConfigEntry):
    from .config_flow import NexoOptionsFlowHandler  # lazy import, by uniknąć cykli
    return NexoOptionsFlowHandler(entry)
