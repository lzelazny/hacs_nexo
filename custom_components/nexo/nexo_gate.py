"""Nexo gate resource."""

from .nexo_resource import NexoResource


class NexoGate(NexoResource):
    """Nexo gate."""

    @property
    def is_open(self) -> bool | None:
        """Return the state of the gate."""
        match self.state["value"]:
            case 1:
                return True
            case 2:
                return False
            case _:
                return None

    async def async_toggle(self):
        """Toggle the gate."""
        await self._async_send_cmd_operation(2)
