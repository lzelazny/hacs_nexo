"""Nexo thermostat."""

from typing import Final

from .nexo_temperature import NexoTemperature


class NexoThermostat(NexoTemperature):
    """Nexo thermostat resource."""

    _NONE_VALUE: Final = 32767

    def __init__(self, web_socket, min, max, *args, **kwargs) -> None:
        """Initialize the Nexo thermostat resource."""
        super().__init__(web_socket, *args, **kwargs)
        self._min = min
        self._max = max

    @property
    def min(self) -> float:
        """Return the minimum thermostat temperature."""
        return self._min

    @property
    def max(self) -> float:
        """Return the maximum thermostat temperature."""
        return self._max

    @property
    def is_on(self) -> bool:
        """Return whether the thermostat is on."""
        return self.state["is_on"]

    @property
    def is_active(self) -> bool:
        """Return whether the thermostat is active."""
        return self.state["is_active"]

    async def async_turn_on(self) -> None:
        """Turn on the thermostat."""
        await self._async_send_cmd_operation(1, self._NONE_VALUE)

    async def async_turn_off(self) -> None:
        """Turn off the thermostat."""
        await self._async_send_cmd_operation(0, self._NONE_VALUE)

    async def async_toggle(self) -> None:
        """Toggle the thermostat."""
        await self._async_send_cmd_operation(
            1 if not self.is_on else 0, self._NONE_VALUE
        )

    async def async_set_value(self, value) -> None:
        """Set the target temperature."""
        value = int(value * 10)
        await self._async_send_cmd_operation(int(self.is_on), value)
