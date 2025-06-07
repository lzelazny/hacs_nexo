"""Nexo Climate Entity."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_thermostat import NexoThermostat
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoClimate(thermostat)
        for thermostat in nexo.get_resources_by_type(NexoThermostat)
    )


class HANexoClimate(HANexo, ClimateEntity):
    """Home Assistant Nexo Climate."""

    def __init__(self, nexo_termostat: NexoThermostat) -> None:
        """Initialize the Nexo Climate."""
        super().__init__(nexo_resource=nexo_termostat)
        self._nexo_termostat: NexoThermostat = nexo_termostat
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
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        if self._nexo_termostat.is_on:
            return HVACMode.HEAT_COOL
        return HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        if not self._nexo_termostat.is_on:
            return HVACAction.OFF
        if self._nexo_termostat.is_active:
            return HVACAction.COOLING
        return HVACAction.HEATING

    @property
    def target_temperature(self) -> float:
        """Return the current temperature."""
        return self._nexo_termostat.value

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self._nexo_termostat.async_turn_off()
        else:
            await self._nexo_termostat.async_turn_on()

    async def async_set_temperature(self, temperature, **kwargs):
        """Set the target temperature."""
        await self._nexo_termostat.async_set_value(temperature)
