"""Nexo Switch Entity."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_output import NexoOutput

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up."""
    nexo = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        HANexoSwitch(switch) for switch in nexo.get_resources_by_type(NexoOutput)
    )


class HANexoSwitch(HANexo, SwitchEntity):
    """Home Assistant Nexo Switch."""

    def __init__(self, nexo_output) -> None:
        """Initialize the Nexo switch."""
        super().__init__(nexo_resource=nexo_output)
        self._nexo_Output: NexoOutput = nexo_output

    @property
    def is_on(self) -> bool:
        """Return the state of the switch."""
        return self._nexo_Output.is_on

    async def async_turn_on(self):
        """Turn the entity on."""
        await self._nexo_Output.async_turn_on()

    async def async_turn_off(self):
        """Turn the entity off."""
        await self._nexo_Output.async_turn_off()
