"""Nexo gate resource."""

from .nexo_resource import NexoResource


class NexoGate(NexoResource):
    """Nexo gate."""

    def is_open(self) -> bool | None:
        """Return the state of the gate."""
        match self.state["value"]:
            case 1:
                return True
            case 2:
                return False
            case _:
                return None

    def toggle(self):
        """Toggle the gate."""
        self.web_socket.send(self._get_toggle_message())

    def _get_toggle_message(self):
        """Return the message to send to the gate."""
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":2}}}}'
