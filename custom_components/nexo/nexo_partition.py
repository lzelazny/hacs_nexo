from nexo_resource import NexoResource


class NexoPartition(NexoResource):
    def __init__(self, web_socket, mode, *args, **kwargs):
        super().__init__(web_socket, *args, **kwargs)
        self.mode = mode
