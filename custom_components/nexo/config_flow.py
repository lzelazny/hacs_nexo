"""Config flow for nexo integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_EXT_COMMANDS, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

def connection_schema(data=None):
    """Build connection fields for new and existing entries."""
    data = data or {}
    return vol.Schema({
        vol.Required("host", default=data.get("host", "")): str,
        vol.Required("port", default=data.get("port", DEFAULT_PORT)): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
    })


STEP_USER_DATA_SCHEMA = connection_schema()


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    hub = PlaceholderHub(data["host"])

    # if not await hub.authenticate(data["username"], data["password"]):
    #   raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Karta MM"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for nexo."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the per-entry external command options form."""
        return NexoOptionsFlow(config_entry)

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        """Update connection settings without replacing the entry."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            # The existing update listener reloads after saving.
            changed = self.hass.config_entries.async_update_entry(
                entry, data={**entry.data, **user_input}
            )
            # Failed setup has no update listener; retry the connection explicitly.
            if not changed or entry.entry_id not in self.hass.data.get(DOMAIN, {}):
                await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")
        return self.async_show_form(
            step_id="reconfigure", data_schema=connection_schema(entry.data)
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class NexoOptionsFlow(config_entries.OptionsFlow):
    """Allow manually configured commands when discovery is unavailable."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input=None):
        """Choose command configuration or the latest JSON inspector."""
        return self.async_show_menu(
            step_id="init", menu_options=["commands", "inspect_json"]
        )

    async def async_step_inspect_json(self, user_input=None):
        """Link to the inspector for this specific bridge without saving options."""
        if user_input is not None:
            return self.async_abort(reason="inspector_closed")
        return self.async_show_form(
            step_id="inspect_json",
            description_placeholders={
                "inspector_url": f"/nexo-inspector?config_entry={self._entry.entry_id}"
            },
            last_step=True,
        )

    async def async_step_commands(self, user_input=None):
        """Save comma separated command names and reload the integration."""
        if user_input is not None:
            commands = sorted(
                {name.strip() for name in user_input.get(CONF_EXT_COMMANDS, "").split(",") if name.strip()}
            )
            return self.async_create_entry(
                title="", data={**self._entry.options, CONF_EXT_COMMANDS: commands}
            )
        current = ", ".join(self._entry.options.get(CONF_EXT_COMMANDS, []))
        return self.async_show_form(
            step_id="commands",
            data_schema=vol.Schema(
                {vol.Optional(CONF_EXT_COMMANDS, default=current): str}
            ),
        )
