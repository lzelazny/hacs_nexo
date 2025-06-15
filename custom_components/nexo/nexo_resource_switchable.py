"""Nexo resource switchable."""

from .nexo_resource import NexoResource


class NexoResourceSwitchable(NexoResource):
    """Base class for Nexo switchable resources."""

    @property
    def is_on(self) -> bool:
        """Return True if the resource is on, False if off."""
        return bool(self.state["is_on"])

    async def async_turn_on(self) -> None:
        """Turn on."""
        await self._async_send_cmd_operation(1)

    async def async_turn_off(self) -> None:
        """Turn off."""
        await self._async_send_cmd_operation(0)

    async def async_toggle(self) -> None:
        """Toggle state."""
        await self._async_send_cmd_operation(0 if self.is_on else 1)
