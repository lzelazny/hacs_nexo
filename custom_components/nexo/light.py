"""Nexo Light Entity."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_light import NexoLight
from .nexo_light_dimmable import NexoDimmableLight
from .nexoBridge import NexoBridge

_LOGGER: Final = logging.getLogger(__name__)
BRIGHTNESS_SCALE = (0, 255)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoLight(light) for light in nexo.get_resources_by_type(NexoLight)
    )

    async_add_entities(
        HANexoDimmableLight(light)
        for light in nexo.get_resources_by_type(NexoDimmableLight)
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


class HANexoDimmableLight(HANexoLight):
    """Home Assistant Nexo light."""

    def __init__(self, nexo_light) -> None:
        """Initialize the Nexo Dimmable light."""
        super().__init__(nexo_light)
        self._nexo_light: NexoDimmableLight = nexo_light
        self._attr_supported_color_modes = ColorMode.BRIGHTNESS
        self._attr_color_mode = ColorMode.BRIGHTNESS

    @property
    def brightness(self):
        """Return the brightness of the light."""
        # return value_to_brightness(BRIGHTNESS_SCALE, self._nexo_light.brightness)
        return self._nexo_light.brightness

    @property
    def color_mode(self):
        """Return the color mode of the light."""
        return ColorMode.BRIGHTNESS

    @property
    def supported_color_modes(self):
        """Return the supported color modes for the light."""
        return {ColorMode.BRIGHTNESS}

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        if ATTR_BRIGHTNESS in kwargs:
            await self._nexo_light.async_turn_brightness_on(kwargs[ATTR_BRIGHTNESS])
        else:
            await self._nexo_light.async_turn_on()
