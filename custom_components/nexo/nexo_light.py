from .nexo_resource import NexoResource


class NexoLight(NexoResource):
    def __init__(self, web_socket, *args, **kwargs):
        super().__init__(web_socket, *args, **kwargs)

    def is_on(self) -> bool:
        return True if self.state["is_on"] > 0 else False

    def turn_on(self):
        self.web_socket.send(self._get_on_message())

    def turn_off(self):
        self.web_socket.send(self._get_off_message())

    def toggle(self):
        self.web_socket.send(self._get_toggle_message())

    def _get_on_message(self):
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":1}} }}'

    def _get_off_message(self):
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":0}} }}'

    def _get_toggle_message(self):
        toggle_state = 1 if self.state["is_on"] > 0 else 0
        return f'{{"type": "resource", "id": {self.id}, "cmd":{{"operation":{toggle_state} }} }}'
