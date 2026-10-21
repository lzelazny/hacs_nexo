"""Weather parsing and entity lifecycle checks without a running HA instance."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "nexo"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class _WeatherEntity:
    async def async_added_to_hass(self):
        pass

    async def async_will_remove_from_hass(self):
        pass

    def async_write_ha_state(self):
        self.writes = getattr(self, "writes", 0) + 1


def _load_weather():
    """Load the production files with dependencies scoped to this function."""
    package = ModuleType("_nexo_weather_tests")
    package.__path__ = [str(COMPONENT)]
    weather_dependency = ModuleType("homeassistant.components.weather")
    weather_dependency.WeatherEntity = _WeatherEntity
    const_dependency = ModuleType("homeassistant.const")
    const_dependency.UnitOfSpeed = SimpleNamespace(METERS_PER_SECOND="m/s")
    const_dependency.UnitOfTemperature = SimpleNamespace(CELSIUS="°C")
    core_dependency = ModuleType("homeassistant.core")
    core_dependency.callback = lambda function: function
    component_const = ModuleType("_nexo_weather_tests.const")
    component_const.DOMAIN = "nexo"
    modules = {
        "_nexo_weather_tests": package,
        "_nexo_weather_tests.const": component_const,
        "homeassistant": ModuleType("homeassistant"),
        "homeassistant.components": ModuleType("homeassistant.components"),
        "homeassistant.components.weather": weather_dependency,
        "homeassistant.const": const_dependency,
        "homeassistant.core": core_dependency,
    }
    with patch.dict(sys.modules, modules):
        model = _load("_nexo_weather_tests.nexo_weather", COMPONENT / "nexo_weather.py")
        entity = _load("_nexo_weather_tests.weather", COMPONENT / "weather.py")
    return model.NexoWeather, entity.HANexoWeather


NexoWeather, HANexoWeather = _load_weather()


class WeatherModelTests(unittest.TestCase):
    def test_partial_messages_keep_existing_observations(self):
        weather = NexoWeather()
        weather.update_from_bridge({"devices/0": {
            "pictogram": "cloud_sun", "air": {"temperature": 21.5, "wind": 3},
            "conditions": {"sun": True},
            "light": {"intensity": 14, "angle": 45, "north": 3, "S": 7},
        }})
        weather.update_from_bridge({"state": {"value": {"N": 4, "E": 4}}})
        self.assertEqual(weather.temperature_c, 21.5)
        self.assertEqual(weather.wind_ms, 3.0)
        self.assertEqual(weather.pictogram, "CLOUD_SUN")
        self.assertEqual(weather.light_quadrants, {"N": 3.0, "S": 7.0})
        self.assertEqual(weather.wind_dir_deg, 45.0)
        self.assertEqual(weather.wind_dir_cardinal, "NE")

    def test_malformed_values_do_not_break_or_replace_valid_measurements(self):
        weather = NexoWeather(temperature_c=21.0, wind_ms=3.0)
        for data in (None, [], "bad", {"devices/0": []},
                     {"devices/0": {"air": "bad", "light": True}},
                     {"state": []}):
            weather.update_from_bridge(data)
        weather.update_from_bridge({"devices/0": {
            "pictogram": [], "conditions": [],
            "air": {"temperature": float("nan"), "wind": -1},
            "light": {"angle": float("inf"), "N": True},
        }, "state": {"value": {None: 1, "S": float("inf"), "E": False}}})
        self.assertEqual(weather.temperature_c, 21.0)
        self.assertEqual(weather.wind_ms, 3.0)
        self.assertIsNone(weather.pictogram)
        self.assertIsNone(weather.light_angle)
        self.assertEqual(weather.wind_rose, {})
        weather.update_from_bridge({"devices/0": {"air": {"temperature": 10**400}}})
        self.assertEqual(weather.temperature_c, 21.0)

    def test_calm_wind_clears_previous_direction(self):
        weather = NexoWeather()
        weather.update_from_bridge({"state": {"value": {"E": 1}}})
        self.assertEqual(weather.wind_dir_deg, 90.0)
        weather.update_from_bridge({"state": {"value": {"N": 0, "E": 0}}})
        self.assertIsNone(weather.wind_dir_deg)
        self.assertIsNone(weather.wind_dir_cardinal)


class WeatherEntityTests(unittest.IsolatedAsyncioTestCase):
    def make_bridge(self):
        weather = NexoWeather()
        listeners = set()
        return SimpleNamespace(
            get_weather_resources=lambda: [weather],
            register_weather_listener=listeners.add,
            unregister_weather_listener=listeners.discard,
            weather=weather,
            listeners=listeners,
        )

    async def test_listener_is_removed_on_unload_and_updates_write_state(self):
        bridge = self.make_bridge()
        entity = HANexoWeather(bridge, "entry-1")
        await entity.async_added_to_hass()
        self.assertEqual(len(bridge.listeners), 1)
        bridge.weather.update_from_bridge({"devices/0": {"air": {"temperature": 8}}})
        for callback in tuple(bridge.listeners):
            callback()
        self.assertEqual(entity.native_temperature, 8.0)
        self.assertEqual(entity.writes, 1)
        await entity.async_will_remove_from_hass()
        self.assertFalse(bridge.listeners)

    async def test_unknown_condition_is_not_reported_as_cloudy(self):
        bridge = self.make_bridge()
        entity = HANexoWeather(bridge, "entry-1")
        self.assertFalse(entity.available)
        self.assertIsNone(entity.condition)
        bridge.weather.temperature_c = 0
        bridge.weather.wind_ms = 0
        self.assertTrue(entity.available)
        self.assertEqual(entity.native_temperature, 0)
        self.assertEqual(entity.native_wind_speed, 0)
        self.assertFalse(entity._attr_should_poll)
        bridge.weather.conditions = {"rain": "false", "sun": []}
        self.assertIsNone(entity.condition)
        bridge.weather.conditions = {"rain": 1}
        self.assertEqual(entity.condition, "rainy")

    async def test_weather_ids_are_stable_and_different_between_entries(self):
        bridge = self.make_bridge()
        first = HANexoWeather(bridge, "entry-1")
        reloaded = HANexoWeather(bridge, "entry-1")
        second = HANexoWeather(bridge, "entry-2")
        self.assertEqual(first._attr_unique_id, reloaded._attr_unique_id)
        self.assertNotEqual(first._attr_unique_id, second._attr_unique_id)


if __name__ == "__main__":
    unittest.main()
