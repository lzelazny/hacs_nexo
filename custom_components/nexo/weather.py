"""HA weather entity for Nexo + prognoza dzienna (Open-Meteo)."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Final, Optional

import aiohttp
from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexoBridge import NexoBridge
from .nexo_weather import NexoWeather

_LOGGER: Final = logging.getLogger(__name__)

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


def _conditions_to_condition(flags: dict, fallback_picto: Optional[str]) -> Optional[str]:
    if not isinstance(flags, dict):
        flags = {}
    if flags.get("rain"):
        return "rainy"
    if flags.get("frost"):
        return "snowy"
    if flags.get("wind") and not flags.get("rain"):
        return "windy"
    if flags.get("sun") and not flags.get("rain"):
        if fallback_picto and "CLOUD" in fallback_picto.upper():
            return "partlycloudy"
        return "sunny"
    if fallback_picto:
        return _PICTO_TO_CONDITION.get(fallback_picto.upper(), "cloudy")
    return "cloudy"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HANexoWeather(nexo, hass)], True)


@dataclass
class _ForecastItem:
    dt: str           # ISO data (YYYY-MM-DD)
    t_min_c: float
    t_max_c: float
    cond: str


class HANexoWeather(HANexo, WeatherEntity):
    """Encja pogody Nexo (stan bieżący + prognoza)."""

    _attr_name = "Pogoda (Nexo)"
    _attr_has_entity_name = False
    # >>> kluczowe: włączamy oficjalną prognozę dzienną
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, bridge: NexoBridge, hass: HomeAssistant) -> None:
        super().__init__(nexo_resource=None)
        self._bridge = bridge
        self.hass = hass
        self._wx: NexoWeather = NexoWeather()
        self._forecast: list[_ForecastItem] = []

    def _sync_with_bridge(self) -> None:
        lst = self._bridge.get_weather_resources()
        if lst:
            self._wx = lst[0]

    async def async_added_to_hass(self) -> None:
        self._sync_with_bridge()

        def _on_weather_update():
            self._sync_with_bridge()
            self.async_write_ha_state()

        self._bridge.register_weather_listener(_on_weather_update)

    async def async_will_remove_from_hass(self) -> None:
        # sprzątanie listenera
        def _noop(): ...
        self._bridge.unregister_weather_listener(_noop)

    # ---- bieżące warunki ----

    @property
    def available(self) -> bool:
        return (
            self._wx is not None
            and (
                self._wx.temperature_c is not None
                or self._wx.pictogram is not None
                or bool(self._wx.conditions)
            )
        )

    @property
    def condition(self) -> Optional[str]:
        if self._wx.pictogram:
            cond = _PICTO_TO_CONDITION.get(self._wx.pictogram.upper())
            if cond:
                return cond
        return _conditions_to_condition(self._wx.conditions, self._wx.pictogram)

    @property
    def native_temperature(self) -> Optional[float]:
        return self._wx.temperature_c

    @property
    def native_temperature_unit(self) -> str:
        return UnitOfTemperature.CELSIUS

    @property
    def native_wind_speed(self) -> Optional[float]:
        if self._wx.wind_ms is None:
            return None
        return float(self._wx.wind_ms) * 3.6  # m/s -> km/h

    @property
    def native_wind_speed_unit(self) -> str:
        return UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def wind_bearing(self) -> Optional[float]:
        # HA używa stopni (0° = N)
        return self._wx.wind_dir_deg

    @property
    def extra_state_attributes(self) -> dict:
        attrs: dict = {}

        # Kierunek wiatru – tekst i róża
        if self._wx.wind_dir_cardinal:
            attrs["wind_bearing_text"] = self._wx.wind_dir_cardinal
        if self._wx.wind_rose:
            attrs["wind_rose"] = dict(self._wx.wind_rose)

        # Światło
        if self._wx.light_intensity is not None:
            attrs["light_intensity"] = self._wx.light_intensity
        if self._wx.light_angle is not None:
            attrs["light_angle_deg"] = self._wx.light_angle
        if self._wx.light_quadrants:
            attrs["light_quadrants"] = dict(self._wx.light_quadrants)

        return attrs

    # ---- prognoza na kafelek: oficjalne API forecast_daily ----

    async def async_update(self) -> None:
        # odświeżamy dane prognozy co wywołanie (HA sam dba o throttling)
        await self._fetch_forecast_open_meteo(days=5)

    async def async_forecast_daily(self):
        """Zwróć listę prognoz dziennych w formacie oczekiwanym przez HA."""
        # mapujemy nasze _forecast na słowniki HA:
        # klucze: datetime, condition, temperature (max), templow (min)
        out = []
        for f in self._forecast:
            out.append(
                {
                    "datetime": f.dt,         # YYYY-MM-DD
                    "condition": f.cond,
                    "temperature": f.t_max_c, # max
                    "templow": f.t_min_c,     # min
                }
            )
        return out

    # ---- pobranie prognozy z Open-Meteo ----

    async def _fetch_forecast_open_meteo(self, days: int = 3) -> None:
        lat = self.hass.config.latitude
        lon = self.hass.config.longitude
        if lat is None or lon is None:
            return
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat:.5f}&longitude={lon:.5f}"
            "&daily=temperature_2m_max,temperature_2m_min,weathercode"
            f"&forecast_days={days}&timezone=auto"
        )
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, timeout=10) as r:
                    if r.status != 200:
                        return
                    js = await r.json()
        except Exception as e:
            _LOGGER.debug("Open-Meteo fetch failed: %s", e)
            return

        daily = js.get("daily") or {}
        times = daily.get("time") or []
        tmax = daily.get("temperature_2m_max") or []
        tmin = daily.get("temperature_2m_min") or []
        wcode = daily.get("weathercode") or []

        out: list[_ForecastItem] = []
        for i in range(min(days, len(times))):
            cond = self._weathercode_to_condition(wcode[i] if i < len(wcode) else None)
            out.append(
                _ForecastItem(
                    dt=str(times[i]),
                    t_min_c=float(tmin[i]) if i < len(tmin) else None,
                    t_max_c=float(tmax[i]) if i < len(tmax) else None,
                    cond=cond or "cloudy",
                )
            )
        self._forecast = out

    @staticmethod
    def _weathercode_to_condition(code) -> Optional[str]:
        # minimalne mapowanie WMO -> HA condition
        if code is None:
            return None
        try:
            c = int(code)
        except Exception:
            return None
        if c == 0:
            return "sunny"
        if c in (1, 2, 3):
            return "partlycloudy" if c != 3 else "cloudy"
        if c in (45, 48):
            return "fog"
        if c in (51, 53, 55, 61, 63, 65, 80, 81, 82):
            return "rainy"
        if c in (71, 73, 75, 85, 86):
            return "snowy"
        if c in (95, 96, 99):
            return "lightning-rainy"
        return "cloudy"
