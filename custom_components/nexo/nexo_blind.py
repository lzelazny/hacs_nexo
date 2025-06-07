"""Nexo Blind."""

from enum import Enum

from .nexo_resource import NexoResource


class BlindOperation(Enum):
    """Enum for blind operations."""

    STOP = 0
    CLOSE = 1
    OPEN = 2
    TOGGLE = 3
    SET_LEVEL = 64


class NexoBlind(NexoResource):
    """Nexo blind resource."""

    async def async_close(self) -> None:
        """Close the blind."""
        await self._async_send_cmd(self._get_cmd(BlindOperation.CLOSE.value))

    async def async_open(self) -> None:
        """Open the blind."""
        await self._async_send_cmd(self._get_cmd(BlindOperation.OPEN.value))

    async def async_stop(self) -> None:
        """Stop the blind."""
        await self._async_send_cmd(self._get_cmd(BlindOperation.STOP.value))

    async def async_setLevel(self, level) -> None:
        """Set the blind level."""
        await self._async_send_cmd(
            self._get_cmd_position(BlindOperation.SET_LEVEL.value, level)
        )

    def _get_cmd(self, operation) -> str:
        return f'"blind_op":{operation}'

    def _get_cmd_position(self, operation, level) -> str:
        level = 100 - level
        return f'"blind_op":{operation},"blind_level":{level},"blind_slope":255'

    @property
    def _blind_level(self) -> int:
        return self.state["blind_level"]

    @property
    def _blind_op(self) -> int:
        return self.state["blind_op"]

    @property
    def openPercentage(self) -> int:
        """Return the open percentage of the blind."""
        return 100 - self._blind_level

    @property
    def is_opened(self) -> bool:
        """Return True if the blind is fully opened."""
        return self._blind_level == 0

    @property
    def is_closed(self) -> bool:
        """Return True if the blind is fully closed."""
        return self._blind_level == 100

    @property
    def is_closing(self) -> bool:
        """Return True if the blind is closing."""
        return self._blind_op == 1

    @property
    def is_opening(self) -> bool:
        """Return True if the blind is opening."""
        return self._blind_op == 2

    @property
    def is_in_move(self) -> bool | None:
        """Return True if the blind is moving."""
        match self._blind_op:
            case 0:
                return False
            case 1 | 2:
                return True
            case _:
                return None
