"""Nexo."""

from __future__ import annotations

import logging
from typing import Final

from .nexo_resource import NexoResource

_LOGGER: Final = logging.getLogger(__name__)


class HANexo:
    """Base for Home Assistant Nexo Entity."""

    def __init__(self, nexo_resource) -> None:
        """Initialize the Nexo resource."""
        self._nexo_resource: NexoResource = nexo_resource

    @property
    def name(self):
        # Jeśli encja sama ustawiła _attr_name (np. weather), użyj tego
        if getattr(self, "_attr_name", None):
            return self._attr_name
        # Jeśli nie ma przypisanego zasobu, zwróć None (HA to akceptuje)
        if self._nexo_resource is None:
            return None
        return str(self._nexo_resource.name)

    @property
    def unique_id(self):
        # Bezpiecznik na brak zasobu
        if self._nexo_resource is None:
            # daj stabilny fallback – jedna encja pogody na integrację
            return "nexo-weather"
        return str(self._nexo_resource.id)

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        # Nexo Light should also register callbacks to HA when their state changes
        self._nexo_resource.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._nexo_resource.remove_callback(self.async_write_ha_state)
