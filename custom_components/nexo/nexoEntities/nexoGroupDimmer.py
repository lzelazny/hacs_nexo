from nexoResource import NexoResource


class NexoGroupDimmer(NexoResource):
    def __init__(self, web_socket, ios, *args, **kwargs):
        super().__init__(web_socket, *args, **kwargs)
        self.ios = ios
