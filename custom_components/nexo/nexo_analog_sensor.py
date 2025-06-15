"""Nexo analog sensor."""

from .nexo_resource import NexoResource


class NexoAnalogSensor(NexoResource):
    """Nexo analog sensor resource."""

    @property
    def value(self) -> int:
        """Return the current analog sensor value."""
        return self.state["value"]
