"""Nexo Group Dimmer."""

from .nexo_dimmer import NexoDimmer


class NexoGroupDimmer(NexoDimmer):
    """Nexo group dimmer resource."""

    def __init__(self, web_socket, *args, ios=None, **kwargs) -> None:
        """Initialize the Nexo group dimmer resource."""
        super().__init__(web_socket, *args, **kwargs)
        self.ios = ios
