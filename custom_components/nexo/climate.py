from __future__ import annotations
import logging
import string
from typing import Any, Final
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.climate import ClimateEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .nexo_thermostat import NexoThermostat
from .const import DOMAIN


_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up"""
    nexo = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoClimate(thermostat)
        for thermostat in nexo.get_resources_by_type(NexoThermostat)
    )


class HANexoClimate(ClimateEntity):
    """Home Assistant Nexo Climate"""

    def __init__(self, nexo_termostat) -> None:
        super().__init__()
        self.nexo_termostat = nexo_termostat
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT_COOL]
        self._attr_hvac_actions = [
            HVACAction.COOLING,
            HVACAction.HEATING,
            HVACAction.OFF,
        ]
        self._attr_target_temperature_low = nexo_termostat.min
        self._attr_target_temperature_high = nexo_termostat.max
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS

    @property
    def name(self) -> str:
        """Return the display name of this output."""
        return str(self.nexo_termostat.name)

    @property
    def unique_id(self) -> str:
        """Return the id of this Nexo thermostat."""
        return str(self.nexo_termostat.id)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        return self.nexo_termostat.get_havac_mode()

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        return self.nexo_termostat.get_hvac_action()

    @property
    def target_temperature(self) -> float:
        """Return the current temperature."""
        return self.nexo_termostat.get_value()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            self.nexo_termostat.turn_off()
        else:
            self.nexo_termostat.turn_on()

    async def async_set_temperature(self, **kwargs):
        """Set the target temperature."""
        self.nexo_termostat.set_value(kwargs["temperature"])

    @callback
    def async_update_state(self) -> None:
        """Update the state of the entity."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Nexo Light should also register callbacks to HA when their state changes
        self.nexo_termostat.register_callback(self.async_update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self.nexo_termostat.remove_callback(self.async_update_state)
