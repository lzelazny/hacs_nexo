from .nexo_resource import NexoResource


class NexoGate(NexoResource):
    def __init__(self, web_socket, *args, **kwargs) -> None:
        super().__init__(web_socket, *args, **kwargs)
