"""Nexo Group Dimmer."""

from .nexo_resource import NexoResource


class NexoGroupDimmer(NexoResource):
    """Nexo group dimmer resource."""

    def __init__(self, web_socket, ios, *args, **kwargs) -> None:
        """Initialize the Nexo group dimmer resource."""
        super().__init__(web_socket, *args, **kwargs)
        self.ios = ios
