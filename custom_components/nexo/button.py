"""Buttons for external commands provided by the local Nexo bridge."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_EXT_COMMANDS, DOMAIN
from .nexoBridge import NexoBridge


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Discover configured commands and commands announced after startup."""
    bridge: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    added: set[str] = set()
    configured = entry.options.get(CONF_EXT_COMMANDS, [])

    def add_commands() -> None:
        commands = set(bridge.get_ext_commands()) | set(configured)
        new_commands = sorted(commands - added)
        if new_commands:
            added.update(new_commands)
            async_add_entities(
                [NexoButton(bridge, entry.entry_id, cmd) for cmd in new_commands]
            )

    bridge.register_command_listener(add_commands)
    entry.async_on_unload(lambda: bridge.unregister_command_listener(add_commands))
    add_commands()


class NexoButton(ButtonEntity):
    """A command always sent through the bridge's current connection."""

    _attr_should_poll = False

    def __init__(self, bridge: NexoBridge, entry_id: str, command: str) -> None:
        self._bridge = bridge
        self._command = command
        self._attr_unique_id = f"{entry_id}_command_{command}"
        self._attr_name = command

    async def async_press(self) -> None:
        """Run the named Nexo automation."""
        await self._bridge.async_send_ext_command(self._command)
