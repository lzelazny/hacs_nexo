"""Nexo Binary Sensor."""

from .nexo_resource import NexoResource


class NexoBinarySensor(NexoResource):
    """Nexo binary sensor resource."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on, False if off, None if unknown."""
        match self.state["value"]:
            case 101:
                return False
            case 102:
                return True
            case _:
                return None
