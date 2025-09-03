"""Nexo external command (button)."""
from __future__ import annotations
import json
import logging
from typing import Final
from .nexo_resource import NexoResource

_LOGGER: Final = logging.getLogger(__name__)

class NexoCommand(NexoResource):
    """Represents a Nexo 'ext_command' exposed as a HA button."""

    def __init__(self, web_socket, name: str, **kwargs) -> None:
        fake_id = f"cmd:{name}"
        super().__init__(web_socket, id=fake_id, name=name, state={})
        self._cmd = name

    async def async_press(self) -> None:
        try:
            payload = json.dumps({"type": "ext_command", "cmd": self._cmd})
            self.web_socket.send(payload)  # type: ignore[attr-defined]
            _LOGGER.debug("Sent ext_command: %s", payload)
        except Exception as e:
            _LOGGER.error("Failed to send ext_command %s: %s", self._cmd, e)