"""Nexo temperature."""

from .nexo_analog_sensor import NexoAnalogSensor


class NexoTemperature(NexoAnalogSensor):
    """Nexo temperature sensor."""

    @property
    def value(self) -> float:
        """Return the current temperature value in °C as float with 1 decimal."""
        # surowa wartość to dziesiętne stopnie (np. 236 -> 23.6 °C)
        raw = super().value
        try:
            return round(raw / 10, 1)
        except Exception:
            # na wszelki wypadek, gdyby raw był None / nie-liczbą
            return 0.0
