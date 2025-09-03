"""Nexo Button platform for ext_commands."""
from __future__ import annotations

import logging
from typing import Final, Iterable

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_EXT_COMMANDS
from .nexo import HANexo
from .nexoBridge import NexoBridge
from .nexo_command import NexoCommand

_LOGGER: Final = logging.getLogger(__name__)


def _normalize_cmds(values: Iterable[str] | None) -> set[str]:
    if not values:
        return set()
    return {str(v).strip() for v in values if str(v).strip()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    bridge: NexoBridge = hass.data[DOMAIN][entry.entry_id]

    # 1) z bridge (op="modifications")
    try:
        bridge_cmds = _normalize_cmds(bridge.get_ext_commands())
    except Exception:
        bridge_cmds = set()

    # 2) z opcji wpisu (OptionsFlow, jeśli zadziała)
    option_cmds = _normalize_cmds(entry.options.get(CONF_EXT_COMMANDS, []))

    # 3) z YAML (fallback)
    yaml_cmds = _normalize_cmds(hass.data.get(DOMAIN, {}).get("yaml_ext_commands", []))

    cmds = sorted(bridge_cmds | option_cmds | yaml_cmds)

    entities: list[NexoButton] = [NexoButton(NexoCommand(bridge.ws, name=cmd)) for cmd in cmds]

    if not entities:
        _LOGGER.info("Nexo Button: no ext_commands to create (yet).")
        return

    async_add_entities(entities)


class NexoButton(HANexo, ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, nexo_cmd: NexoCommand) -> None:
        HANexo.__init__(self, nexo_cmd)
        ButtonEntity.__init__(self)
        self._nexo_cmd: NexoCommand = nexo_cmd
        self._attr_name = nexo_cmd.name

    async def async_press(self) -> None:
        await self._nexo_cmd.async_press()
