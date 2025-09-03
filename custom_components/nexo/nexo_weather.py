"""Model danych pogody z mostka Nexo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


def _cardinal_from_degrees(deg: float) -> str:
    # 16-kierunkowa róża
    dirs = [
        "płn.", "płn.-płn.-wsch.", "płn.-wsch.", "wsch.-płn.-wsch.",
        "wsch.", "wsch.-płd.-wsch.", "płd.-wsch.", "płd.-płd.-wsch.",
        "płd.", "płd.-płd.-zach.", "płd.-zach.", "zach.-płd.-zach.",
        "zach.", "zach.-płn.-zach.", "płn.-zach.", "płn.-płn.-zach.",
    ]
    ix = int((deg % 360) / 22.5 + 0.5) % 16
    return dirs[ix]


@dataclass
class NexoWeather:
    # podstawowe
    pictogram: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    temperature_c: Optional[float] = None
    wind_ms: Optional[float] = None

    # wiatr – z róży N/S/E/W (mode==4)
    wind_rose: Dict[str, float] = field(default_factory=dict)  # {"N": 0, "E": ...}
    wind_dir_deg: Optional[float] = None
    wind_dir_cardinal: Optional[str] = None

    # światło
    light_intensity: Optional[int] = None
    light_angle: Optional[int] = None
    light_quadrants: Dict[str, int] = field(default_factory=dict)  # {"N": 0, "S": ...}

    def update_from_bridge(self, data: dict) -> None:
        """Przepisuje dane z pojedynczego opisu 'data' (pole z op=set_weather)."""
        # 1) Piktogram i flagi
        dev0 = data.get("devices/0") or {}
        self.pictogram = dev0.get("pictogram") or self.pictogram
        cond = dev0.get("conditions")
        if isinstance(cond, dict):
            self.conditions = cond

        # 2) Temperatura i wiatr (mode==1/3)
        air = dev0.get("air") or {}
        if isinstance(air.get("temperature"), (int, float)):
            self.temperature_c = float(air["temperature"])
        if isinstance(air.get("wind"), (int, float)):
            self.wind_ms = float(air["wind"])

        # 3) Światło (z devices/0.light)
        light = dev0.get("light") or {}
        if isinstance(light.get("intensity"), (int, float)):
            self.light_intensity = int(light["intensity"])
        if isinstance(light.get("angle"), (int, float)):
            self.light_angle = int(light["angle"])
        # kierunki jasności (E/N/S/W jeśli są)
        lq = {}
        for k in ("N", "S", "E", "W", "north", "south", "east", "west"):
            if k in light and isinstance(light[k], (int, float)):
                lq[k.upper()[0]] = int(light[k])
        if lq:
            self.light_quadrants = lq

        # 4) Wiatr – róża (mode==4)
        #   przykład: state.value: {"N": 0, "S": 11, "E": 8, "W": 6}
        st = data.get("state", {})
        rose = st.get("value")
        if isinstance(rose, dict):
            cleaned = {}
            for k, v in rose.items():
                if isinstance(v, (int, float)) and k and k[0].upper() in ("N", "S", "E", "W"):
                    cleaned[k[0].upper()] = float(v)
            if cleaned:
                self.wind_rose = cleaned
                # wektorowy kierunek z róży (prosty model)
                # oś X: E(+), W(-); oś Y: N(+), S(-)
                ex = cleaned.get("E", 0.0) - cleaned.get("W", 0.0)
                ey = cleaned.get("N", 0.0) - cleaned.get("S", 0.0)
                if ex != 0.0 or ey != 0.0:
                    # kierunek skąd wieje: zamieniamy na azymut meteorologiczny (0=N, 90=E)
                    # atan2(y, x) -> radiany; tutaj chcemy 0°=N, rosnący zgodnie z ruchem wskazówek:
                    # az = (atan2(ex, ey) w rad) -> stopnie
                    import math

                    az = math.degrees(math.atan2(ex, ey))
                    if az < 0:
                        az += 360.0
                    self.wind_dir_deg = az
                    self.wind_dir_cardinal = _cardinal_from_degrees(az)
