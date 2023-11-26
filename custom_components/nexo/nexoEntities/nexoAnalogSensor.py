from nexoResource import NexoResource


class NexoAnalogSensor(NexoResource):
    def __init__(self, web_socket, blocked=False, index=0, *args, **kwargs):
        super().__init__(web_socket, *args, **kwargs)

    def get_value(self) -> int:
        return self.state["value"]
