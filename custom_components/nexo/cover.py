"""Support for Nexo blinds."""
from __future__ import annotations
import logging
from typing import Any, Final


from homeassistant.config_entries import ConfigEntry
from homeassistant.components.cover import CoverEntity, CoverDeviceClass

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .nexoBridge import NexoBlind
from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up"""
    nexo = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HANexoBlind(l) for l in nexo.get_resources_by_type(NexoBlind))


class HANexoBlind(CoverEntity):
    """Home Assiant Nexo Blind"""

    def __init__(self, nexoBlind) -> None:
        super().__init__()
        self._nexoBlind = nexoBlind
        self._name = nexoBlind.name

    @property
    def device_class(self) -> str:
        return CoverDeviceClass.BLIND

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        return not self._nexoBlind.is_opened()

    @callback
    def async_update_state(self) -> None:
        """Notify of internal state update"""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Nexo Light should also register callbacks to HA when their state changes
        self._nexoBlind.register_callback(self.async_update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._nexoBlind.remove_callback(self.async_update_state)