from .nexo_resource import NexoResource


class NexoBlind(NexoResource):
    def __init__(self, web_socket, time_down, time_pulse, time_up, *args, **kwargs):
        super().__init__(web_socket, *args, **kwargs)
        self.time_down = time_down
        self.time_pulse = time_pulse
        self.time_up = time_up

    def is_opened(self):
        match self.state["blind_op"]:
            case 0:
                return False
            case 1:
                return True
            case _:
                return None

    def is_in_move(self):
        match self.state["blind_op"]:
            case 2:
                return True
            case _:
                return None
