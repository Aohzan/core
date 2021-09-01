"""Config flow to configure the rfplayer integration."""
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.const import CONF_DEVICE
import serial
import os
from .const import DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class RfPlayerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a rfplayer config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            user_selection = user_input[CONF_DEVICE]
            dev_path = await self.hass.async_add_executor_job(
                get_serial_by_id, user_selection
            )

            try:
                # TODO test
                # data = await self.async_validate_rfx(device=dev_path)
                data = {CONF_DEVICE: dev_path}
            except CannotConnect:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(title=DOMAIN, data=data)

        ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)
        list_of_ports = {}
        for port in ports:
            list_of_ports[
                port.device
            ] = f"{port}, s/n: {port.serial_number or 'n/a'}" + (
                f" - {port.manufacturer}" if port.manufacturer else ""
            )
        # list_of_ports[CONF_MANUAL_PATH] = CONF_MANUAL_PATH

        schema = vol.Schema({vol.Required(CONF_DEVICE): vol.In(list_of_ports)})
        return self.async_show_form(
            step_id="setup_serial",
            data_schema=schema,
            errors=errors,
        )


def get_serial_by_id(dev_path: str) -> str:
    """Return a /dev/serial/by-id match for given device if available."""
    by_id = "/dev/serial/by-id"
    if not os.path.isdir(by_id):
        return dev_path

    for path in (entry.path for entry in os.scandir(by_id) if entry.is_symlink()):
        if os.path.realpath(path) == dev_path:
            return path
    return dev_path


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""
