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
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN
from .nexo import HANexo
from .nexo_blind import NexoBlind
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)

AUTO_STOP_MARGIN: Final = 2


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
        self._nexo_blind: NexoBlind = nexo_blind
        self._cancel_auto_stop_timer: CALLBACK_TYPE | None = None
        self._attr_supported_features = (
            CoverEntityFeature.CLOSE
            | CoverEntityFeature.OPEN
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    async def async_added_to_hass(self) -> None:
        """Register for state changes and clear a stale movement state."""
        self._nexo_blind.register_callback(self._handle_update)
        self._schedule_auto_stop()

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks and cancel the pending auto stop."""
        self._nexo_blind.remove_callback(self._handle_update)
        self._cancel_auto_stop()

    def _handle_update(self) -> None:
        self._schedule_auto_stop()
        self.async_write_ha_state()

    def _cancel_auto_stop(self) -> None:
        if self._cancel_auto_stop_timer is not None:
            self._cancel_auto_stop_timer()
            self._cancel_auto_stop_timer = None

    def _schedule_auto_stop(self) -> None:
        """Without position feedback the module never reports the end of a movement."""
        self._cancel_auto_stop()
        run_time = self._nexo_blind.run_time
        if self._nexo_blind.has_position or run_time is None:
            return
        self._cancel_auto_stop_timer = async_call_later(
            self.hass, run_time + AUTO_STOP_MARGIN, self._auto_stop
        )

    async def _auto_stop(self, _now) -> None:
        self._cancel_auto_stop_timer = None
        self._nexo_blind.mark_stopped()
        self.async_write_ha_state()

    @property
    def assumed_state(self) -> bool:
        """Keep open and close enabled when the position is unknown."""
        return not self._nexo_blind.has_position

    @property
    def device_class(self) -> str:
        """Return the device class of this cover."""
        return CoverDeviceClass.BLIND

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self._nexo_blind.open_percentage

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        return self._nexo_blind.is_closed

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closed or not."""
        return self._nexo_blind.is_closing

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is closed or not."""
        return self._nexo_blind.is_opening

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self._nexo_blind.async_open()

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        await self._nexo_blind.async_close()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self._nexo_blind.async_stop()

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        await self._nexo_blind.async_set_level(kwargs["position"])
