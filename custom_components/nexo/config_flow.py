"""Config flow for Nexo integration (setup + options)."""

from __future__ import annotations

import logging
from typing import Any, Dict

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_EXT_COMMANDS

_LOGGER = logging.getLogger(__name__)


class NexoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nexo."""

    VERSION = 1

    async def async_step_user(self, user_input: Dict[str, Any] | None = None) -> FlowResult:
        """Initial step: ask for host."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            host = (user_input.get(CONF_HOST) or "").strip()
            if not host:
                errors["base"] = "invalid_host"
            else:
                # One instance per host
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Nexo ({host})", data={CONF_HOST: host}
                )

        schema = vol.Schema({vol.Required(CONF_HOST): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, user_input: Dict[str, Any] | None = None) -> FlowResult:
        """Support YAML import if ever needed."""
        return await self.async_step_user(user_input)


async def _options_schema(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> vol.Schema:
    """Build options form schema."""
    current_list = entry.options.get(CONF_EXT_COMMANDS, [])
    current_csv = ", ".join(current_list) if isinstance(current_list, list) else str(current_list or "")
    return vol.Schema(
        {
            vol.Optional(
                CONF_EXT_COMMANDS,
                description={"suggested_value": current_csv},
            ): str,
        }
    )


class NexoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Nexo options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: Dict[str, Any] | None = None) -> FlowResult:
        """Options: initial (and only) step."""
        if user_input is not None:
            raw = user_input.get(CONF_EXT_COMMANDS, "")
            # csv -> list
            ext_cmds = [s.strip() for s in cv.ensure_list_csv(raw or "") if s.strip()]

            new_options = dict(self.entry.options)
            new_options[CONF_EXT_COMMANDS] = ext_cmds
            return self.async_create_entry(title="", data=new_options)

    # pokaż formularz
        schema = await _options_schema(self.hass, self.entry)
        return self.async_show_form(step_id="init", data_schema=schema)
