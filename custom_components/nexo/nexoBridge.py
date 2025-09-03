import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import logging
from typing import Final, List, Callable, Optional

import rel
import websocket

from .nexo_analog_sensor import NexoAnalogSensor
from .nexo_binary_sensor import NexoBinarySensor
from .nexo_blind import NexoBlind
from .nexo_blind_group import NexoBlindGroup
from .nexo_gate import NexoGate
from .nexo_group_dimmer import NexoGroupDimmer
from .nexo_light import NexoLight
from .nexo_dimmer import NexoDimmer
from .nexo_output import NexoOutput
from .nexo_partition import NexoPartition
from .nexo_resource import NexoResource
from .nexo_temperature import NexoTemperature
from .nexo_thermostat import NexoThermostat
from .nexo_weather import NexoWeather
from .nexo_led import NexoLed
from .nexo_group_led import NexoGroupLed
from .nexo_group_output import NexoGroupOutput

NEXO_INIT_TIMEOUT = 10
NEXO_RECONNECT_TIMEOUT = 5

_LOGGER: Final = logging.getLogger(__name__)


class NexoBridge:
    def __init__(self, local_ip: str) -> None:
        self.__executor = ThreadPoolExecutor(max_workers=1)
        self.ws: Optional[websocket.WebSocketApp] = None
        self.resources: dict[int, NexoResource] = {}
        self.local_ip = local_ip
        self.raw_data_model: dict = {}
        self.initialized = False
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.get_event_loop()

        # Pogoda: jedna instancja + słuchacze powiadomień
        self._weather: List[NexoWeather] = []
        self._weather_listeners: List[Callable[[], None]] = []

        # Lista dostępnych ext_command (zbierana z op="modifications")
        self._ext_commands: set[str] = set()

    # ---------------- Core WS lifecycle ----------------

    async def async_watchdog(self) -> None:
        """Pilnowanie połączenia WebSocket i reconnect."""
        try:
            if self.ws is None or self.ws.sock is None or self.ws.sock.getstatus() != 101:
                _LOGGER.warning("Watchdog: reconnecting websocket...")
                await self.connect()
            else:
                asyncio.get_event_loop().call_later(
                    NEXO_RECONNECT_TIMEOUT,
                    lambda: asyncio.create_task(self.async_watchdog()),
                )
        except Exception as e:
            _LOGGER.exception("Watchdog failure: %s", e)

    def on_open(self, web_socket) -> None:
        _LOGGER.info("Nexo integration started")

    async def wait_for_initial_resources_load(self, timeout: int) -> None:
        """Czeka aż zasoby zostaną utworzone po initial_data."""
        t = timeout
        while not self.initialized and t > 0:
            await asyncio.sleep(1)
            t -= 1

    async def connect(self) -> None:
        """Nawiązanie połączenia, uruchomienie pętli rel i watchdog."""
        _LOGGER.info("Connecting... %s:%s", self.local_ip, 8766)
        _LOGGER.info("Reconnect Timeout %s", NEXO_RECONNECT_TIMEOUT)
        _LOGGER.info("Init Timeout %s", NEXO_INIT_TIMEOUT)

        # odśwież referencję do pętli (po restarcie HA itp.)
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.get_event_loop()

        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass

        self.ws = websocket.WebSocketApp(
            f"ws://{self.local_ip}:8766/",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )

        # Logger dla outgoing
        original_send = self.ws.send

        def logged_send(payload, *args, **kwargs):
            _LOGGER.debug("NexoBridge sent: %s", payload)
            return original_send(payload, *args, **kwargs)

        self.ws.send = logged_send  # type: ignore[method-assign]

        # Start WS w pętli rel z reconnectem i pingami
        self.ws.run_forever(
            dispatcher=rel,
            reconnect=NEXO_RECONNECT_TIMEOUT,
            ping_interval=NEXO_RECONNECT_TIMEOUT,
            ping_payload='{"type":"ping"}',
        )

        if not rel.is_running():
            self.__executor.submit(rel.dispatch)

        await self.wait_for_initial_resources_load(NEXO_INIT_TIMEOUT)
        await self.async_watchdog()

    # ---------------- Message handling ----------------

    def on_message(self, web_socket, message: str) -> None:
        _LOGGER.debug("NexoBridge received: %s", message)
        try:
            json_message = json.loads(message)
        except Exception as e:
            _LOGGER.exception("Invalid JSON from bridge: %s", e)
            return

        op = json_message.get("op")

        if op == "initial_data":
            self.on_message_initial_data(json_message)
            return

        if op == "data_update":
            self.on_message_data_update(json_message)
            return

        if op == "set_weather":
            try:
                self.on_message_set_weather(json_message)
            except Exception as e:
                _LOGGER.exception("Failed to parse set_weather: %s", e)
            return

        if op == "modifications":
            self.on_message_modifications(json_message)
            return

    def on_message_initial_data(self, json_message: dict) -> None:
        _LOGGER.info(
            "Received initial_data with %d resources",
            len(json_message.get("resources", {})),
        )
        # Pierwszy initial_data – budujemy model; kolejne: tylko odświeżamy socket wewnątrz obiektów
        if not self.raw_data_model and json_message:
            self.raw_data_model = json_message
            self.update_resources()
        else:
            self.refresh_resources()

    def update_resources(self) -> None:
        """Tworzy obiekty zasobów na podstawie raw_data_model."""
        self.initialized = False
        self.resources.clear()
        for resource_id in dict(self.raw_data_model.get("resources", {})):
            self.add_resource(self.raw_data_model["resources"][resource_id])
        self.initialized = True
        _LOGGER.info("Resources initialized: %s", list(self.resources.keys()))

    def refresh_resources(self) -> None:
        """Podmienia referencję web_socket w już istniejących obiektach."""
        for resource in self.resources.values():
            resource.web_socket = self.ws

    def on_message_data_update(self, json_message: dict) -> None:
        """Aktualizacje stanów zasobów."""
        resources = json_message.get("resources", {})
        for res in resources:
            item = resources[res]
            resource = self.get_resource_by_id(item.get("id"))
            if resource is not None and "state" in item:
                resource.state = item["state"]
                try:
                    loop = self._loop
                    if loop is None or loop.is_closed():
                        _LOGGER.debug(
                            "Event loop closed; skipping update for resource %s",
                            item.get("id"),
                        )
                    else:
                        resource.publish_update(loop)
                except Exception as e:
                    _LOGGER.exception(
                        "Failed to schedule update for %s: %s",
                        item.get("id"),
                        e,
                    )

    # ---------------- Weather handling ----------------

    def ensure_weather_resource(self) -> None:
        """Utwórz obiekt NexoWeather, jeśli go jeszcze nie ma."""
        if not self._weather:
            self._weather.append(NexoWeather())

    def get_weather_resources(self) -> List[NexoWeather]:
        self.ensure_weather_resource()
        return list(self._weather)

    def register_weather_listener(self, callback: Callable[[], None]) -> None:
        if callback not in self._weather_listeners:
            self._weather_listeners.append(callback)

    def unregister_weather_listener(self, callback: Callable[[], None]) -> None:
        try:
            self._weather_listeners.remove(callback)
        except ValueError:
            pass

    def on_message_set_weather(self, json_message: dict) -> None:
        """Obsługa op=set_weather – aktualizacja jedynego obiektu pogody i powiadomienie encji."""
        data = json_message.get("data") or {}
        self.ensure_weather_resource()
        wx = self._weather[0]
        wx.update_from_bridge(data)

        for cb in list(self._weather_listeners):
            try:
                self._loop.call_soon_threadsafe(cb)
            except Exception:
                _LOGGER.exception("Weather listener callback failed")

    # ---------------- Helpers ----------------

    def get_resource_by_id(self, resource_id) -> Optional[NexoResource]:
        try:
            rid = int(resource_id)
        except Exception:
            return None
        return self.resources.get(rid)

    def get_resources_by_type(self, resource_type):
        return list(
            filter(lambda x: isinstance(x, resource_type), list(self.resources.values()))
        )

    def on_error(self, web_socket, error) -> None:
        _LOGGER.error("WebSocket error: %s", error)

    def on_close(self, web_socket, close_status_code, close_msg) -> None:
        _LOGGER.error("Connection closed: %s %s", close_status_code, close_msg)

    # ---------------- Resource factory ----------------

    def add_resource(self, nexo_resource: dict) -> Optional[NexoResource]:
        nexo_resource_type = nexo_resource.get("type")
        _LOGGER.debug(
            "Adding resource type=%s id=%s",
            nexo_resource_type,
            nexo_resource.get("id"),
        )

        match nexo_resource_type:
            case "light":
                obj = NexoLight(self.ws, **nexo_resource)
            case "dimmer":
                obj = NexoDimmer(self.ws, **nexo_resource)
                _LOGGER.warning("NexoBridge: dodano DIMMER %s", obj.id)
            case "led":
                obj = NexoLed(self.ws, **nexo_resource)
                _LOGGER.warning("NexoBridge: dodano LED %s", obj.id)
            case "group_led":
                obj = NexoGroupLed(self.ws, **nexo_resource)
                _LOGGER.warning("NexoBridge: dodano GROUP_LED %s", obj.id)
            case "group_output":
                obj = NexoGroupOutput(self.ws, **nexo_resource)
                _LOGGER.warning("NexoBridge: dodano GROUP_OUTPUT %s", obj.id)
            case "sensor":
                if "state" not in nexo_resource:
                    return None
                obj = NexoBinarySensor(self.ws, **nexo_resource)
            case "analogsensor":
                obj = NexoAnalogSensor(self.ws, **nexo_resource)
            case "output":
                obj = NexoOutput(self.ws, **nexo_resource)
            case "temperature":
                mode = nexo_resource.get("mode")
                if mode == 1:
                    obj = NexoTemperature(self.ws, **nexo_resource)
                elif mode == 2:
                    obj = NexoThermostat(self.ws, **nexo_resource)
                else:
                    return None
            case "blind":
                obj = NexoBlind(self.ws, **nexo_resource)
            case "group_blind":
                obj = NexoBlindGroup(self.ws, **nexo_resource)
            case "group_dimmer":
                obj = NexoGroupDimmer(self.ws, **nexo_resource)
            case "gate":
                obj = NexoGate(self.ws, **nexo_resource)
            case "partition":
                obj = NexoPartition(self.ws, **nexo_resource)
            case _:
                _LOGGER.warning("NexoBridge: unsupported resource type %s", nexo_resource_type)
                return None

        self.resources[obj.id] = obj
        return obj

    # ---------------- ext_command support ----------------

    def get_ext_commands(self) -> list[str]:
        """Return discovered ext_command names."""
        try:
            return sorted(self._ext_commands)
        except AttributeError:
            # fallback w razie braku inicjalizacji
            self._ext_commands = set()
            return []

    def on_message_modifications(self, json_message: dict) -> None:
        """Capture available ext_commands from 'modifications' op."""
        try:
            mods = json_message.get("modifications") or {}
            exts = mods.get("ext_commands") or {}
            for scope_key in ("to_system", "to_user"):
                scope = exts.get(scope_key) or {}
                for cmd_name in scope.keys():
                    self._ext_commands.add(str(cmd_name))
            _LOGGER.debug("ext_commands discovered: %s", sorted(self._ext_commands))
        except Exception as e:
            _LOGGER.debug("Failed to parse ext_commands: %s", e)
