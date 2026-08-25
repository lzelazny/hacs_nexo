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
        return self._id

    @property
    def name(self) -> str:
        return self._name

    async def _wrapper(self, awaitable):
        if awaitable is not None:
            return await awaitable()
        return None

    async def _async_send(self, message) -> None:
        """Send a message to the websocket — safe, non-crashing."""
        try:
            self.web_socket.send(message)
        except (
            BrokenPipeError,
            OSError,
            websocket.WebSocketConnectionClosedException,
            websocket.WebSocketException,
        ) as ex:
            self._LOGGER.warning(
                "Nexo WS: send failed for resource id=%s name=%s — "
                "waiting for auto-reconnect. Error: %s",
                self._id,
                self._name,
                ex,
            )
        except Exception as ex:
            self._LOGGER.error(
                "Nexo WS: unexpected send error for resource id=%s: %s",
                self._id,
                ex,
            )

    async def _async_send_cmd(self, cmd) -> None:
        await self._async_send(f'{{"type":"resource","id":{self.id},"cmd":{{{cmd}}}}}')

    async def _async_send_cmd_operation_custom(self, operation, **kwargs) -> None:
        cmd = f'"operation":{operation}'
        if kwargs:
            cmd += f",{','.join(f'\"{key}\":{value}' for key, value in kwargs.items())}"
        await self._async_send_cmd(cmd)

    async def _async_send_cmd_operation(self, operation, value=None) -> None:
        if value is None:
            await self._async_send_cmd_operation_custom(operation)
        else:
            await self._async_send_cmd_operation_custom(operation, value=value)

    def register_callback(self, callback: Callable[[], None]) -> None:
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        self._callbacks.discard(callback)

    def publish_update(self, _loop) -> None:
        for callback in self._callbacks:
            self._LOGGER.debug(
                "Notifying HA about state change of device id: %s type: %s to state %s",
                self.id,
                self.name,
                self.state,
            )
            asyncio.run_coroutine_threadsafe(self._wrapper(callback), _loop)
