"""Nexo partition resource definitions."""

from homeassistant.components.alarm_control_panel import AlarmControlPanelState

from .nexo_resource import NexoResource


class NexoPartition(NexoResource):
    """Nexo partition resource."""

    def get_state(self) -> AlarmControlPanelState:
        """Return the state of the partition."""
        if bool(self.state["is_damaged"]):
            return "Damaged"
        if bool(self.state["is_suspended"]):
            return AlarmControlPanelState.PENDING
        if bool(self.state["is_alarming"]):
            return AlarmControlPanelState.TRIGGERED
        if bool(self.state["is_armed"]):
            return AlarmControlPanelState.ARMED_AWAY
        return AlarmControlPanelState.DISARMED

    def arm(self, password):
        """Arm the partition."""
        self.web_socket.send(self._get_message(1, password))

    def disarm(self, password):
        """Disarm the partition."""
        self.web_socket.send(self._get_message(0, password))

    def _get_message(self, operation, password):
        """Return the message to send to the partition."""
        return f'{{"type":"resource","id":{self.id},"cmd":{{"operation":{operation},"password":"{password}"}}}}'
