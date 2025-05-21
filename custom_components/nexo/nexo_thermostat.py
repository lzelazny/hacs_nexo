from .nexo_temperature import NexoTemperature
from homeassistant.components.climate.const import (
    HVACAction,
    HVACMode,
)


class NexoThermostat(NexoTemperature):
    """Nexo thermostat sensor"""

    def __init__(self, web_socket, min, max, *args, **kwargs):
        """Initialize the Nexo thermostat sensor."""
        super().__init__(web_socket, *args, **kwargs)
        self.min = min
        self.max = max

    def get_havac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        if bool(self._get_is_on()):
            return HVACMode.HEAT_COOL
        return HVACMode.OFF

    def get_hvac_action(self) -> HVACAction:
        """Return the current HVAC action."""
        if not bool(self._get_is_on()):
            return HVACAction.OFF
        if bool(self.state["is_active"]):
            return HVACAction.COOLING
        return HVACAction.HEATING

    def turn_on(self):
        """Turn on the thermostat."""
        self.web_socket.send(self._get_message(1))

    def turn_off(self):
        """Turn off the thermostat."""
        self.web_socket.send(self._get_message(0))

    def toggle(self):
        """Toggle the thermostat."""
        self.web_socket.send(self._get_message(1 if self._get_is_on() == 0 else 0))

    def set_value(self, value):
        """Set the target temperature."""
        value = int(value * 10)
        self.web_socket.send(self._get_message(self._get_is_on(), value))

    def _get_is_on(self):
        """Return the current state of the thermostat."""
        return self.state["is_on"]

    def _get_message(self, operation, value=32767):
        """Return the message to send to the thermostat."""
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":{operation},"value":{value}}} }}'
