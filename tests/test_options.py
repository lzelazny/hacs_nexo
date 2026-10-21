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
    stubs["voluptuous"].Required = lambda key: key
    stubs["voluptuous"].Optional = lambda key, **kwargs: key
    with patch.dict(sys.modules, stubs):
        return importlib.import_module(f"{package.__name__}.config_flow")


FLOW = _load_flow()


class OptionsTests(unittest.IsolatedAsyncioTestCase):
    async def test_config_flow_exposes_options_and_preserves_other_options(self):
        entry = SimpleNamespace(options={"other": True, "ext_commands": ["old"]})
        flow = FLOW.ConfigFlow.async_get_options_flow(entry)
        result = await flow.async_step_init({"ext_commands": " open,close, ,open "})
        self.assertEqual(result["data"], {"other": True, "ext_commands": ["close", "open"]})

    async def test_empty_commands_remove_manual_buttons(self):
        flow = FLOW.ConfigFlow.async_get_options_flow(SimpleNamespace(options={"ext_commands": ["old"]}))
        result = await flow.async_step_init({"ext_commands": " , "})
        self.assertEqual(result["data"], {"ext_commands": []})

    async def test_options_form_can_be_opened(self):
        flow = FLOW.ConfigFlow.async_get_options_flow(SimpleNamespace(options={}))
        result = await flow.async_step_init()
        self.assertEqual(result["step_id"], "init")
        self.assertIn("ext_commands", result["data_schema"])
