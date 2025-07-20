"""Module for managing the NexoBridge WebSocket connection and resource handling."""

import asyncio
import json
import logging
from typing import Final

import websockets

from homeassistant.core import HomeAssistant

from .nexo_analog_sensor import NexoAnalogSensor
from .nexo_binary_sensor import NexoBinarySensor
from .nexo_blind import NexoBlind
from .nexo_blind_group import NexoBlindGroup
from .nexo_gate import NexoGate
from .nexo_group_dimmer import NexoGroupDimmer
from .nexo_light import NexoLight
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
    """Class for managing the NexoBridge WebSocket connection and resources."""

    def __init__(self, hass: HomeAssistant, ip) -> None:
        """Initialize the NexoBridge instance."""
        self._hass = hass
        self.ip = ip
        self._ws = None
        self._resources = {}
        self._raw_data_model = {}
        self._initialized = False
        self._task = None
        self._stop_event = asyncio.Event()

    async def async_wait_for_initial_resources_load(self, timeout):
        """Wait asynchronously for the initial resources to load or until the timeout expires."""
        t = timeout
        while self._initialized is False and t > 0:
            await asyncio.sleep(1)
            t = t - 1

    async def connect(self):
        """Establish and maintain the WebSocket connection."""
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(f"ws://{self.ip}:8766/") as websocket:
                    _LOGGER.info("Connected to WebSocket: %s", self.ip)
                    self._ws = websocket
                    await self.listen()
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning(
                    "WebSocket error: %s. Attempting to reconnect in %s seconds",
                    err,
                    NEXO_RECONNECT_TIMEOUT,
                )
                await asyncio.sleep(NEXO_RECONNECT_TIMEOUT)

    async def listen(self):
        """Handle incoming messages from the WebSocket."""
        async for message in self._ws:
            _LOGGER.debug("Received message: %s", message)
            json_message = json.loads(message)
            if json_message["op"] == "initial_data":
                self.on_message_initial_data(json_message)
            if json_message["op"] == "data_update":
                self.on_message_data_update(json_message)

    async def start(self):
        """Start the WebSocket client in the background."""
        self._initialized = False
        self._stop_event.clear()
        self._task = asyncio.create_task(self.connect())

    async def stop(self):
        """Stop the client and close the connection."""
        self._stop_event.set()
        if self._ws:
            await self._ws.close()
        if self._task:
            await self._task

    def on_message_initial_data(self, json_message):
        """Handle the initial data message from the WebSocket."""
        _LOGGER.debug(json_message)
        if len(self._raw_data_model.keys()) == 0 and len(json_message.keys()) > 0:
            self._raw_data_model = json_message
            self.update_resources()
        else:
            self.refresh_resources()

    def update_resources(self):
        """Update resources based on the initial data model."""
        _LOGGER.debug("INIT START")
        self._resources.clear()
        for resource_id in dict(self._raw_data_model["resources"]):
            self.add_resource(self._raw_data_model["resources"][resource_id])
        self._initialized = True
        _LOGGER.debug("INIT END")
        _LOGGER.debug("Resources: %s", self._resources)

    def refresh_resources(self):
        """Refresh resources with the current WebSocket connection."""
        for resource in self._resources.values():
            resource.web_socket = self._ws

    def on_message_data_update(self, json_message):
        """Handle data update messages from the WebSocket."""
        if "resources" in json_message:
            for res in json_message["resources"]:
                resource = self.get_resource_by_id(json_message["resources"][res]["id"])
                if resource is not None and "state" in json_message["resources"][res]:
                    resource.state = json_message["resources"][res]["state"]
                    resource.publish_update(self._hass.loop)

    def get_resource_by_id(self, resource_id) -> NexoResource | None:
        """Get a resource by its ID."""
        if int(resource_id) in self._resources:
            return self._resources[int(resource_id)]
        return None

    def get_resources_by_type(self, resource_type):
        """Get resources filtered by type."""
        return list(
            filter(lambda x: type(x) is resource_type, list(self._resources.values()))
        )

    def add_resource(self, nexo_resource):
        """Add a resource based on its type."""
        nexo_resource_type = nexo_resource["type"]
        match nexo_resource_type:
            case "light":
                obj = NexoLight(self._ws, **nexo_resource)
                self._resources[obj.id] = obj
                return obj

            case "sensor":
                if "state" not in nexo_resource:
                    return None
                obj = NexoBinarySensor(self._ws, **nexo_resource)
                self._resources[obj.id] = obj
                return obj

            case "analogsensor":
                obj = NexoAnalogSensor(self._ws, **nexo_resource)
                self._resources[obj.id] = obj
                return obj

            case "output":
                obj = NexoOutput(self._ws, **nexo_resource)
                self._resources[obj.id] = obj
                return obj

            case "temperature":
                match nexo_resource["mode"]:
                    case 1:
                        obj = NexoTemperature(self._ws, **nexo_resource)
                    case 2:
                        obj = NexoThermostat(self._ws, **nexo_resource)
                    case _:
                        return None
                self._resources[obj.id] = obj
                return obj

            case "blind":
                obj = NexoBlind(self._ws, **nexo_resource)
                self._resources[obj.id] = obj
                return obj

            case "group_blind":
                obj = NexoBlindGroup(self._ws, **nexo_resource)
                self._resources[obj.id] = obj
                return obj

            case "group_dimmer":
                obj = NexoGroupDimmer(self._ws, **nexo_resource)
                self._resources[obj.id] = obj
                return obj

            case "gate":
                obj = NexoGate(self._ws, **nexo_resource)
                self._resources[obj.id] = obj
                return obj

            case "partition":
                obj = NexoPartition(self._ws, **nexo_resource)
                self._resources[obj.id] = obj
                return obj

            case _:
                print(f"not supported {type}")
