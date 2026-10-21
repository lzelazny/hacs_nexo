"""Nexo dimmer resources."""

from .nexo_resource_dimmable import NexoResourceDimmable


class NexoDimmer(NexoResourceDimmable):
    """A dimmer that can restore its last brightness level."""

    async def async_turn_on(self) -> None:
        """Restore the last level reported by the controller."""
        await self._async_send_cmd_operation(4)

    async def async_turn_brightness_on(self, brightness: int) -> None:
        """Set brightness, or turn off for a zero level."""
        level = max(0, min(255, int(brightness)))
        if level == 0:
            await self.async_turn_off()
            return
        await self._async_send_cmd_operation_custom(1, brightness=level)
