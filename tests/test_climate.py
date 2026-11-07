"""Check thermostat entity limits and target temperature without Home Assistant."""

from enum import StrEnum
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


def _load_climate():
    package_name = "_nexo_climate_tests"
    package = ModuleType(package_name)
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "custom_components" / "nexo")]

    stubs = {package_name: package}
    for name in (
        "homeassistant", "homeassistant.components", "homeassistant.components.climate",
        "homeassistant.components.climate.const", "homeassistant.config_entries",
        "homeassistant.const", "homeassistant.core", "homeassistant.helpers",
        "homeassistant.helpers.entity_platform",
        "websocket",
    ):
        stubs[name] = ModuleType(name)
    stubs["homeassistant.components.climate"].ClimateEntity = object
    const = stubs["homeassistant.components.climate.const"]
    const.ClimateEntityFeature = StrEnum("ClimateEntityFeature", {"TARGET_TEMPERATURE": "target"})
    const.HVACAction = StrEnum("HVACAction", {"COOLING": "cooling", "HEATING": "heating", "OFF": "off"})
    const.HVACMode = StrEnum("HVACMode", {"OFF": "off", "HEAT_COOL": "heat_cool"})
    stubs["homeassistant.config_entries"].ConfigEntry = SimpleNamespace
    stubs["homeassistant.const"].UnitOfTemperature = SimpleNamespace(CELSIUS="°C")
    stubs["homeassistant.core"].HomeAssistant = SimpleNamespace
    stubs["homeassistant.helpers.entity_platform"].AddEntitiesCallback = object
    stubs["websocket"].WebSocketException = Exception
    stubs["websocket"].WebSocketConnectionClosedException = Exception
    bridge_stub = ModuleType(f"{package_name}.nexoBridge")
    bridge_stub.NexoBridge = object
    stubs[bridge_stub.__name__] = bridge_stub
    with patch.dict(sys.modules, stubs):
        return (
            importlib.import_module(f"{package_name}.climate"),
            importlib.import_module(f"{package_name}.nexo_thermostat"),
        )


CLIMATE, THERMOSTAT = _load_climate()


class ClimateTests(unittest.TestCase):
    def make_entity(self):
        # Sample from a real bridge: thermostat limits are degrees, values are tenths.
        thermostat = THERMOSTAT.NexoThermostat(
            None, id=8654337, name="tsBiuro", min=15, max=25,
            state={"is_on": 1, "is_active": 1, "value": 205}, mode=2, thermometer_id=1,
        )
        return CLIMATE.HANexoClimate(thermostat)

    def test_limits_are_exposed_as_min_and_max_temp(self):
        entity = self.make_entity()
        self.assertEqual((entity._attr_min_temp, entity._attr_max_temp), (15, 25))

    def test_native_target_temperature_is_in_degrees(self):
        self.assertEqual(self.make_entity().native_target_temperature, 20.5)


if __name__ == "__main__":
    unittest.main()
