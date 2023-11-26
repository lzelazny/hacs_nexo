"""Nexwell Nexo Simple Light Support """
from __future__ import annotations
import logging
from typing import Any, Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.light import LightEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .nexo_light import NexoLight
from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up"""
    nexo = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HANexoLight(light) for light in nexo.get_resources_by_type(NexoLight))


class HANexoLight(LightEntity):
    """Home Assistant Nexo light"""

    def __init__(self, nexo_light) -> None:
        super().__init__()
        self._nexolight = nexo_light
        self._name = nexo_light.name
        self._attr_is_on = self._nexolight.is_on()

    @property
    def unique_id(self) -> str:
        """Return the id of this Nexo light."""
        return str(self._nexolight.id)

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return str(self._name)

    @property
    def is_on(self) -> bool:
        return self._nexolight.is_on()

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._nexolight.turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._nexolight.turn_off()

    @callback
    def async_update_state(self) -> None:
        """Notify of internal state update"""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Nexo Light should also register callbacks to HA when their state changes
        self._nexolight.register_callback(self.async_update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._nexolight.remove_callback(self.async_update_state)
