import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import logging
from typing import Final

import rel
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

_LOGGER: Final = logging.getLogger(__name__)


class NexoBridge:
    def __init__(self, local_ip) -> None:
        self.__executor = ThreadPoolExecutor(max_workers=1)
        self.ws = None
        self.resources = {}
        self.local_ip = local_ip
        self.raw_data_model = {}
        self.initialized = False
        self._loop = asyncio.get_running_loop()

    async def async_watchdog(self):
        if self.ws.sock is None or self.ws.sock.getstatus() != 101:
            print("Connection reconect")
            await self.connect()
        else:
            asyncio.get_event_loop().call_later(
                NEXO_RECONNECT_TIMEOUT,
                lambda: asyncio.create_task(self.async_watchdog()),
            )

    def on_open(self, web_socket):
        _LOGGER.info("Nexo integration started")

    async def wait_for_initial_resources_load(self, timeout):
        t = timeout
        while self.initialized is False and t > 0:
            await asyncio.sleep(1)
            t = t - 1

    async def connect(self):
        _LOGGER.info("Connecting... %s:%s", self.local_ip, 8766)
        _LOGGER.info("Reconnect Timeout %s", NEXO_RECONNECT_TIMEOUT)
        _LOGGER.info("Init Timeout %s", NEXO_INIT_TIMEOUT)
        # websocket.enableTrace(traceable=True)
        if self.ws is not None:
            self.ws.close()

        self.ws = websocket.WebSocketApp(
            f"ws://{self.local_ip}:8766/",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
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

    def on_message(self, web_socket, message):
        _LOGGER.debug("Message: %s", message)
        json_message = json.loads(message)

        if json_message["op"] == "initial_data":
            self.on_message_initial_data(json_message)

        if json_message["op"] == "data_update":
            self.on_message_data_update(json_message)

    def on_message_initial_data(self, json_message):
        print(">>>>>>>>>>>>>Initial")
        print(json_message)
        if len(self.raw_data_model.keys()) == 0 and len(json_message.keys()) > 0:
            self.raw_data_model = json_message
            self.update_resources()
        else:
            self.refresh_resources()

    def update_resources(self):
        self.initialized = False
        self.resources.clear()
        for resource_id in dict(self.raw_data_model["resources"]):
            self.add_resource(self.raw_data_model["resources"][resource_id])

        # self.add_weather_station(self.raw_data_model["weather_station"])
        self.initialized = True
        print("AFTER INIT")
        print(self.resources)

    def add_weather_station(self, weather_station):
        if weather_station is not None and len(weather_station.keys()) > 0:
            for resource_id in dict(weather_station):
                self.add_resource(weather_station[resource_id])

    def refresh_resources(self):
        for resource in self.resources.values():
            resource.web_socket = self.ws

    def on_message_data_update(self, json_message):
        if "resources" in json_message:
            for res in json_message["resources"]:
                resource = self.get_resource_by_id(json_message["resources"][res]["id"])
                if resource is not None and "state" in json_message["resources"][res]:
                    resource.state = json_message["resources"][res]["state"]
                    resource.publish_update(self._loop)

    def get_resource_by_id(self, resource_id) -> NexoResource | None:
        if int(resource_id) in self.resources:
            return self.resources[int(resource_id)]
        return None

    def get_resources_by_type(self, resource_type):
        return list(
            filter(lambda x: type(x) is resource_type, list(self.resources.values()))
        )

    def on_error(self, web_socket, error):
        _LOGGER.error(error)

    def on_close(self, web_socket, close_status_code, close_msg):
        _LOGGER.error("Connection closed")

    def add_resource(self, nexo_resource):
        nexo_resource_type = nexo_resource["type"]
        match nexo_resource_type:
            case "light":
                if "state" in nexo_resource and "brightness" in nexo_resource["state"]:
                    # This is a dimmable light
                    obj = NexoDimmableLight(self.ws, **nexo_resource)
                    self.resources[obj.id] = obj
                else:
                    # This is a simple light
                    obj = NexoLight(self.ws, **nexo_resource)
                    self.resources[obj.id] = obj

            case "led":
                if "state" in nexo_resource and "brightness" in nexo_resource["state"]:
                    # This is a dimmable LED
                    obj = NexoDimmableLight(self.ws, **nexo_resource)
                    self.resources[obj.id] = obj
                else:
                    # This is a simple LLED
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
