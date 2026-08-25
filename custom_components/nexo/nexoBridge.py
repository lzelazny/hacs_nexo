import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import threading
import time
from typing import Final

import websocket

from .nexo_analog_sensor import NexoAnalogSensor
from .nexo_binary_sensor import NexoBinarySensor
from .nexo_blind import NexoBlind
from .nexo_blind_group import NexoBlindGroup
from .nexo_gate import NexoGate
from .nexo_group_dimmer import NexoGroupDimmer
from .nexo_light import NexoLight
from .nexo_light_dimmable import NexoDimmableLight
from .nexo_output import NexoOutput
from .nexo_partition import NexoPartition
from .nexo_resource import NexoResource
from .nexo_temperature import NexoTemperature
from .nexo_thermostat import NexoThermostat


NEXO_RESOURCE_TYPE_TEMPERATURE = "temperature"
NEXO_RESOURCE_TYPE_OUTPUT = "output"
NEXO_RESOURCE_TYPE_SENSOR = "sensor"
NEXO_RESOURCE_TYPE_ANALOG_SENSOR = "analogsensor"
NEXO_RESOURCE_TYPE_LIGHT = "light"
NEXO_INIT_TIMEOUT = 10
NEXO_RECONNECT_TIMEOUT = 5
NEXO_PING_INTERVAL = 30

_LOGGER: Final = logging.getLogger(__name__)


class NexoBridge:
    def __init__(self, local_ip) -> None:
        self.ws = None
        self.resources = {}
        self.local_ip = local_ip
        self.raw_data_model = {}
        self.initialized = False

        self._loop = asyncio.get_running_loop()
        self._executor = ThreadPoolExecutor(max_workers=1)

        self._keep_running = False
        self._ws_thread = None
        self._watchdog_task = None

    def _run_websocket(self) -> None:
        """Pętla reconnect w osobnym wątku (bez rel)."""
        while self._keep_running:
            try:
                _LOGGER.info("Connecting to Nexo... %s:8766", self.local_ip)

                self.ws = websocket.WebSocketApp(
                    f"ws://{self.local_ip}:8766/",
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                )
                # Bez ping_* – watchdog wysyła JSON ping (text frame)
                self.ws.run_forever()

            except Exception as e:
                _LOGGER.error("WebSocket runtime error: %s", e)

            if self._keep_running:
                _LOGGER.warning(
                    "Nexo WS disconnected. Reconnecting in %s s...",
                    NEXO_RECONNECT_TIMEOUT,
                )
                time.sleep(NEXO_RECONNECT_TIMEOUT)

    async def _stop_ws_thread(self) -> None:
        """Zatrzymuje wątek WS bez blokowania Event Loop HA."""
        self._keep_running = False

        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass

        if self._ws_thread is not None and self._ws_thread.is_alive():
            # join w executorze – nie blokuje pętli asynchronicznej
            await self._loop.run_in_executor(
                self._executor,
                lambda: self._ws_thread.join(timeout=5),
            )

    async def connect(self) -> None:
        _LOGGER.info("Initializing Nexo connection...")

        # Zatrzymaj poprzedni wątek jeśli istnieje
        await self._stop_ws_thread()

        # Zatrzymaj poprzedni watchdog
        if self._watchdog_task is not None and not self._watchdog_task.done():
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass

        # Uruchom nowy wątek WS
        self._keep_running = True
        self._ws_thread = threading.Thread(
            target=self._run_websocket,
            daemon=True,
        )
        self._ws_thread.start()

        await self.wait_for_initial_resources_load(NEXO_INIT_TIMEOUT)

        # Uruchom watchdog
        self._watchdog_task = self._loop.create_task(self.async_watchdog())

    async def async_watchdog(self) -> None:
        """
        Wysyła JSON ping co NEXO_PING_INTERVAL sekund.
        Jeśli send() rzuci wyjątek — zamyka socket, a _run_websocket zrobi reconnect.
        """
        while self._keep_running:
            await asyncio.sleep(NEXO_PING_INTERVAL)

            if self.ws is None:
                continue

            try:
                self.ws.send('{"type":"ping"}')
                _LOGGER.debug("Nexo WS: ping sent")
            except Exception as e:
                _LOGGER.warning(
                    "Nexo WS: ping failed (%s) — forcing reconnect",
                    e,
                )
                try:
                    self.ws.close()
                except Exception:
                    pass
                await asyncio.sleep(NEXO_RECONNECT_TIMEOUT + 1)

    def on_open(self, web_socket) -> None:
        _LOGGER.info("Nexo integration started / reconnected")
        if self.initialized:
            self.refresh_resources()

    async def wait_for_initial_resources_load(self, timeout: int) -> None:
        t = timeout
        while not self.initialized and t > 0:
            await asyncio.sleep(1)
            t -= 1

    def on_message(self, web_socket, message: str) -> None:
        _LOGGER.debug("Message: %s", message)
        json_message = json.loads(message)

        if json_message.get("op") == "initial_data":
            self.on_message_initial_data(json_message)

        if json_message.get("op") == "data_update":
            self.on_message_data_update(json_message)

    def on_message_initial_data(self, json_message: dict) -> None:
        if not self.raw_data_model and json_message:
            self.raw_data_model = json_message
            self.update_resources()
        else:
            self.refresh_resources()

    def update_resources(self) -> None:
        self.initialized = False
        self.resources.clear()

        for resource_id in dict(self.raw_data_model["resources"]):
            self.add_resource(self.raw_data_model["resources"][resource_id])

        self.initialized = True

    def add_weather_station(self, weather_station: dict) -> None:
        if weather_station and len(weather_station.keys()) > 0:
            for resource_id in dict(weather_station):
                self.add_resource(weather_station[resource_id])

    def refresh_resources(self) -> None:
        for resource in self.resources.values():
            resource.web_socket = self.ws

    def on_message_data_update(self, json_message: dict) -> None:
        if "resources" in json_message:
            for res in json_message["resources"]:
                res_obj = json_message["resources"][res]
                resource = self.get_resource_by_id(res_obj["id"])
                if resource is not None and "state" in res_obj:
                    resource.state = res_obj["state"]
                    resource.publish_update(self._loop)

    def get_resource_by_id(self, resource_id) -> NexoResource | None:
        if int(resource_id) in self.resources:
            return self.resources[int(resource_id)]
        return None

    def get_resources_by_type(self, resource_type):
        return list(
            filter(
                lambda x: type(x) is resource_type,
                list(self.resources.values()),
            )
        )

    def on_error(self, web_socket, error) -> None:
        _LOGGER.error("Nexo WS Error: %s", error)

    def on_close(self, web_socket, close_status_code, close_msg) -> None:
        _LOGGER.warning("Nexo WebSocket closed: %s", close_msg)

    def add_resource(self, nexo_resource: dict) -> None:
        nexo_resource_type = nexo_resource["type"]

        match nexo_resource_type:
            case "light":
                if "state" in nexo_resource and "brightness" in nexo_resource["state"]:
                    obj = NexoDimmableLight(self.ws, **nexo_resource)
                else:
                    obj = NexoLight(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case "led":
                if "state" in nexo_resource and "brightness" in nexo_resource["state"]:
                    obj = NexoDimmableLight(self.ws, **nexo_resource)
                else:
                    obj = NexoLight(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case "sensor":
                if "state" not in nexo_resource:
                    return
                obj = NexoBinarySensor(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case "analogsensor":
                obj = NexoAnalogSensor(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case "output":
                obj = NexoOutput(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case "temperature":
                match nexo_resource["mode"]:
                    case 1:
                        obj = NexoTemperature(self.ws, **nexo_resource)
                    case 2:
                        obj = NexoThermostat(self.ws, **nexo_resource)
                    case _:
                        return
                self.resources[obj.id] = obj

            case "blind":
                obj = NexoBlind(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case "group_blind":
                obj = NexoBlindGroup(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case "group_dimmer":
                obj = NexoGroupDimmer(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case "gate":
                obj = NexoGate(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case "partition":
                obj = NexoPartition(self.ws, **nexo_resource)
                self.resources[obj.id] = obj

            case _:
                _LOGGER.warning(
                    "Unsupported resource type %s, id %s",
                    nexo_resource_type,
                    nexo_resource["id"],
                )
