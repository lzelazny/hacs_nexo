from .nexo_resource import NexoResource
from enum import Enum

class BlindOperation(Enum):
    STOP = 0
    CLOSE = 1
    OPEN = 2
    TOGGLE = 3
    SET_LEVEL = 64

class NexoBlind(NexoResource):
    def __init__(self, web_socket, time_down, time_pulse, time_up, *args, **kwargs):
        super().__init__(web_socket, *args, **kwargs)
        self.time_down = time_down
        self.time_pulse = time_pulse
        self.time_up = time_up

    def close(self):
        self.web_socket.send(self._get_close_message())

    def open(self):
        self.web_socket.send(self._get_open_message())

    def stop(self):
        self.web_socket.send(self._open_close_message(0))

    def setLevel(self, level):
        self.web_socket.send(self._set_position(level))

    def _get_open_message(self):
        return self._open_close_message(BlindOperation.OPEN.value)

    def _get_close_message(self):
        return self._open_close_message(BlindOperation.CLOSE.value)

    def _get_stop_message(self):
        return self._open_close_message(BlindOperation.STOP.value)

    def _open_close_message(self, operation):
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"blind_op":{operation}}}}}'

    def _set_position(self, level):
        nextLevel = 100 - level
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"blind_op":{BlindOperation.SET_LEVEL.value},"blind_level":{nextLevel},"blind_slope":255}}}}'

    def openPercentage (self):
        return 100 - self.state['blind_level']

    def is_opened(self):
        match self.state["blind_level"]:
            case 0:
                return True
            case 100:
                return False
            case _:
                return False

    def is_closed(self):
        match self.state["blind_level"]:
            case 0:
                return False
            case 100:
                return True
            case _:
                return False

    def is_closing(self):
        match self.state["blind_op"]:
            case 0:
                return False
            case 1:
                return True
            case 2:
                return False
            case _:
                return False

    def is_opening(self):
        match self.state["blind_op"]:
            case 0:
                return False
            case 1:
                return False
            case 2:
                return True
            case _:
                return False

    def is_in_move(self):
        match self.state["blind_op"]:
            case 0:
                return False
            case 1:
                return True
            case 2:
                return True
            case _:
                return None
