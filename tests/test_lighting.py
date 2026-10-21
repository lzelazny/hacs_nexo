"""Resource command and entity discovery checks without a Home Assistant install."""

from enum import StrEnum
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


def _load_modules():
    """Load the real integration modules with only HA's entity shell replaced."""
    package_name = "_nexo_lighting_tests"
    package = ModuleType(package_name)
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "nexo")]
    sys.modules[package_name] = package

    class ColorMode(StrEnum):
        ONOFF = "onoff"
        BRIGHTNESS = "brightness"

    class Entity:
        def async_write_ha_state(self):
            pass

    stubs = {}
    for name in (
        "homeassistant", "homeassistant.components", "homeassistant.components.light",
        "homeassistant.components.switch", "homeassistant.config_entries",
        "homeassistant.core", "homeassistant.helpers", "homeassistant.helpers.entity_platform",
        "websocket",
    ):
        stubs[name] = ModuleType(name)
    stubs["homeassistant.components.light"].ATTR_BRIGHTNESS = "brightness"
    stubs["homeassistant.components.light"].ColorMode = ColorMode
    stubs["homeassistant.components.light"].LightEntity = Entity
    stubs["homeassistant.components.switch"].SwitchEntity = Entity
    stubs["homeassistant.config_entries"].ConfigEntry = SimpleNamespace
    stubs["homeassistant.core"].HomeAssistant = SimpleNamespace
    stubs["homeassistant.helpers.entity_platform"].AddEntitiesCallback = object
    stubs["websocket"].WebSocketException = type("WebSocketException", (Exception,), {})
    stubs["websocket"].WebSocketConnectionClosedException = type("WebSocketConnectionClosedException", (Exception,), {})
    bridge_stub = ModuleType(f"{package_name}.nexoBridge")
    bridge_stub.NexoBridge = object
    stubs[bridge_stub.__name__] = bridge_stub
    with patch.dict(sys.modules, stubs):
        modules = {
            name: importlib.import_module(f"{package_name}.{name}")
            for name in (
                "nexo_light", "nexo_light_dimmable", "nexo_dimmer",
                "nexo_group_dimmer", "nexo_group_led", "nexo_output", "nexo_group_output",
                "light", "switch",
            )
        }
    return modules


MODULES = _load_modules()


class Socket:
    def __init__(self):
        self.commands = []

    def send(self, message):
        self.commands.append(json.loads(message))


def resource(module_name, class_name, rid=10, **extra):
    socket = Socket()
    cls = getattr(MODULES[module_name], class_name)
    obj = cls(socket, id=rid, name=f"Resource {rid}", state={"is_on": 1, "brightness": 64}, **extra)
    return obj, socket


class LightingTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_dimmer_and_group_commands(self):
        for module_name, class_name in (
            ("nexo_dimmer", "NexoDimmer"),
            ("nexo_group_dimmer", "NexoGroupDimmer"),
            ("nexo_group_led", "NexoGroupLed"),
        ):
            with self.subTest(resource=class_name):
                obj, socket = resource(module_name, class_name, ios=[1, 2])
                entity = MODULES["light"].HANexoDimmableLight(obj)
                await entity.async_turn_on()
                await entity.async_turn_on(brightness=123)
                await entity.async_turn_on(brightness=0)
                await entity.async_turn_off()
                self.assertEqual(
                    [cmd["cmd"] for cmd in socket.commands],
                    [{"operation": 4}, {"operation": 1, "brightness": 123}, {"operation": 0}, {"operation": 0}],
                )
                self.assertTrue(all(cmd["id"] == 10 and cmd["type"] == "resource" for cmd in socket.commands))
                # The controller remains the source of truth until it sends a state update.
                self.assertEqual(entity.brightness, 64)
                obj.state = {"is_on": 0, "brightness": 0}
                self.assertFalse(entity.is_on)
                self.assertEqual(entity.brightness, 0)

    async def test_existing_dimmable_light_protocol_and_id_are_preserved(self):
        obj, socket = resource("nexo_light_dimmable", "NexoDimmableLight", rid=7)
        entity = MODULES["light"].HANexoDimmableLight(obj)
        await entity.async_turn_on()
        await entity.async_turn_on(brightness=180)
        self.assertEqual([cmd["cmd"] for cmd in socket.commands], [{"operation": 1}, {"operation": 1, "brightness": 180}])
        self.assertEqual(entity.unique_id, "7")

    async def test_lights_are_discovered_once_with_existing_ids(self):
        specs = (
            ("nexo_light", "NexoLight"),
            ("nexo_light_dimmable", "NexoDimmableLight"),
            ("nexo_dimmer", "NexoDimmer"),
            ("nexo_group_dimmer", "NexoGroupDimmer"),
            ("nexo_group_led", "NexoGroupLed"),
        )
        resources = [resource(module, name, rid=i)[0] for i, (module, name) in enumerate(specs, 1)]
        bridge = SimpleNamespace(get_resources_by_type=lambda cls: [obj for obj in resources if type(obj) is cls])
        hass = SimpleNamespace(data={"nexo": {"entry": bridge}})
        entities = []
        await MODULES["light"].async_setup_entry(hass, SimpleNamespace(entry_id="entry"), lambda batch: entities.extend(batch))
        self.assertEqual(len(entities), len(resources))
        self.assertEqual({entity.unique_id for entity in entities}, {str(i) for i in range(1, len(specs) + 1)})

    async def test_group_output_sends_switch_commands_and_keeps_ids(self):
        obj, socket = resource("nexo_group_output", "NexoGroupOutput", rid=14, ios=[1, 2])
        entity = MODULES["switch"].HANexoSwitch(obj)
        await entity.async_turn_on()
        await entity.async_turn_off()
        self.assertEqual([cmd["cmd"] for cmd in socket.commands], [{"operation": 1}, {"operation": 0}])
        self.assertEqual(entity.unique_id, "14")

    async def test_switch_discovery_includes_group_once(self):
        output = resource("nexo_output", "NexoOutput", rid=1)[0]
        group = resource("nexo_group_output", "NexoGroupOutput", rid=2)[0]
        bridge = SimpleNamespace(get_resources_by_type=lambda cls: [obj for obj in (output, group) if type(obj) is cls])
        entities = []
        await MODULES["switch"].async_setup_entry(SimpleNamespace(data={"nexo": {"entry": bridge}}), SimpleNamespace(entry_id="entry"), lambda batch: entities.extend(batch))
        self.assertEqual([entity.unique_id for entity in entities], ["1", "2"])


if __name__ == "__main__":
    unittest.main()
