"""Nexo Binary Sensor Entity."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_binary_sensor import NexoBinarySensor
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoBinarySensor(sensor)
        for sensor in nexo.get_resources_by_type(NexoBinarySensor)
    )


class HANexoBinarySensor(HANexo, BinarySensorEntity):
    """Home Assistant Nexo Binary Sensor."""

    def __init__(self, nexo_sensor) -> None:
        """Initialize the Nexo binary sensor."""
        super().__init__(nexo_resource=nexo_sensor)
        self._nexo_sensor: NexoBinarySensor = nexo_sensor

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor."""
        return self._nexo_sensor.is_on

    @property
    def device_class(self) -> str:
        """Return the device class of this binary sensor."""
        return BinarySensorDeviceClass.MOTION
