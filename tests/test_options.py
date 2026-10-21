"""Check options flow discovery and command parsing without a HA installation."""

import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


def _load_flow():
    package = ModuleType("_nexo_options_tests")
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "nexo")]
    stubs = {package.__name__: package}
    for name in ("homeassistant", "homeassistant.config_entries", "homeassistant.core",
                 "homeassistant.data_entry_flow", "homeassistant.exceptions", "voluptuous"):
        stubs[name] = ModuleType(name)

    class Flow:
        def __init_subclass__(cls, **kwargs):
            pass
        def async_create_entry(self, **kwargs):
            return {"type": "create_entry", **kwargs}
        def async_show_menu(self, **kwargs):
            return {"type": "menu", **kwargs}
        def async_show_form(self, **kwargs):
            return {"type": "form", **kwargs}

    stubs["homeassistant.config_entries"].ConfigFlow = Flow
    stubs["homeassistant.config_entries"].OptionsFlow = Flow
    stubs["homeassistant.config_entries"].ConfigEntry = SimpleNamespace
    stubs["homeassistant.core"].HomeAssistant = SimpleNamespace
    stubs["homeassistant.core"].callback = lambda callback: callback
    stubs["homeassistant.data_entry_flow"].FlowResult = dict
    stubs["homeassistant.exceptions"].HomeAssistantError = Exception
    stubs["voluptuous"].Schema = lambda data: data
    stubs["voluptuous"].Required = lambda key, **kwargs: key
    stubs["voluptuous"].Optional = lambda key, **kwargs: key
    stubs["voluptuous"].All = lambda *args: args
    stubs["voluptuous"].Coerce = lambda value: value
    stubs["voluptuous"].Range = lambda **kwargs: kwargs
    with patch.dict(sys.modules, stubs):
        return importlib.import_module(f"{package.__name__}.config_flow")


FLOW = _load_flow()


class OptionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_config_flow_exposes_options_and_preserves_other_options(self):
        entry = SimpleNamespace(options={"other": True, "ext_commands": ["old"]})
        flow = FLOW.ConfigFlow.async_get_options_flow(entry)
        result = await flow.async_step_commands({"ext_commands": " open,close, ,open "})
        self.assertEqual(result["data"], {"other": True, "ext_commands": ["close", "open"]})

    async def test_empty_commands_remove_manual_buttons(self):
        flow = FLOW.ConfigFlow.async_get_options_flow(SimpleNamespace(options={"ext_commands": ["old"]}))
        result = await flow.async_step_commands({"ext_commands": " , "})
        self.assertEqual(result["data"], {"ext_commands": []})

    async def test_options_form_can_be_opened(self):
        flow = FLOW.ConfigFlow.async_get_options_flow(SimpleNamespace(options={}))
        menu = await flow.async_step_init()
        self.assertEqual(menu["type"], "menu")
        self.assertEqual(menu["menu_options"], ["commands", "inspect_json"])
        result = await flow.async_step_commands()
        self.assertEqual(result["step_id"], "commands")
        self.assertIn("ext_commands", result["data_schema"])

    async def test_reconfigure_prefills_legacy_connection(self):
        flow = FLOW.ConfigFlow()
        flow._get_reconfigure_entry = lambda: SimpleNamespace(data={"host": "192.0.2.1"})
        result = await flow.async_step_reconfigure()
        self.assertEqual(result["step_id"], "reconfigure")
        self.assertEqual(set(result["data_schema"]), {"host", "port"})

    async def test_reconfigure_updates_existing_entry_preserving_data(self):
        from unittest.mock import Mock
        entry = SimpleNamespace(entry_id="test", data={"host": "192.0.2.1", "other": True}, options={"ext_commands": ["open"]})
        flow = FLOW.ConfigFlow()
        flow._get_reconfigure_entry = lambda: entry
        flow.hass = SimpleNamespace(data={"nexo": {"test": object()}}, config_entries=SimpleNamespace(async_update_entry=Mock(return_value=True)))
        flow.async_abort = lambda **kwargs: kwargs
        result = await flow.async_step_reconfigure({"host": "192.0.2.2", "port": 9000})
        flow.hass.config_entries.async_update_entry.assert_called_once_with(
            entry, data={"host": "192.0.2.2", "port": 9000, "other": True}
        )
        self.assertEqual(result["reason"], "reconfigure_successful")
        self.assertEqual(entry.options, {"ext_commands": ["open"]})

    async def test_reconfigure_retries_entry_after_failed_setup(self):
        from unittest.mock import AsyncMock, Mock
        entry = SimpleNamespace(entry_id="test", data={"host": "192.0.2.1"})
        flow = FLOW.ConfigFlow()
        flow._get_reconfigure_entry = lambda: entry
        reload_entry = AsyncMock()
        flow.hass = SimpleNamespace(data={}, config_entries=SimpleNamespace(
            async_update_entry=Mock(return_value=True), async_reload=reload_entry))
        flow.async_abort = lambda **kwargs: kwargs
        await flow.async_step_reconfigure({"host": "192.0.2.2", "port": 9000})
        reload_entry.assert_awaited_once_with("test")

    async def test_json_menu_links_to_selected_entry_without_saving(self):
        flow = FLOW.ConfigFlow.async_get_options_flow(
            SimpleNamespace(entry_id="bridge-two", options={"ext_commands": ["open"]})
        )
        result = await flow.async_step_inspect_json()
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["description_placeholders"]["inspector_url"],
                         "/nexo-inspector?config_entry=bridge-two")
        self.assertEqual(flow._entry.options, {"ext_commands": ["open"]})
