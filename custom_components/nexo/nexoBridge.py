from concurrent.futures import ThreadPoolExecutor
import threading
import asyncio
import websocket
import json
import time

NEXO_RESOURCE_TYPE_TEMPERATURE = "temperature"
NEXO_RESOURCE_TYPE_OUTPUT = "output"
NEXO_RESOURCE_TYPE_SENSOR = "sensor"
NEXO_RESOURCE_TYPE_ANALOG_SENSOR = "analogsensor"
NEXO_RESOURCE_TYPE_LIGHT = "light"

from .nexoEntities import (
    NexoAnalogSensor,
    NexoBlind,
    NexoBlindGroup,
    NexoGate,
    NexoGroupDimmer,
    NexoLight,
    NexoOutput,
    NexoPartition,
    NexoResource,
    NexoSensor,
    NexoTemperature,
)


class NexoBridge:
    def __init__(self, local_ip) -> None:
        self.ws = None
        self.resources = dict()
        self.local_ip = local_ip
        self.raw_data_model = dict()
        self.initialized = False
        self._loop = asyncio.get_running_loop()

    def on_open(self, ws):
        print("Opened connection")

    async def connect(self):
        # websocket.enableTrace(traceable=True)
        self.ws = websocket.WebSocketApp(
            f"ws://{self.local_ip}:8766/",
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )

        # wst = threading.Thread(target=self.ws.run_forever)
        # wst.daemon = True
        # wst.start()

        # asyncio.run(self.ws.run_forever(reconnect=10))

        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(self.ws.run_forever)
        timeout = 5

        while self.initialized is False and timeout > 0:
            await asyncio.sleep(1)
            timeout = timeout - 1

    def update_resources(self):
        self.initialized = False
        self.resources.clear()
        for resource_id in dict(self.raw_data_model["resources"]):
            self.add_resource(self.raw_data_model["resources"][resource_id])
        self.initialized = True

    def on_message(self, webSocet, message):
        json_message = json.loads(message)
        if json_message["op"] == "initial_data":
            self.on_message_initial_data(json_message)
        if json_message["op"] == "data_update":
            self.on_message_data_update(json_message)

    def on_message_initial_data(self, json_message):
        if len(self.raw_data_model.keys()) == 0:
            self.raw_data_model = json_message
            self.update_resources()

    def on_message_data_update(self, json_message):
        for res in json_message["resources"]:
            resource = self.get_resource_by_id(json_message["resources"][res]["id"])
            if resource is not None:
                resource.state = json_message["resources"][res]["state"]
                resource.timestamp = json_message["resources"][res]["timestamp"]
                resource.publish_update(self._loop)

    def get_resource_by_id(self, resource_id):
        if int(resource_id) in self.resources.keys():
            return self.resources[int(resource_id)]
        return None

    def get_resources_by_type(self, resource_type):
        return list(
            filter(
                lambda x: isinstance(x, resource_type), list(self.resources.values())
            )
        )

    def on_error(self, webSocet, error):
        print(error)

    def on_close(self, webSocet, close_status_code, close_msg):
        print("### closed ###")

    def add_resource(self, nexo_resource):
        type = nexo_resource["type"]
        match type:
            case "light":
                obj = NexoLight(self.ws, **nexo_resource)
                self.resources[obj.id] = obj
                return obj

            case "sensor":
                obj = NexoSensor(self.ws, **nexo_resource)
                self.resources[obj.id] = obj
                return obj

            case "output":
                obj = NexoOutput(self.ws, **nexo_resource)
                self.resources[obj.id] = obj
                return obj

            case "temperature":
                obj = NexoTemperature(self.ws, **nexo_resource)
                self.resources[obj.id] = obj
                return obj

            #   case "blind":
            #      obj = NexoBlind(self.ws, **nexo_resource)
            #     self.resources[obj.id] = obj
            #    return obj

            case "group_blind":
                obj = NexoBlindGroup(self.ws, **nexo_resource)
                self.resources[obj.id] = obj
                return obj

            case "group_dimmer":
                obj = NexoGroupDimmer(self.ws, **nexo_resource)
                self.resources[obj.id] = obj
                return obj

            case "analogsensor":
                obj = NexoAnalogSensor(self.ws, **nexo_resource)
                self.resources[obj.id] = obj
                return obj

            case "gate":
                obj = NexoGate(self.ws, **nexo_resource)
                self.resources[obj.id] = obj
                return obj

            case "partition":
                obj = NexoPartition(self.ws, **nexo_resource)
                self.resources[obj.id] = obj
                return obj

            case _:
                print(f"not supported {type}")
