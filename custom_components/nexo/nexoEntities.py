"""Nexo Entities created from JSON messages"""
from typing import Callable, Final
import asyncio
import logging


_LOGGER: Final = logging.getLogger(__name__)


class NexoResource:
    """Common Nexo features"""

    def __init__(
        self, web_socet, id, type, name, state, timestamp, *args, **kwargs
    ) -> None:
        self.web_socet = web_socet
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
        self.web_socet.Send(message)

    def register_callback(self, callback: Callable[[], None]) -> None:
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        self._callbacks.discard(callback)

    def publish_update(self, _loop) -> None:
        for callback in self._callbacks:
            _LOGGER.debug(
                "Notifying HA about state change of device id: %s type: %s to state %s",
                self.id,
                self.name,
                self.state,
            )
            asyncio.run_coroutine_threadsafe(self.wrapper(callback), _loop)


class NexoGate(NexoResource):
    def __init__(self, web_socet, *args, **kwargs) -> None:
        super().__init__(web_socet, *args, **kwargs)


class NexoLight(NexoResource):
    def __init__(self, web_socet, *args, **kwargs):
        super().__init__(web_socet, *args, **kwargs)

    def is_on(self) -> bool:
        return True if self.state["is_on"] > 0 else False

    def turn_on(self):
        self.web_socet.send(self._get_on_message())

    def turn_off(self):
        self.web_socet.send(self._get_off_message())

    def toggle(self):
        self.web_socet.send(self._get_toggle_message())

    def _get_on_message(self):
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":1}} }}'

    def _get_off_message(self):
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":0}} }}'

    def _get_toggle_message(self):
        toggle_state = 1 if self.state["is_on"] > 0 else 0
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":{toggle_state} }} }}'


class NexoOutput(NexoResource):
    def __init__(self, web_socet, *args, **kwargs):
        super().__init__(web_socet, *args, **kwargs)

    def is_on(self) -> bool:
        return True if self.state["is_on"] > 0 else False

    def _get_on_message(self):
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":1}} }}'

    def _get_off_message(self):
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":0}} }}'

    def _get_toggle_message(self):
        toggle_state = 1 if self.state["is_on"] > 0 else 0
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":{toggle_state} }} }}'

    def turn_on(self):
        self.web_socet.send(self._get_on_message())

    def turn_off(self):
        self.web_socet.send(self._get_off_message())

    def toggle(self):
        self.web_socet.send(self._get_toggle_message())


class NexoSensor(NexoResource):
    def __init__(self, web_socet, blocked=False, index=0, *args, **kwargs):
        super().__init__(web_socet, *args, **kwargs)

    def is_on(self) -> bool:
        return False if self.state == 101 else True


class NexoAnalogSensor(NexoSensor):
    def __init__(self, web_socet, *args, **kwargs):
        super().__init__(web_socet, *args, **kwargs)


class NexoTemperature(NexoResource):
    def __init__(self, web_socet, max, min, mode, *args, **kwargs):
        super().__init__(web_socet, *args, **kwargs)
        self.max = max
        self.min = min
        self.mode = mode


class NexoBlind(NexoResource):
    def __init__(self, web_socet, time_down, time_pulse, time_up, *args, **kwargs):
        super().__init__(web_socet, *args, **kwargs)
        self.time_down = time_down
        self.time_pulse = time_pulse
        self.time_up = time_up


class NexoBlindGroup(NexoResource):
    def __init__(self, web_socet, ios, *args, **kwargs):
        super().__init__(web_socet, *args, **kwargs)
        self.ios = ios


class NexoGroupDimmer(NexoResource):
    def __init__(self, web_socet, ios, *args, **kwargs):
        super().__init__(web_socet, *args, **kwargs)
        self.ios = ios


class NexoPartition(NexoResource):
    def __init__(self, web_socet, mode, *args, **kwargs):
        super().__init__(web_socet, *args, **kwargs)
        self.mode = mode
