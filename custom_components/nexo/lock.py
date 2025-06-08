"""Nexo Lock Entity."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_gate import NexoGate
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoGate(gate) for gate in nexo.get_resources_by_type(NexoGate)
    )


class HANexoGate(HANexo, LockEntity):
    """Home Assistant Nexo Gate."""

    def __init__(self, nexo_gate: NexoGate) -> None:
        """Initialize the Nexo gate."""
        super().__init__(nexo_resource=nexo_gate)
        self._nexo_gate: NexoGate = nexo_gate
        self._last_is_open: bool = (
            nexo_gate.is_open if nexo_gate.is_open is not None else True
        )

    @property
    def is_open(self) -> bool:
        """Return the state of the gate."""
        return self._nexo_gate.is_open

    @property
    def is_locked(self) -> bool:
        """Return the state of the gate."""
        return not self._nexo_gate.is_open

    @property
    def is_opening(self) -> bool:
        """Return the state of the gate."""
        return (not self._last_is_open) & self._nexo_gate.is_open is None

    @property
    def is_locking(self) -> bool:
        """Return the state of the gate."""
        return self._last_is_open & self._nexo_gate.is_open is None

    async def async_unlock(self):
        """Unlock all or specified locks. A code to unlock the lock with may optionally be specified."""
        await self._nexo_gate.async_toggle()

    async def async_lock(self):
        """Lock all or specified locks. A code to lock the lock with may optionally be specified."""
        await self._nexo_gate.async_toggle()
