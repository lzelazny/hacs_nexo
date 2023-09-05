"""Support for Nexo Switches."""
from __future__ import annotations
import logging
from typing import Any, Final


from homeassistant.config_entries import ConfigEntry
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .nexoBridge import NexoSensor
from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up"""
    nexo = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    for sensor in nexo.get_resources_by_type(NexoSensor):
        sensors.insert(0, HANexoPIR(sensor))

    async_add_entities(sensors)


class HANexoPIR(BinarySensorEntity):
    """Home Assiant Nexo output"""

    def __init__(self, nexo_sensor) -> None:
        super().__init__()
        self._nexo_sensor = nexo_sensor
        # self._name = nexo_sensor.name
        # self._attr_is_on = self._nexo_sensor.is_on()

    @property
    def unique_id(self) -> str:
        """Return the Id of this Nexo output."""
        return str(self._nexo_sensor.id)

    @property
    def name(self) -> str:
        """Return the display name of this output."""
        return str(self._nexo_sensor.name)

    @property
    def is_on(self) -> bool:
        return self._nexo_sensor.is_on()

    @property
    def device_class(self) -> str:
        return BinarySensorDeviceClass.MOTION

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
