"""Exercise external-command button routing and discovery without a running HA."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


def _load_button_module():
    """Import the real button module with temporary, narrowly scoped HA stubs."""
    source_dir = Path(__file__).resolve().parents[1] / "custom_components" / "nexo"
    package_name = "_nexo_commands_test"
    package = ModuleType(package_name)
    package.__path__ = [str(source_dir)]

    class ButtonEntity:
        @property
        def unique_id(self):
            return self._attr_unique_id

        @property
        def name(self):
            return self._attr_name

        @property
        def should_poll(self):
            return self._attr_should_poll

    modules = {package_name: package}
    for name in (
        "homeassistant",
        "homeassistant.components",
        "homeassistant.components.button",
        "homeassistant.config_entries",
        "homeassistant.core",
        "homeassistant.helpers",
        "homeassistant.helpers.entity_platform",
        f"{package_name}.nexoBridge",
    ):
        modules[name] = ModuleType(name)
    modules["homeassistant.components.button"].ButtonEntity = ButtonEntity
    modules["homeassistant.config_entries"].ConfigEntry = object
    modules["homeassistant.core"].HomeAssistant = object
    modules["homeassistant.helpers.entity_platform"].AddEntitiesCallback = object
    modules[f"{package_name}.nexoBridge"].NexoBridge = object

    with patch.dict(sys.modules, modules):
        for filename in ("const", "button"):
            qualified_name = f"{package_name}.{filename}"
            spec = importlib.util.spec_from_file_location(
                qualified_name, source_dir / f"{filename}.py"
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[qualified_name] = module
            spec.loader.exec_module(module)
        return module


button = _load_button_module()


class FakeBridge:
    """Model connection replacement and bridge command notifications."""

    def __init__(self, commands=()):
        self.commands = set(commands)
        self.listeners = set()
        self.ws = []

    def get_ext_commands(self):
        return sorted(self.commands)

    def register_command_listener(self, callback):
        self.listeners.add(callback)

    def unregister_command_listener(self, callback):
        self.listeners.discard(callback)

    async def async_send_ext_command(self, command):
        self.ws.append(command)

    def announce(self, *commands):
        self.commands.update(commands)
        for callback in tuple(self.listeners):
            callback()


class FakeEntry:
    def __init__(self, entry_id="bridge_a", commands=()):
        self.entry_id = entry_id
        self.options = {"ext_commands": list(commands)}
        self.unload_callbacks = []

    def async_on_unload(self, callback):
        self.unload_callbacks.append(callback)

    def unload(self):
        for callback in self.unload_callbacks:
            callback()
        self.unload_callbacks.clear()


class CommandButtonTests(unittest.IsolatedAsyncioTestCase):
    async def test_press_uses_current_connection_after_reconnect(self):
        bridge = FakeBridge()
        entity = button.NexoButton(bridge, "bridge_a", "gate")
        first_connection = bridge.ws
        await entity.async_press()

        bridge.ws = []
        await entity.async_press()

        self.assertEqual(first_connection, ["gate"])
        self.assertEqual(bridge.ws, ["gate"])
        self.assertEqual(entity.name, "gate")
        self.assertFalse(entity.should_poll)

    async def test_same_command_has_separate_ids_and_routes_for_each_entry(self):
        first = FakeBridge()
        second = FakeBridge()
        first_entity = button.NexoButton(first, "bridge_a", "gate")
        second_entity = button.NexoButton(second, "bridge_b", "gate")

        self.assertEqual(first_entity.unique_id, "bridge_a_command_gate")
        self.assertEqual(second_entity.unique_id, "bridge_b_command_gate")
        self.assertNotEqual(first_entity.unique_id, second_entity.unique_id)
        await second_entity.async_press()
        self.assertEqual(first.ws, [])
        self.assertEqual(second.ws, ["gate"])

    async def test_setup_combines_configured_and_announced_commands_once(self):
        bridge = FakeBridge(["gate", "garden"])
        entry = FakeEntry(commands=["gate", "door", "door"])
        hass = SimpleNamespace(data={"nexo": {entry.entry_id: bridge}})
        batches = []

        await button.async_setup_entry(hass, entry, batches.append)

        self.assertEqual(len(batches), 1)
        self.assertEqual([entity.name for entity in batches[0]], ["door", "garden", "gate"])
        self.assertEqual(len(bridge.listeners), 1)
        self.assertEqual(len(entry.unload_callbacks), 1)

    async def test_late_discovery_adds_only_new_commands_and_unload_removes_listener(self):
        bridge = FakeBridge()
        entry = FakeEntry()
        hass = SimpleNamespace(data={"nexo": {entry.entry_id: bridge}})
        batches = []
        await button.async_setup_entry(hass, entry, batches.append)
        self.assertEqual(batches, [])

        bridge.announce("gate", "garden")
        bridge.announce("gate", "garden")
        bridge.announce("gate", "door")

        self.assertEqual(
            [[entity.name for entity in batch] for batch in batches],
            [["garden", "gate"], ["door"]],
        )
        entry.unload()
        self.assertEqual(bridge.listeners, set())
        bridge.announce("new_after_unload")
        self.assertEqual(len(batches), 2)

    async def test_press_propagates_bridge_failure(self):
        async def send_failure(command):
            raise ConnectionError("bridge disconnected")

        bridge = SimpleNamespace(async_send_ext_command=send_failure)
        entity = button.NexoButton(bridge, "bridge_a", "gate")
        with self.assertRaisesRegex(ConnectionError, "bridge disconnected"):
            await entity.async_press()


if __name__ == "__main__":
    unittest.main()
