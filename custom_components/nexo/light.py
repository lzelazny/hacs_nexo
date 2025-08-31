"""Support for Nexo lights, dimmers and LEDs (including groups)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .nexoBridge import NexoBridge
from .nexo_light import NexoLight
from .nexo_dimmer import NexoDimmer
from .nexo_led import NexoLed
from .nexo_group_led import NexoGroupLed
from .nexo_group_dimmer import NexoGroupDimmer
from .nexo_resource import NexoResource

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Nexo lights/dimmers/LEDs."""
    _LOGGER.debug("LIGHT platform setup starting...")
    nexo: NexoBridge = hass.data[DOMAIN][entry.entry_id]

    entities: list[LightEntity] = []

    # 1) Zwykłe światła (ON/OFF)
    lights = nexo.get_resources_by_type(NexoLight)

    # 2) „Ściemniacze” – UWAGA: ten zbiór zawiera też grupy i LED-y (dziedziczenie!)
    dimmers_all = nexo.get_resources_by_type(NexoDimmer)

    # 3) Grupy ściemniaczy (podzbiór dimmers_all)
    group_dimmers_all = nexo.get_resources_by_type(NexoGroupDimmer)

    # 4) LED-y (też podzbiór dimmers_all)
    leds = nexo.get_resources_by_type(NexoLed)

    # 5) Grupy LED (podzbiór group_dimmers_all / dimmers_all)
    group_leds = nexo.get_resources_by_type(NexoGroupLed)

    # ── Filtry anty-duplikacyjne ────────────────────────────────────────────────
    # „Prawdziwe” dimmery = ściemniacze, które NIE są LED-em, NIE są grupą ściemniaczy
    # i NIE są grupą LED
    dimmers = [
        d for d in dimmers_all
        if not isinstance(d, (NexoLed, NexoGroupDimmer, NexoGroupLed))
    ]

    # „Prawdziwe” group dimmery = grupowe ściemniacze, które NIE są grupą LED
    group_dimmers = [
        g for g in group_dimmers_all
        if not isinstance(g, NexoGroupLed)
    ]

    _LOGGER.info(
        "Nexo LIGHT discovery: lights=%d, dimmers=%d, group_dimmers=%d, "
        "leds=%d, group_leds=%d",
        len(lights), len(dimmers), len(group_dimmers), len(leds), len(group_leds)
    )

    # ── Tworzenie encji ─────────────────────────────────────────────────────────
    entities.extend(HANexoLight(hass, light) for light in lights)
    entities.extend(HANexoDimmer(hass, dimmer) for dimmer in dimmers)
    entities.extend(HANexoGroupDimmer(hass, gd) for gd in group_dimmers)
    entities.extend(HANexoLed(hass, led) for led in leds)
    entities.extend(HANexoGroupLed(hass, gled) for gled in group_leds)

    if not entities:
        _LOGGER.warning("Nexo LIGHT setup: no entities discovered.")
        return

    _LOGGER.debug("Adding %d light entities to HA", len(entities))
    async_add_entities(entities)


class HANexo(LightEntity):
    """Base class for Nexo light-like entities."""

    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, nexo_resource: NexoResource) -> None:
        self.hass = hass
        self._nexo_resource: NexoResource = nexo_resource
        cls = type(self).__name__.lower()
        rid = getattr(nexo_resource, "id", "unknown")
        name = getattr(nexo_resource, "name", f"Nexo {rid}")
        self._attr_unique_id = f"{DOMAIN}_{cls}_{rid}"
        self._attr_name = name

        async def _async_update_cb() -> None:
            _LOGGER.debug("Entity %s: async update from Nexo", self._attr_unique_id)
            self.async_write_ha_state()

        try:
            nexo_resource.register_callback(_async_update_cb)
        except Exception as e:
            _LOGGER.exception("Entity %s: register_callback failed: %s", self._attr_unique_id, e)

    @property
    def available(self) -> bool:
        return True

    async def async_update(self) -> None:
        """No manual polling; updates come via websocket."""


class HANexoLight(HANexo, LightEntity):
    """Representation of a standard Nexo light (on/off)."""

    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> bool:
        try:
            val = getattr(self._nexo_resource, "is_on", False)
            return bool(val() if callable(val) else val)
        except Exception as e:
            _LOGGER.exception("HANexoLight.is_on failed: %s", e)
            return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            if hasattr(self._nexo_resource, "async_turn_on"):
                await self._nexo_resource.async_turn_on()
            elif hasattr(self._nexo_resource, "turn_on"):
                await self.hass.async_add_executor_job(self._nexo_resource.turn_on)
            else:
                _LOGGER.error("NexoLight has no turn_on method")
        except Exception as e:
            _LOGGER.exception("HANexoLight.turn_on failed: %s", e)

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            if hasattr(self._nexo_resource, "async_turn_off"):
                await self._nexo_resource.async_turn_off()
            elif hasattr(self._nexo_resource, "turn_off"):
                await self.hass.async_add_executor_job(self._nexo_resource.turn_off)
            else:
                _LOGGER.error("NexoLight has no turn_off method")
        except Exception as e:
            _LOGGER.exception("HANexoLight.turn_off failed: %s", e)


class HANexoDimmer(HANexo, LightEntity):
    """Representation of a Nexo dimmer (brightness control)."""

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    @property
    def is_on(self) -> bool:
        try:
            val = getattr(self._nexo_resource, "is_on", False)
            return bool(val() if callable(val) else val)
        except Exception as e:
            _LOGGER.exception("HANexoDimmer.is_on failed: %s", e)
            return False

    @property
    def brightness(self) -> int | None:
        try:
            val = getattr(self._nexo_resource, "brightness", None)
            if val is None:
                return None
            return int(val() if callable(val) else val)
        except Exception as e:
            _LOGGER.exception("HANexoDimmer.brightness failed: %s", e)
            return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
            if hasattr(self._nexo_resource, "async_set_brightness"):
                await self._nexo_resource.async_set_brightness(brightness)
            elif hasattr(self._nexo_resource, "set_brightness"):
                await self.hass.async_add_executor_job(self._nexo_resource.set_brightness, brightness)
            else:
                _LOGGER.error("NexoDimmer has no set_brightness/async_set_brightness")
        except Exception as e:
            _LOGGER.exception("HANexoDimmer.turn_on failed: %s", e)

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            if hasattr(self._nexo_resource, "async_turn_off"):
                await self._nexo_resource.async_turn_off()
            elif hasattr(self._nexo_resource, "turn_off"):
                await self.hass.async_add_executor_job(self._nexo_resource.turn_off)
            else:
                _LOGGER.error("NexoDimmer has no turn_off/async_turn_off")
        except Exception as e:
            _LOGGER.exception("HANexoDimmer.turn_off failed: %s", e)


class HANexoLed(HANexoDimmer):
    """Representation of a Nexo LED dimmable light."""
    # LED zachowuje się jak dimmer – dziedziczymy bez zmian.


class HANexoGroupDimmer(HANexoDimmer):
    """Representation of a Nexo Group Dimmer (group brightness)."""
    # Tak samo jak dimmer – steruje jasnością grupy.


class HANexoGroupLed(HANexoDimmer):
    """Representation of a Nexo Group LED (group brightness)."""
    # Również jak dimmer – ale dla grup LED.
