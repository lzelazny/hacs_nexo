"""Nexo Light Entity."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_light import NexoLight
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoLight(light) for light in nexo.get_resources_by_type(NexoLight)
    )


class HANexoLight(HANexo, LightEntity):
    """Home Assistant Nexo light."""

    def __init__(self, nexo_light) -> None:
        """Initialize the Nexo light."""
        super().__init__(nexo_resource=nexo_light)
        self._nexo_light: NexoLight = nexo_light
        self._attr_supported_color_modes = ColorMode.ONOFF
        self._attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return self._nexo_light.is_on

    async def async_turn_on(self):
        """Turn device on."""
        await self._nexo_light.async_turn_on()

    async def async_turn_off(self):
        """Turn device off."""
        await self._nexo_light.async_turn_off()
