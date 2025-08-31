import asyncio
import logging
from .nexo_resource import NexoResource

_LOGGER = logging.getLogger(__name__)

class NexoDimmer(NexoResource):
    """Nexo Dimmer (ściemnialne światło)."""

    def __init__(self, web_socket, **kwargs):
        super().__init__(web_socket, **kwargs)
        self._is_on = False
        self._brightness = 0
        if "state" in kwargs:
            self._apply_state(kwargs["state"])

    # ====== interfejs dla encji Light ======
    def is_on(self) -> bool:
        return self._is_on

    def brightness(self) -> int:
        return self._brightness

    # ====== sterowanie ======
    async def _async_set_level(self, value: int):
        """
        Ustaw jasność 1..255 -> operation=1, brightness=<...>;
        0 -> OFF (operation=0).
        """
        value = int(value)
        if value <= 0:
            # OFF
            self._is_on = False
            self._brightness = 0
            try:
                _LOGGER.debug("NexoDimmer %s async_turn_off()", self.id)
                await self._async_send_cmd_operation(0)
            except Exception as e:
                _LOGGER.exception("NexoDimmer %s async_turn_off failed: %s", self.id, e)
            return

        # ON + poziom
        value = max(1, min(255, value))
        self._is_on = True
        self._brightness = value
        try:
            _LOGGER.debug("NexoDimmer %s async_set_brightness(%s)", self.id, value)
            # WAŻNE: wg sniffingu aplikacja używa pola 'brightness' (nie 'value')
            await self._async_send_cmd_operation_custom(1, brightness=value)
        except Exception as e:
            _LOGGER.exception("NexoDimmer %s async_set_brightness failed: %s", self.id, e)

    async def async_set_brightness(self, value: int):
        await self._async_set_level(value)

    def set_brightness(self, value: int):
        asyncio.get_event_loop().create_task(self._async_set_level(value))

    async def async_turn_off(self):
        await self._async_set_level(0)

    def turn_off(self):
        asyncio.get_event_loop().create_task(self.async_turn_off())

    async def async_turn_on(self, brightness: int | None = None):
        """
        Włącznik:
        - bez jasności -> operation=4 (ostatnia zapamiętana jasność),
        - z jasnością -> operation=1 + brightness.
        """
        try:
            if brightness is None:
                _LOGGER.debug("NexoDimmer %s async_turn_on() -> operation=4 (last level)", self.id)
                self._is_on = True
                await self._async_send_cmd_operation(4)
            else:
                await self._async_set_level(int(brightness))
        except Exception as e:
            _LOGGER.exception("NexoDimmer %s async_turn_on failed: %s", self.id, e)

    def turn_on(self, brightness: int | None = None):
        asyncio.get_event_loop().create_task(self.async_turn_on(brightness=brightness))

    # ====== aktualizacje z mostka ======
    @property
    def state(self):
        return {"is_on": 1 if self._is_on else 0, "brightness": self._brightness}

    @state.setter
    def state(self, value):
        self._apply_state(value)

    def _apply_state(self, state: dict):
        self._is_on = bool(state.get("is_on", 0))
        self._brightness = int(state.get("brightness", 0))
        _LOGGER.debug(
            "Dimmer %s updated -> is_on=%s brightness=%s",
            self.id, self._is_on, self._brightness
        )
