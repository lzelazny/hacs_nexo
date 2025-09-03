# custom_components/nexo/cover.py
"""Nexo Cover Entity with group support."""

from __future__ import annotations

import logging
from typing import Final, Iterable, List

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexo import HANexo
from .nexoBridge import NexoBridge
from .nexo_blind import NexoBlind, BlindOperation
from .nexo_blind_group import NexoBlindGroup

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nexo covers and cover groups from a config entry."""
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]
    entities: List[CoverEntity] = []

    # Single covers
    blinds: Iterable[NexoBlind] = nexo.get_resources_by_type(NexoBlind)
    for b in blinds:
        entities.append(HANexoBlind(b))

    # Group covers (new)
    groups: Iterable[NexoBlindGroup] = nexo.get_resources_by_type(NexoBlindGroup)
    for g in groups:
        entities.append(HANexoBlindGroup(g))

    _LOGGER.debug(
        "Adding %d cover entities (%d singles, %d groups).",
        len(entities),
        len(list(blinds)),
        len(list(groups)),
    )
    async_add_entities(entities)


class HANexoBlind(HANexo, CoverEntity):
    """Home Assistant Nexo Blind (single)."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, nexo_blind: NexoBlind) -> None:
        super().__init__(nexo_resource=nexo_blind)
        self._blind: NexoBlind = nexo_blind

    @property
    def is_closed(self) -> bool | None:
        try:
            level = int(self._blind.state.get("blind_level", 0))
            return level >= 100
        except Exception:
            return None

    @property
    def is_opening(self) -> bool | None:
        try:
            return int(self._blind.state.get("blind_op", 0)) == BlindOperation.OPEN.value
        except Exception:
            return None

    @property
    def is_closing(self) -> bool | None:
        try:
            return int(self._blind.state.get("blind_op", 0)) == BlindOperation.CLOSE.value
        except Exception:
            return None

    @property
    def current_cover_position(self) -> int | None:
        """Return 0..100 where 0=closed, 100=open for HA."""
        try:
            level = int(self._blind.state.get("blind_level", 0))
            return 100 - level
        except Exception:
            return None

    async def async_open_cover(self) -> None:
        await self._blind.async_open()

    async def async_close_cover(self) -> None:
        await self._blind.async_close()

    async def async_stop_cover(self) -> None:
        await self._blind.async_stop()

    async def async_set_cover_position(self, **kwargs) -> None:
        pos = int(kwargs.get(ATTR_POSITION))
        await self._blind.async_setLevel(pos)


class HANexoBlindGroup(HANexo, CoverEntity):
    """Home Assistant Nexo Blind Group (new)."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, nexo_group: NexoBlindGroup) -> None:
        super().__init__(nexo_resource=nexo_group)
        self._group: NexoBlindGroup = nexo_group
        rid = getattr(nexo_group, "id", None)
        rname = getattr(nexo_group, "name", None)
        self._attr_unique_id = (
            f"{DOMAIN}_cover_group_{rid}" if rid is not None else f"{DOMAIN}_cover_group_{id(self)}"
        )
        if rname:
            self._attr_name = rname

    @property
    def is_closed(self) -> bool | None:
        try:
            level = int(self._group.state.get("blind_level", 0))
            return level >= 100
        except Exception:
            return None

    @property
    def is_opening(self) -> bool | None:
        try:
            return int(self._group.state.get("blind_op", 0)) == BlindOperation.OPEN.value
        except Exception:
            return None

    @property
    def is_closing(self) -> bool | None:
        try:
            return int(self._group.state.get("blind_op", 0)) == BlindOperation.CLOSE.value
        except Exception:
            return None

    @property
    def current_cover_position(self) -> int | None:
        try:
            level = int(self._group.state.get("blind_level", 0))
            return 100 - level
        except Exception:
            return None

    async def async_open_cover(self) -> None:
        # Prefer native methods if the lib grows them
        if hasattr(self._group, "async_open"):
            await getattr(self._group, "async_open")()
            return
        await self._group._async_send_cmd_operation_custom(  # type: ignore[attr-defined]
            BlindOperation.OPEN.value, blind_op=BlindOperation.OPEN.value, blind_slope=255
        )

    async def async_close_cover(self) -> None:
        if hasattr(self._group, "async_close"):
            await getattr(self._group, "async_close")()
            return
        await self._group._async_send_cmd_operation_custom(  # type: ignore[attr-defined]
            BlindOperation.CLOSE.value, blind_op=BlindOperation.CLOSE.value, blind_slope=255
        )

    async def async_stop_cover(self) -> None:
        if hasattr(self._group, "async_stop"):
            await getattr(self._group, "async_stop")()
            return
        await self._group._async_send_cmd_operation_custom(  # type: ignore[attr-defined]
            BlindOperation.STOP.value, blind_op=BlindOperation.STOP.value, blind_slope=255
        )

    async def async_set_cover_position(self, **kwargs) -> None:
        pos = int(kwargs.get(ATTR_POSITION))
        nexo_level = 100 - pos  # HA->Nexo map
        if hasattr(self._group, "async_setLevel"):
            await getattr(self._group, "async_setLevel")(pos)
            return
        await self._group._async_send_cmd_operation_custom(  # type: ignore[attr-defined]
            BlindOperation.SET_LEVEL.value,
            blind_op=BlindOperation.SET_LEVEL.value,
            blind_level=nexo_level,
            blind_slope=255,
        )
