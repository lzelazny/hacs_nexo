from typing import Callable, Final
import asyncio
import logging
class NexoResource:
    """Common Nexo features"""
    _LOGGER: Final = logging.getLogger(__name__)
    def __init__(
        self, web_socket, id, type, name, state, timestamp, *args, **kwargs
    ) -> None:
        self.web_socket = web_socket
        self.id = id
        self.type = type
        self.name = name
        self.state = state
        self.timestamp = timestamp
        self._callbacks = set()

    async def wrapper(self, awaitable):
        return await awaitable()

    def send(self, message) -> None:
        """Send"""
        self.web_socket.Send(message)

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
            asyncio.run_coroutine_threadsafe(self.wrapper(callback), _loop)