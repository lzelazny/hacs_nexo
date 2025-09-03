"""Nexo Switch Entity."""

from __future__ import annotations

import logging
from typing import Final, Iterable, List

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexo_output import NexoOutput

# Opcjonalny import dla grup wyjść – jeśli moduł istnieje
try:
    from .nexo_group_output import NexoGroupOutput  # type: ignore
except Exception:  # pragma: no cover
    NexoGroupOutput = None  # type: ignore

_LOGGER: Final = logging.getLogger(__name__)


def _exact_type(items: Iterable[object], cls: type) -> list:
    """Zwróć wyłącznie obiekty dokładnie danego typu (bez podklas)."""
    return [x for x in items if type(x) is cls]  # noqa: E721


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nexo switches."""
    nexo = hass.data[DOMAIN][entry.entry_id]

    entities: List[SwitchEntity] = []

    # --- Zwykłe wyjścia (dokładny typ) ---
    outputs_all: List[NexoOutput] = list(nexo.get_resources_by_type(NexoOutput))
    plain_outputs: List[NexoOutput] = _exact_type(outputs_all, NexoOutput)  # bez podklas
    _LOGGER.debug(
        "Discovered %d NexoOutput total, %d plain (exact type).",
        len(outputs_all),
        len(plain_outputs),
    )
    entities.extend(HANexoSwitch(sw) for sw in plain_outputs)

    # --- Grupowe wyjścia (jeśli klasa dostępna) ---
    if NexoGroupOutput is not None:
        group_outputs = list(nexo.get_resources_by_type(NexoGroupOutput))  # type: ignore[arg-type]
        _LOGGER.debug("Discovered %d NexoGroupOutput.", len(group_outputs))
        entities.extend(HANexoGroupSwitch(gw) for gw in group_outputs)
    else:
        _LOGGER.debug("NexoGroupOutput class not found – skipping group outputs.")

    if not entities:
        _LOGGER.warning("SWITCH setup finished with 0 entities.")
        return

    _LOGGER.info("Adding %d switch entities to HA.", len(entities))
    async_add_entities(entities)


class HANexoSwitch(HANexo, SwitchEntity):
    """Home Assistant Nexo Switch (pojedyncze wyjście)."""

    def __init__(self, nexo_output: NexoOutput) -> None:
        super().__init__(nexo_resource=nexo_output)
        self._nexo_output: NexoOutput = nexo_output

        # --- Jednoznaczne ID i nazwa (analogicznie do light.py) ---
        cls = type(self).__name__.lower()
        rid = getattr(nexo_output, "id", None)
        rname = getattr(nexo_output, "name", None)

        # {DOMAIN}_{nazwa_klasy}_{id}; fallback gdyby brakowało id
        self._attr_unique_id = (
            f"{DOMAIN}_{cls}_{rid}" if rid is not None else f"{DOMAIN}_{cls}_{id(self)}"
        )
        self._attr_name = rname or (f"Nexo {rid}" if rid is not None else "Nexo Switch")

    @property
    def is_on(self) -> bool:
        return bool(getattr(self._nexo_output, "is_on", False))

    async def async_turn_on(self) -> None:
        await self._nexo_output.async_turn_on()

    async def async_turn_off(self) -> None:
        await self._nexo_output.async_turn_off()


class HANexoGroupSwitch(HANexo, SwitchEntity):
    """Home Assistant Nexo Switch (grupowe wyjście)."""

    def __init__(self, nexo_group_output) -> None:
        super().__init__(nexo_resource=nexo_group_output)
        self._nexo_group_output = nexo_group_output

        # --- Jednoznaczne ID i nazwa (analogicznie do light.py) ---
        cls = type(self).__name__.lower()
        rid = getattr(nexo_group_output, "id", None)
        rname = getattr(nexo_group_output, "name", None)

        self._attr_unique_id = (
            f"{DOMAIN}_{cls}_{rid}" if rid is not None else f"{DOMAIN}_{cls}_{id(self)}"
        )
        self._attr_name = rname or (f"Nexo group {rid}" if rid is not None else "Nexo Group Switch")

    @property
    def is_on(self) -> bool:
        # Implementacja zależna od Twojej klasy NexoGroupOutput (najczęściej OR)
        try:
            return bool(getattr(self._nexo_group_output, "is_on", False))
        except Exception:  # pragma: no cover
            return False

    async def async_turn_on(self) -> None:
        if hasattr(self._nexo_group_output, "async_turn_on"):
            await self._nexo_group_output.async_turn_on()

    async def async_turn_off(self) -> None:
        if hasattr(self._nexo_group_output, "async_turn_off"):
            await self._nexo_group_output.async_turn_off()
