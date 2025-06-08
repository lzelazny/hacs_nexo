"""Nexo Cover Entity."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_blind import NexoBlind
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoBlind(blind) for blind in nexo.get_resources_by_type(NexoBlind)
    )


class HANexoBlind(HANexo, CoverEntity):
    """Home Assistant Nexo Blind."""

    def __init__(self, nexo_blind) -> None:
        """Initialize the Nexo blind."""
        super().__init__(nexo_resource=nexo_blind)
        self._nexo_Blind: NexoBlind = nexo_blind
        self._attr_supported_features = (
            CoverEntityFeature.CLOSE
            | CoverEntityFeature.OPEN
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    @property
    def device_class(self) -> str:
        """Return the device class of this cover."""
        return CoverDeviceClass.BLIND

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self._nexo_Blind.openPercentage

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        return self._nexo_Blind.is_closed

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closed or not."""
        return self._nexo_Blind.is_closing

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is closed or not."""
        return self._nexo_Blind.is_opening

    async def async_open_cover(self):
        """Open the cover."""
        await self._nexo_Blind.async_open()

    async def async_close_cover(self):
        """Close cover."""
        await self._nexo_Blind.async_close()

    async def async_stop_cover(self):
        """Stop the cover."""
        await self._nexo_Blind.async_stop()

    async def async_set_cover_position(self, position):
        """Move the cover to a specific position."""
        await self._nexo_Blind.async_setLevel(position)
