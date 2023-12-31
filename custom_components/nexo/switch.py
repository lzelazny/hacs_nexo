"""Support for Nexo Switches."""
from __future__ import annotations
import logging
from typing import Any, Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .nexo_output import NexoOutput
from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up"""
    nexo = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HANexoOutput(switch) for switch in nexo.get_resources_by_type(NexoOutput))


class HANexoOutput(SwitchEntity):
    """Home Assistant Nexo output"""

    def __init__(self, nexo_output) -> None:
        super().__init__()
        self._nexoOutput = nexo_output
        self._name = nexo_output.name
        self._attr_is_on = self._nexoOutput.is_on()

    @property
    def unique_id(self) -> str:
        """Return the id of this Nexo output."""
        return str(self._nexoOutput.id)

    @property
    def name(self) -> str:
        """Return the display name of this output."""
        return str(self._name)

    @property
    def is_on(self) -> bool:
        return self._nexoOutput.is_on()

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._nexoOutput.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._nexoOutput.turn_off()

    @callback
    def async_update_state(self) -> None:
        """Notify of internal state update"""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Nexo Light should also register callbacks to HA when their state changes
        self._nexoOutput.register_callback(self.async_update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._nexoOutput.remove_callback(self.async_update_state)
