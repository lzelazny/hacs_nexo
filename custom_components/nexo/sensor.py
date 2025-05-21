"""Support for Nexo analog sensor."""
from __future__ import annotations
import logging
import string
from typing import Final
from homeassistant.config_entries import ConfigEntry

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .nexo_analog_sensor import NexoAnalogSensor
from .nexo_temperature import NexoTemperature
from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up"""
    nexo = hass.data[DOMAIN][entry.entry_id]
    sensors = []
    temperature_sensors = []

    for sensor in nexo.get_resources_by_type(NexoAnalogSensor):
        sensors.insert(0, HANexoAnalogSensor(sensor))

    for temp in nexo.get_resources_by_exact_type(NexoTemperature):
        temperature_sensors.insert(0, HANexoTemperatureSensor(temp))

    async_add_entities(sensors)
    async_add_entities(temperature_sensors)

class HANexoTemperatureSensor(SensorEntity):
    """Home Assistant Nexo output"""
    def __init__(self, nexo_sensor) -> None:
        super().__init__()
        self._nexo_sensor = nexo_sensor

    @property
    def unique_id(self) -> str:
        """Return the id of this Nexo output."""
        return str(self._nexo_sensor.id)

    @property
    def name(self) -> str:
        """Return the display name of this output."""
        return str(self._nexo_sensor.name)

    @property
    def native_value(self) -> float:
        return self._nexo_sensor.get_value()

    @property
    def native_unit_of_measurement(self):
        return "°C"

    @property
    def suggested_display_precision(self) -> int:
        return 1

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @callback
    def async_update_state(self) -> None:
        """Notify of internal state update"""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Nexo Light should also register callbacks to HA when their state changes
        self._nexo_sensor.register_callback(self.async_update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._nexo_sensor.remove_callback(self.async_update_state)

class HANexoAnalogSensor(SensorEntity):
    """Home Assistant Nexo output"""

    def __init__(self, nexo_sensor) -> None:
        super().__init__()
        self._nexo_sensor = nexo_sensor

    @property
    def unique_id(self) -> str:
        """Return the id of this Nexo output."""
        return str(self._nexo_sensor.id)

    @property
    def name(self) -> str:
        """Return the display name of this output."""
        return str(self._nexo_sensor.name)

    @property
    def native_value(self) -> int:
        return self._nexo_sensor.get_value()

    @property
    def suggested_display_precision(self) -> int:
        return 0

    @property
    def device_class(self):
        return None

    @callback
    def async_update_state(self) -> None:
        """Notify of internal state update"""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Nexo Light should also register callbacks to HA when their state changes
        self._nexo_sensor.register_callback(self.async_update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._nexo_sensor.remove_callback(self.async_update_state)
