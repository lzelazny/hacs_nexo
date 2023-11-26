from .nexo_resource import NexoResource


class NexoBinarySensor(NexoResource):
    def __init__(self, web_socket, blocked=False, index=0, *args, **kwargs):
        super().__init__(web_socket, *args, **kwargs)

    def is_on(self):
        match self.state["value"]:
            case 101:
                return False
            case 102:
                return True
            case _:
                return None
