"""Nexo Blind Group."""

from .nexo_resource import NexoResource


class NexoBlindGroup(NexoResource):
    """Nexo blind group resource."""

    def __init__(self, web_socket, ios, *args, **kwargs) -> None:
        """Initialize the Nexo blind group resource."""
        super().__init__(web_socket, *args, **kwargs)
        self.ios = ios
