"""Alarm control panel platform for Nexo integration."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
    CodeFormat,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo_partition import NexoPartition

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoPartition(partition)
        for partition in nexo.get_resources_by_type(NexoPartition)
    )


class HANexoPartition(AlarmControlPanelEntity):
    """Home Assistant Nexo Climate."""

    def __init__(self, nexo_partition) -> None:
        """Initialize the Nexo gate."""
        super().__init__()
        self._attr_code_arm_required = True
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_supported_features = AlarmControlPanelEntityFeature.ARM_AWAY
        self._nexo_partition = nexo_partition

    @property
    def name(self) -> str:
        """Return the display name of this output."""
        return str(self._nexo_partition.name)

    @property
    def unique_id(self) -> str:
        """Return the id of this Nexo pertition."""
        return str(self._nexo_partition.id)

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        """Return the state of the alarm."""
        return self._nexo_partition.get_state()

    def alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        self._nexo_partition.disarm(code)

    def alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        self._nexo_partition.arm(code)

    @callback
    def async_update_state(self) -> None:
        """Update the state of the entity."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        self._nexo_partition.register_callback(self.async_update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        self._nexo_partition.remove_callback(self.async_update_state)
