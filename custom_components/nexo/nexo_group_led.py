"""Nexo LED group resources."""

from .nexo_group_dimmer import NexoGroupDimmer


class NexoGroupLed(NexoGroupDimmer):
    """A group of LEDs controlled through its resource ID."""
