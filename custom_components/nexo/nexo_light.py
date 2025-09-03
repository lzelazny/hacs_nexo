"""Nexo Light."""
import asyncio
import logging
_LOGGER = logging.getLogger(__name__)

from .nexo_resource_switchable import NexoResourceSwitchable


class NexoLight(NexoResourceSwitchable):
    """Nexo light resource."""

def is_on(self) -> bool:
    """Zwróć stan ON/OFF jako bool.
    Jeśli w stanie przychodzi flaga 'is_on' – użyj jej, w przeciwnym razie rzutuj cały state na bool.
    """
    try:
        st = getattr(self, "state", None)
        if isinstance(st, dict) and "is_on" in st:
            return bool(st["is_on"])
        return bool(st)
    except Exception:
        return False

async def async_turn_on(self) -> None:
    """Włącz światło – standardowy 'operation'=1."""
    try:
        _LOGGER.debug("NexoLight %s async_turn_on()", self.id)
        await self._async_send_cmd_operation(1)
    except Exception as e:
        _LOGGER.exception("NexoLight %s async_turn_on failed: %s", self.id, e)

def turn_on(self) -> None:
    """Sync wrapper dla zgodności z kodem wyżej."""
    asyncio.get_event_loop().create_task(self.async_turn_on())

async def async_turn_off(self) -> None:
    """Wyłącz światło – standardowy 'operation'=0."""
    try:
        _LOGGER.debug("NexoLight %s async_turn_off()", self.id)
        await self._async_send_cmd_operation(0)
    except Exception as e:
        _LOGGER.exception("NexoLight %s async_turn_off failed: %s", self.id, e)

def turn_off(self) -> None:
    """Sync wrapper dla zgodności z kodem wyżej."""
    asyncio.get_event_loop().create_task(self.async_turn_off())