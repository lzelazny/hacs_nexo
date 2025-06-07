"""Nexo partition."""

from .nexo_resource import NexoResource


class NexoPartition(NexoResource):
    """Nexo partition resource."""

    @property
    def is_armed(self) -> bool:
        """Return True if the partition is armed, False if disarmed."""
        return bool(self.state["is_armed"])

    @property
    def is_suspended(self) -> bool:
        """Return True if the partition is suspended, False otherwise."""
        return bool(self.state["is_suspended"])

    @property
    def is_damaged(self) -> bool:
        """Return True if the partition is damaged, False otherwise."""
        return bool(self.state["is_damaged"])

    @property
    def is_alarming(self) -> bool:
        """Return True if the partition is alarming, False otherwise."""
        return bool(self.state["is_alarming"])

    async def async_arm(self, password) -> None:
        """Arm the partition."""
        await self._async_send_cmd_operation_custom(1, password=f'"{password}"')

    async def async_disarm(self, password) -> None:
        """Disarm the partition."""
        await self._async_send_cmd_operation_custom(0, password=f'"{password}"')
