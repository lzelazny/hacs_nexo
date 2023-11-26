from nexo_resource import NexoResource


class NexoTemperature(NexoResource):
    def __init__(self, web_socket, max, min, mode, *args, **kwargs):
        super().__init__(web_socket, *args, **kwargs)
        self.max = max
        self.min = min
        self.mode = mode
