"""Verify init snapshots independently of resource and socket lifecycles."""

import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from test_bridge import BRIDGE


class SnapshotTests(unittest.TestCase):
    def test_latest_init_replaces_snapshot_without_changing_first_resource_model(self):
        bridge = object.__new__(BRIDGE.NexoBridge)
        bridge.raw_data_model = {}
        bridge.update_resources = Mock()
        bridge.refresh_resources = Mock()
        first = {"op": "initial_data", "resources": {"1": {"name": "first"}}}
        second = {"op": "initial_data", "resources": {"1": {"name": "latest"}}}
        bridge.on_message_initial_data(first)
        bridge.on_message_initial_data(second)
        received, snapshot = bridge.latest_initial_data
        self.assertTrue(received.endswith("+00:00"))
        self.assertEqual(snapshot, second)
        second["resources"]["1"]["name"] = "mutated"
        self.assertEqual(snapshot["resources"]["1"]["name"], "latest")
        self.assertIs(bridge.raw_data_model, first)
        bridge.update_resources.assert_called_once()
        bridge.refresh_resources.assert_called_once()

    def test_inspector_reports_loaded_and_unloaded_entries_and_requires_admin(self):
        from test_options import FLOW
        package = FLOW.__package__
        package_module = ModuleType(package)
        package_module.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "nexo")]
        modules = {package: package_module}
        for name in ("homeassistant", "homeassistant.components", "homeassistant.components.http", "homeassistant.core", "homeassistant.exceptions", "voluptuous"):
            modules[name] = ModuleType(name)
        admin = Mock(side_effect=lambda fn: fn)
        modules["homeassistant.components"].panel_custom = SimpleNamespace()
        modules["homeassistant.components"].websocket_api = SimpleNamespace(
            websocket_command=lambda schema: lambda fn: fn, require_admin=admin,
            async_response=lambda fn: fn)
        modules["homeassistant.components.http"].StaticPathConfig = Mock()
        modules["homeassistant.exceptions"].HomeAssistantError = RuntimeError
        modules["homeassistant.core"].callback = lambda fn: fn
        modules["voluptuous"].Required = lambda key: key
        with patch.dict(sys.modules, modules):
            inspector = importlib.import_module(f"{package}.inspector")
        entry = SimpleNamespace(entry_id="test", title="Bridge", data={"host": "192.0.2.1"}, options={})
        payload = {"op": "initial_data", "resources": {}}
        bridge = SimpleNamespace(latest_initial_data=("2026-10-22T12:00:00+00:00", payload), connected=False, get_ext_commands=lambda: ["open"])
        hass = SimpleNamespace(data={"nexo": {"test": bridge}})
        result = inspector.snapshot(hass, entry)
        self.assertIs(result["initial_data"], payload)
        self.assertEqual(result["port"], 8766)
        self.assertFalse(result["connected"])
        hass.data.clear()
        self.assertIsNone(inspector.snapshot(hass, entry)["initial_data"])
        self.assertEqual(admin.call_count, 3)
        self.assertEqual(result["commands"], ["open"])
        global INSPECTOR
        INSPECTOR = inspector


class CommandApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        from unittest.mock import AsyncMock
        if "INSPECTOR" not in globals():
            SnapshotTests("test_inspector_reports_loaded_and_unloaded_entries_and_requires_admin").test_inspector_reports_loaded_and_unloaded_entries_and_requires_admin()
        self.bridge = SimpleNamespace(connected=True, async_send_ext_command=AsyncMock())
        self.hass = SimpleNamespace(data={"nexo": {"one": self.bridge}})
        self.connection = SimpleNamespace(send_result=Mock(), send_error=Mock())

    async def test_send_routes_to_selected_bridge_and_trims_command(self):
        from unittest.mock import AsyncMock
        other = SimpleNamespace(connected=True, async_send_ext_command=AsyncMock())
        self.hass.data["nexo"]["two"] = other
        await INSPECTOR.websocket_send_command(self.hass, self.connection,
            {"id": 1, "entry_id": "one", "command": " open gate "})
        self.bridge.async_send_ext_command.assert_awaited_once_with("open gate")
        other.async_send_ext_command.assert_not_awaited()
        self.connection.send_result.assert_called_once()

    async def test_disconnected_bridge_cannot_send(self):
        self.bridge.connected = False
        await INSPECTOR.websocket_send_command(self.hass, self.connection,
            {"id": 1, "entry_id": "one", "command": "open"})
        self.bridge.async_send_ext_command.assert_not_awaited()
        self.assertEqual(self.connection.send_error.call_args.args[1], "not_connected")

    async def test_send_failure_reaches_ui(self):
        self.bridge.async_send_ext_command.side_effect = RuntimeError("Connection lost")
        await INSPECTOR.websocket_send_command(self.hass, self.connection,
            {"id": 1, "entry_id": "one", "command": "open"})
        self.assertEqual(self.connection.send_error.call_args.args[1], "send_failed")
        self.connection.send_result.assert_not_called()

    async def test_save_preserves_other_options_and_parses_names(self):
        entry = SimpleNamespace(domain="nexo", options={"other": True})
        update = Mock()
        self.hass.config_entries = SimpleNamespace(async_get_entry=lambda key: entry,
                                                  async_update_entry=update)
        INSPECTOR.websocket_save_commands(self.hass, self.connection,
            {"id": 1, "entry_id": "one", "commands": " open, close,open, "})
        update.assert_called_once_with(entry, options={"other": True, "ext_commands": ["close", "open"]})

    async def test_save_rejects_another_integration(self):
        update = Mock()
        self.hass.config_entries = SimpleNamespace(
            async_get_entry=lambda key: SimpleNamespace(domain="other"), async_update_entry=update)
        INSPECTOR.websocket_save_commands(self.hass, self.connection,
            {"id": 1, "entry_id": "one", "commands": "open"})
        update.assert_not_called()
        self.assertEqual(self.connection.send_error.call_args.args[1], "not_found")
