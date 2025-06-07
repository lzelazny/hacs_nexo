"""Nexo temperature."""

from .nexo_analog_sensor import NexoAnalogSensor


class NexoTemperature(NexoAnalogSensor):
    """Nexo temperature sensor."""

    @property
    def value(self) -> float:
        """Return the current temperature value."""
        return super().value / 10
