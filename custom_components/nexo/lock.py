"""Lock platform for Nexo integration."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo_gate import NexoGate

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoGate(gate) for gate in nexo.get_resources_by_type(NexoGate)
    )


class HANexoGate(LockEntity):
    """Home Assistant Nexo Climate."""

    def __init__(self, nexo_gate) -> None:
        """Initialize the Nexo gate."""
        super().__init__()
        self._nexo_gate = nexo_gate
        self.__last_is_open = (
            nexo_gate.is_open() if nexo_gate.is_open() is not None else True
        )

    @property
    def name(self) -> str:
        """Return the display name of this output."""
        return str(self._nexo_gate.name)

    @property
    def unique_id(self) -> str:
        """Return the id of this Nexo thermostat."""
        return str(self._nexo_gate.id)

    @property
    def is_open(self) -> bool:
        """Return the state of the gate."""
        return self._nexo_gate.is_open() is True

    @property
    def is_locked(self) -> bool:
        """Return the state of the gate."""
        return self._nexo_gate.is_open() is False

    @property
    def is_opening(self) -> bool:
        """Return the state of the gate."""
        return self.__last_is_open is False & self._nexo_gate.is_open() is None

    @property
    def is_locking(self) -> bool:
        """Return the state of the gate."""
        return self.__last_is_open is True & self._nexo_gate.is_open() is None

    def unlock(self, **kwargs):
        """Unlock the gate."""
        self._nexo_gate.toggle()

    def lock(self, **kwargs):
        """Lock the gate."""
        self._nexo_gate.toggle()

    @callback
    def async_update_state(self) -> None:
        """Update the state of the entity."""
        self.async_write_ha_state()
        self.__last_is_open = self._nexo_gate.is_open()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Nexo Light should also register callbacks to HA when their state changes
        self._nexo_gate.register_callback(self.async_update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._nexo_gate.remove_callback(self.async_update_state)
