"""Support for Nexo blinds."""
from __future__ import annotations
import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .nexo_blind import NexoBlind
from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up"""
    nexo = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HANexoBlind(blind) for blind in nexo.get_resources_by_type(NexoBlind))


class HANexoBlind(CoverEntity):
    """Home Assistant Nexo Blind"""

    def __init__(self, nexo_blind) -> None:
        super().__init__()
        self._nexoBlind = nexo_blind
        self._name = nexo_blind.name
        self._attr_supported_features = CoverEntityFeature.CLOSE | CoverEntityFeature.OPEN | CoverEntityFeature.STOP | CoverEntityFeature.SET_POSITION

    @property
    def unique_id(self) -> str:
        """Return the id of this Nexo blind."""
        return str(self._nexoBlind.id)

    @property
    def name(self) -> str:
        """Return the display name of this blind."""
        return str(self._name)

    @property
    def device_class(self) -> str:
        return CoverDeviceClass.BLIND

    @property
    def current_cover_position(self):
        return self._nexoBlind.openPercentage()

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        return self._nexoBlind.is_closed()

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closed or not."""
        return self._nexoBlind.is_closing()

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is closed or not."""
        return self._nexoBlind.is_opening()

    def open_cover(self):
        """Open the cover."""
        self._nexoBlind.open();

    def close_cover(self):
        """Close cover."""
        self._nexoBlind.close();

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self._nexoBlind.stop();

    def set_cover_position(self, **kwargs):
        self._nexoBlind.setLevel(kwargs['position'])
        """Move the cover to a specific position."""

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
