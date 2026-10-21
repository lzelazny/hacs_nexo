"""Download the latest init snapshot through Home Assistant diagnostics."""

from copy import deepcopy

from homeassistant.components.diagnostics import async_redact_data

from .inspector import snapshot


async def async_get_config_entry_diagnostics(hass, entry):
    """Return an independent snapshot with common secrets redacted."""
    return async_redact_data(deepcopy(snapshot(hass, entry)), {
        "host", "password", "token", "access_token", "refresh_token",
        "api_key", "secret", "username",
    })
