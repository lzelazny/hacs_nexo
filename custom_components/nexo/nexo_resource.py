"""Nexo resource."""

import asyncio
from collections.abc import Callable
import logging
from typing import Final

import websocket


class NexoResource:
    """Base class for Nexo resources."""

    _LOGGER: Final = logging.getLogger(__name__)

    def __init__(self, web_socket, id, name, state, *args, **kwargs) -> None:
        """Initialize the Nexo resource."""
        self.web_socket: websocket = web_socket
        self._id = id
        self._name = name
        self.state = state
        self._callbacks = set()

    @property
    def id(self) -> str:
        """Return the id of the resource."""
        return self._id

    @property
    def name(self) -> str:
        """Return the name of the resource."""
        return self._name

    async def _wrapper(self, awaitable):
        """Return the result of the awaitable."""
        if awaitable is not None:
            return await awaitable()
        return None

    async def _async_send(self, message) -> None:
        """Send a message to the websocket."""
        self.web_socket.send(message)

    async def _async_send_cmd(self, cmd) -> None:
        """Send a command message to the websocket."""
        await self._async_send(f'{{"type":"resource","id":{self.id},"cmd":{{{cmd}}}}}')

    async def _async_send_cmd_operation_custom(self, operation, **kwargs) -> None:
        """Send a custom operation command message to the websocket."""
        cmd = f'"operation":{operation}'
        if kwargs:
            cmd += f",{','.join(f'"{key}":{value}' for key, value in kwargs.items())}"
        await self._async_send_cmd(cmd)

    async def _async_send_cmd_operation(self, operation, value=None) -> None:
        """Send an operation command message to the websocket."""
        if value is None:
            await self._async_send_cmd_operation_custom(operation)
        else:
            await self._async_send_cmd_operation_custom(operation, value=value)

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when the resource state changes."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove a callback."""
        self._callbacks.discard(callback)

    def publish_update(self, _loop) -> None:
        """Notify Home Assistant about a state change."""
        for callback in self._callbacks:
            self._LOGGER.debug(
                "Notifying HA about state change of device id: %s type: %s to state %s",
                self.id,
                self.name,
                self.state,
            )
            asyncio.run_coroutine_threadsafe(self._wrapper(callback), _loop)
