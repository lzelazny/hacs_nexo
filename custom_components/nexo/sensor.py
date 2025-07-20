"""Nexo Sensor Entity."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_analog_sensor import NexoAnalogSensor
from .nexo_temperature import NexoTemperature
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoAnalogSensor(sensor)
        for sensor in nexo.get_resources_by_type(NexoAnalogSensor)
    )
    async_add_entities(
        HANexoTemperatureSensor(temp)
        for temp in nexo.get_resources_by_type(NexoTemperature)
    )


class HANexoAnalogSensor(HANexo, SensorEntity):
    """Home Assistant Nexo analog sensor."""

    def __init__(self, nexo_sensor) -> None:
        """Initialize the Nexo analog sensor."""
        super().__init__(nexo_resource=nexo_sensor)
        self._nexo_sensor: NexoAnalogSensor = nexo_sensor
        self._attr_suggested_display_precision = 0
        self._attr_device_class = None

    @property
    def native_value(self) -> float:
        """Return the current analog sensor value."""
        return self._nexo_sensor.value


class HANexoTemperatureSensor(HANexoAnalogSensor):
    """Home Assistant Nexo temperature sensor."""

    def __init__(self, nexo_sensor) -> None:
        """Initialize the Nexo temperature sensor."""
        super().__init__(nexo_sensor)
        self._attr_suggested_display_precision = 1
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
