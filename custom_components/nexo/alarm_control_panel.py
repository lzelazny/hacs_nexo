"""Nexo Alarm Control Panel Entity."""

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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_partition import NexoPartition
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoPartition(partition)
        for partition in nexo.get_resources_by_type(NexoPartition)
    )


class HANexoPartition(HANexo, AlarmControlPanelEntity):
    """Home Assistant Nexo Climate."""

    def __init__(self, nexo_partition) -> None:
        """Initialize the Nexo gate."""
        super().__init__(nexo_resource=nexo_partition)
        self._attr_code_arm_required = True
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_supported_features = AlarmControlPanelEntityFeature.ARM_AWAY
        self._nexo_partition: NexoPartition = nexo_partition

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        """Return the state of the alarm."""
        if self._nexo_partition.is_damaged:
            return "Damaged"
        if self._nexo_partition.is_suspended:
            return AlarmControlPanelState.PENDING
        if self._nexo_partition.is_alarming:
            return AlarmControlPanelState.TRIGGERED
        if self._nexo_partition.is_armed:
            return AlarmControlPanelState.ARMED_AWAY
        return AlarmControlPanelState.DISARMED

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self._nexo_partition.async_disarm(code)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self._nexo_partition.async_arm(code)
