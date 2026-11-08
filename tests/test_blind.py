"""Check blind position handling for modules that report no position."""

from enum import IntFlag
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


def _load_cover():
    package_name = "_nexo_blind_tests"
    package = ModuleType(package_name)
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "nexo")]

    # Upstream still imports the websocket-client package.
    stubs = {package_name: package, "websocket": ModuleType("websocket")}
    for name in (
        "homeassistant", "homeassistant.components", "homeassistant.components.cover",
        "homeassistant.config_entries", "homeassistant.core", "homeassistant.helpers",
        "homeassistant.helpers.entity_platform", "homeassistant.exceptions",
        "websockets", "websockets.exceptions",
    ):
        stubs[name] = ModuleType(name)
    cover = stubs["homeassistant.components.cover"]
    cover.CoverEntity = object
    cover.CoverDeviceClass = SimpleNamespace(BLIND="blind")
    cover.CoverEntityFeature = IntFlag(
        "CoverEntityFeature", {"OPEN": 1, "CLOSE": 2, "SET_POSITION": 4, "STOP": 8}
    )
    stubs["homeassistant.config_entries"].ConfigEntry = SimpleNamespace
    stubs["homeassistant.core"].HomeAssistant = SimpleNamespace
    stubs["homeassistant.helpers.entity_platform"].AddEntitiesCallback = object
    stubs["homeassistant.exceptions"].HomeAssistantError = Exception
    stubs["websockets.exceptions"].WebSocketException = Exception
    bridge_stub = ModuleType(f"{package_name}.nexoBridge")
    bridge_stub.NexoBridge = object
    stubs[bridge_stub.__name__] = bridge_stub
    with patch.dict(sys.modules, stubs):
        return (
            importlib.import_module(f"{package_name}.cover"),
            importlib.import_module(f"{package_name}.nexo_blind"),
        )


COVER, BLIND = _load_cover()


def _entity(**state):
    blind = BLIND.NexoBlind(None, id=1, name="Rol", state=state)
    return COVER.HANexoBlind(blind)


class BlindPositionTests(unittest.TestCase):
    def test_positioned_blind_reports_position(self):
        entity = _entity(blind_op=0, blind_level=75, blind_target=0, blind_slope=100)
        self.assertEqual(entity.current_cover_position, 25)
        self.assertFalse(entity.assumed_state)

    def test_blind_without_position_keeps_open_and_close_enabled(self):
        entity = _entity(blind_op=0, blind_level=0, blind_target=255, blind_slope=255)
        self.assertTrue(entity.assumed_state)
        self.assertEqual(entity.current_cover_position, 100)
        self.assertFalse(entity.is_closed)

    def test_set_position_is_offered_before_a_position_has_been_seen(self):
        entity = _entity(blind_op=0, blind_level=0, blind_target=255, blind_slope=255)
        for feature in ("OPEN", "CLOSE", "STOP", "SET_POSITION"):
            self.assertTrue(entity._attr_supported_features & COVER.CoverEntityFeature[feature])

    def test_idle_blind_never_reports_an_unknown_state(self):
        entity = _entity(blind_op=0, blind_level=100, blind_target=255, blind_slope=255)
        self.assertTrue(entity.is_closed)

    def test_position_support_is_latched_once_a_position_is_seen(self):
        entity = _entity(blind_op=0, blind_level=0, blind_target=255, blind_slope=255)
        self.assertTrue(entity.assumed_state)
        entity._nexo_blind.state = {
            "blind_op": 0, "blind_level": 40, "blind_target": 255, "blind_slope": 255,
        }
        self.assertFalse(entity.assumed_state)
        entity._nexo_blind.state = {
            "blind_op": 0, "blind_level": 0, "blind_target": 255, "blind_slope": 255,
        }
        self.assertFalse(entity.assumed_state)

    def test_position_support_follows_the_latest_state(self):
        entity = _entity(blind_op=0, blind_level=0, blind_target=255, blind_slope=255)
        entity._nexo_blind.state = {
            "blind_op": 0, "blind_level": 100, "blind_target": 100, "blind_slope": 100,
        }
        self.assertFalse(entity.assumed_state)
        self.assertTrue(entity.is_closed)


if __name__ == "__main__":
    unittest.main()
