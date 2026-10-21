"""Local weather observations received from the Nexo multimedia card."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any


def _number(value: Any) -> float | None:
    """Accept finite measurements without treating booleans as numbers."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            number = float(value)
        except OverflowError:
            return None
        if math.isfinite(number):
            return number
    return None


def _mapping(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _quadrants(value: dict) -> dict[str, float]:
    """Normalize the four compass directions used by Nexo observations."""
    directions = {
        "n": "N", "north": "N", "s": "S", "south": "S",
        "e": "E", "east": "E", "w": "W", "west": "W",
    }
    result = {}
    for key, raw in value.items():
        number = _number(raw)
        if isinstance(key, str) and key.lower() in directions and number is not None:
            result[directions[key.lower()]] = number
    return result


@dataclass
class NexoWeather:
    """Store the most recent valid values from partial set_weather messages."""

    pictogram: str | None = None
    conditions: dict[str, Any] = field(default_factory=dict)
    temperature_c: float | None = None
    wind_ms: float | None = None
    wind_rose: dict[str, float] = field(default_factory=dict)
    wind_dir_deg: float | None = None
    wind_dir_cardinal: str | None = None
    light_intensity: float | None = None
    light_angle: float | None = None
    light_quadrants: dict[str, float] = field(default_factory=dict)

    def update_from_bridge(self, data: dict) -> None:
        """Read the data field of a set_weather message; ignore malformed values."""
        if not isinstance(data, dict):
            return
        device = _mapping(data.get("devices/0"))
        pictogram = device.get("pictogram")
        if isinstance(pictogram, str) and pictogram:
            self.pictogram = pictogram.upper()
        conditions = device.get("conditions")
        if isinstance(conditions, dict):
            self.conditions = dict(conditions)

        air = _mapping(device.get("air"))
        temperature = _number(air.get("temperature"))
        if temperature is not None:
            self.temperature_c = temperature
        wind = _number(air.get("wind"))
        if wind is not None and wind >= 0:
            self.wind_ms = wind

        light = _mapping(device.get("light"))
        intensity = _number(light.get("intensity"))
        if intensity is not None:
            self.light_intensity = intensity
        angle = _number(light.get("angle"))
        if angle is not None:
            self.light_angle = angle
        if quadrants := _quadrants(light):
            self.light_quadrants = quadrants

        rose = _mapping(data.get("state")).get("value")
        if isinstance(rose, dict):
            self.wind_rose = _quadrants(rose)
            east = self.wind_rose.get("E", 0.0) - self.wind_rose.get("W", 0.0)
            north = self.wind_rose.get("N", 0.0) - self.wind_rose.get("S", 0.0)
            self.wind_dir_deg = None
            self.wind_dir_cardinal = None
            if east or north:
                self.wind_dir_deg = math.degrees(math.atan2(east, north)) % 360
                directions = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")
                index = int(self.wind_dir_deg / 22.5 + 0.5) % len(directions)
                self.wind_dir_cardinal = directions[index]
