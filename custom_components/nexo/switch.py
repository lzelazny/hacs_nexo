"""Nexo Switch Entity."""

from __future__ import annotations

import logging
from typing import Final, Iterable, List

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo  # baza, której używasz w innych platformach
from .nexo_output import NexoOutput

# Opcjonalnie: jeśli dodasz obsługę grup wyjść (group_output) – import defensywny
try:
    from .nexo_group_output import NexoGroupOutput  # type: ignore
except Exception:  # pragma: no cover
    NexoGroupOutput = None  # type: ignore

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nexo switches."""
    nexo = hass.data[DOMAIN][entry.entry_id]

    entities: List[SwitchEntity] = []

    # Zwykłe wyjścia
    outputs: Iterable[NexoOutput] = nexo.get_resources_by_type(NexoOutput)
    _LOGGER.debug("Discovered %d NexoOutput", len(outputs))
    entities.extend(HANexoSwitch(sw) for sw in outputs)

    # Grupowe wyjścia – tylko jeśli klasa jest dostępna
    if NexoGroupOutput is not None:
        group_outputs = nexo.get_resources_by_type(NexoGroupOutput)  # type: ignore[arg-type]
        _LOGGER.debug("Discovered %d NexoGroupOutput", len(group_outputs))
        entities.extend(HANexoGroupSwitch(sw) for sw in group_outputs)
    else:
        _LOGGER.debug("NexoGroupOutput class not found – skipping group outputs")

    if not entities:
        _LOGGER.warning("SWITCH setup finished with 0 entities.")
        return

    _LOGGER.info("Adding %d switch entities to HA", len(entities))
    async_add_entities(entities)


class HANexoSwitch(HANexo, SwitchEntity):
    """Home Assistant Nexo Switch (pojedyncze wyjście)."""

    def __init__(self, nexo_output: NexoOutput) -> None:
        super().__init__(nexo_resource=nexo_output)
        self._nexo_output: NexoOutput = nexo_output

    @property
    def is_on(self) -> bool:
        return bool(self._nexo_output.is_on)

    async def async_turn_on(self):
        await self._nexo_output.async_turn_on()

    async def async_turn_off(self):
        await self._nexo_output.async_turn_off()


class HANexoGroupSwitch(HANexo, SwitchEntity):
    """Home Assistant Nexo Switch (grupowe wyjście)."""

    def __init__(self, nexo_group_output) -> None:
        super().__init__(nexo_resource=nexo_group_output)
        self._nexo_group_output = nexo_group_output

    @property
    def is_on(self) -> bool:
        # implementacja zależna od Twojej klasy NexoGroupOutput – zwykle agregacja OR
        try:
            return bool(getattr(self._nexo_group_output, "is_on", False))
        except Exception:  # pragma: no cover
            return False

    async def async_turn_on(self):
        if hasattr(self._nexo_group_output, "async_turn_on"):
            await self._nexo_group_output.async_turn_on()

    async def async_turn_off(self):
        if hasattr(self._nexo_group_output, "async_turn_off"):
            await self._nexo_group_output.async_turn_off()
