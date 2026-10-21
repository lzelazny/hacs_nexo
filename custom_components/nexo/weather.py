"""Expose local Nexo weather observations through Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.weather import WeatherEntity
from homeassistant.const import UnitOfSpeed, UnitOfTemperature
from homeassistant.core import callback

from .const import DOMAIN
from .nexo_weather import NexoWeather

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .nexoBridge import NexoBridge

_PICTO_TO_CONDITION = {
    "SUN": "sunny",
    "MOON": "clear-night",
    "CLOUD": "cloudy",
    "CLOUD_SUN": "partlycloudy",
    "CLOUD_MOON": "partlycloudy",
    "CLOUD_RAIN": "rainy",
    "CLOUD_SHOWERS": "rainy",
    "CLOUD_SNOW": "snowy",
    "CLOUD_THUNDER": "lightning",
    "CLOUD_THUNDER_RAIN": "lightning-rainy",
    "FOG": "fog",
    "WIND": "windy",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create one local weather entity for each configured Nexo bridge."""
    bridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HANexoWeather(bridge, entry.entry_id)])


class HANexoWeather(WeatherEntity):
    """A weather station updated by the Nexo WebSocket connection."""

    _attr_name = "Nexo weather"
    _attr_should_poll = False
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND

    def __init__(self, bridge: NexoBridge, entry_id: str) -> None:
        self._bridge = bridge
        self._attr_unique_id = f"{entry_id}_weather"
        self._weather = NexoWeather()
        self._sync_with_bridge()

    def _sync_with_bridge(self) -> None:
        if resources := self._bridge.get_weather_resources():
            self._weather = resources[0]

    @callback
    def _handle_weather_update(self) -> None:
        self._sync_with_bridge()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._bridge.register_weather_listener(self._handle_weather_update)
        self._sync_with_bridge()

    async def async_will_remove_from_hass(self) -> None:
        self._bridge.unregister_weather_listener(self._handle_weather_update)
        await super().async_will_remove_from_hass()

    @property
    def available(self) -> bool:
        weather = self._weather
        return any((
            weather.temperature_c is not None,
            weather.wind_ms is not None,
            weather.pictogram is not None,
            bool(weather.conditions),
            weather.light_intensity is not None,
            bool(weather.wind_rose),
        ))

    @property
    def condition(self) -> str | None:
        weather = self._weather
        if weather.pictogram in _PICTO_TO_CONDITION:
            return _PICTO_TO_CONDITION[weather.pictogram]
        if weather.conditions.get("rain") in (True, 1):
            return "rainy"
        if weather.conditions.get("wind") in (True, 1):
            return "windy"
        if weather.conditions.get("sun") in (True, 1):
            return "sunny"
        return None

    @property
    def native_temperature(self) -> float | None:
        return self._weather.temperature_c

    @property
    def native_wind_speed(self) -> float | None:
        return self._weather.wind_ms

    @property
    def wind_bearing(self) -> float | None:
        return self._weather.wind_dir_deg

    @property
    def extra_state_attributes(self) -> dict:
        weather = self._weather
        values = {
            "wind_bearing_text": weather.wind_dir_cardinal,
            "wind_rose": dict(weather.wind_rose) or None,
            "light_intensity": weather.light_intensity,
            "light_angle_deg": weather.light_angle,
            "light_quadrants": dict(weather.light_quadrants) or None,
        }
        return {key: value for key, value in values.items() if value is not None}
