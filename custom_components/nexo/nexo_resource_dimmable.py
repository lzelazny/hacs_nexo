"""Nexo resource switchable."""

from .nexo_resource_switchable import NexoResourceSwitchable


class NexoResourceDimmable(NexoResourceSwitchable):
    """Base class for Nexo switchable resources."""

    @property
    def brightness(self) -> int:
        """Return brightnes level of the resource."""
        return int(self.state["brightness"])

    async def async_turn_brightness_on(self, brightness) -> None:
        """Turn on."""
        await self._async_send_cmd_operation_custom(1, brightness=f"{brightness}")
