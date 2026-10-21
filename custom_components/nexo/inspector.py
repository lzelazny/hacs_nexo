"""Admin-only inspector for the latest Nexo initial_data messages."""

from hashlib import sha256
from pathlib import Path

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol

from .const import CONF_EXT_COMMANDS, DEFAULT_PORT, DOMAIN


def snapshot(hass, entry):
    """Return the last received payload separately from the resource model."""
    bridge = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    received, payload = bridge.latest_initial_data if bridge else (None, None)
    return {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "host": entry.data["host"],
        "port": entry.data.get("port", DEFAULT_PORT),
        "connected": bool(bridge and bridge.connected),
        "received_at": received,
        "initial_data": payload,
        "configured_commands": entry.options.get(CONF_EXT_COMMANDS, []),
        "commands": sorted(set(entry.options.get(CONF_EXT_COMMANDS, [])) | (
            set(bridge.get_ext_commands()) if bridge else set()
        )),
    }


@websocket_api.websocket_command({vol.Required("type"): "nexo/initial_data"})
@websocket_api.require_admin
@callback
def websocket_initial_data(hass, connection, msg):
    """Read snapshots for all configured Nexo bridges."""
    connection.send_result(msg["id"], [
        snapshot(hass, entry)
        for entry in hass.config_entries.async_entries(DOMAIN)
    ])


@websocket_api.websocket_command({
    vol.Required("type"): "nexo/send_command",
    vol.Required("entry_id"): str,
    vol.Required("command"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_send_command(hass, connection, msg):
    """Send a command through the selected bridge's active connection."""
    command = msg["command"].strip()
    bridge = hass.data.get(DOMAIN, {}).get(msg["entry_id"])
    if not command:
        connection.send_error(msg["id"], "invalid_command", "Enter a command name.")
        return
    if bridge is None or not bridge.connected:
        connection.send_error(msg["id"], "not_connected", "This Nexo bridge is disconnected.")
        return
    try:
        await bridge.async_send_ext_command(command)
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "send_failed", str(err))
        return
    connection.send_result(msg["id"], {"command": command})


@websocket_api.websocket_command({
    vol.Required("type"): "nexo/save_commands",
    vol.Required("entry_id"): str,
    vol.Required("commands"): str,
})
@websocket_api.require_admin
@callback
def websocket_save_commands(hass, connection, msg):
    """Keep command button configuration accessible from the gear page."""
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_found", "Nexo entry not found.")
        return
    commands = sorted({name.strip() for name in msg["commands"].split(",") if name.strip()})
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_EXT_COMMANDS: commands}
    )
    connection.send_result(msg["id"], {"commands": commands})


def _asset_version(path):
    """Change the module URL whenever the shipped JavaScript changes."""
    return sha256(path.read_bytes()).hexdigest()[:12]


async def async_setup_inspector(hass):
    """Register the inspector once for all Nexo entries."""
    panel_path = Path(__file__).parent / "frontend" / "panel.js"
    version = await hass.async_add_executor_job(_asset_version, panel_path)
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/nexo-inspector/panel.js",
            str(panel_path),
            False,
        )
    ])
    websocket_api.async_register_command(hass, websocket_initial_data)
    websocket_api.async_register_command(hass, websocket_send_command)
    websocket_api.async_register_command(hass, websocket_save_commands)
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path="nexo-inspector",
        webcomponent_name="nexo-inspector",
        module_url=f"/nexo-inspector/panel.js?v={version}",
        require_admin=True,
        config_panel_domain=DOMAIN,
    )
