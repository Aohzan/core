"""Config flow to configure the ipx800v4 integration."""
from homeassistant import config_entries
from homeassistant.const import CONF_HOST

from .const import DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class IpxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a IPX800 config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_import(self, import_info):
        """Import a config entry from YAML config."""
        entry = await self.async_set_unique_id(
            f"{DOMAIN}, {import_info.get(CONF_HOST)}"
        )

        if entry:
            self.hass.config_entries.async_update_entry(entry, data=import_info)
            self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=import_info.get(CONF_HOST), data=import_info
        )

    async def async_step_user(self, user_input):
        """Handle a flow initiated by the user."""
        return self.async_show_form(
            step_id="user", errors={"base": "yaml_config_needed"}
        )
