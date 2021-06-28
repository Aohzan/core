"""Config flow to configure the Flood integration."""
from aiohttp import CookieJar
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import CONF_MAX_SPEED_LIMIT, DOMAIN
from .pyflood import FloodApi, FloodCannotConnectError, FloodInvalidAuthError

BASE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.1.243"): str,
        vol.Required(CONF_PORT, default=80): int,
        vol.Required(CONF_SCAN_INTERVAL, default=30): int,
        vol.Optional(CONF_USERNAME, default="matthieu"): str,
        vol.Optional(CONF_PASSWORD, default="7tp57Mu9UKrnEVLwzZ2Y"): str,
        vol.Required(CONF_MAX_SPEED_LIMIT, default=2000): int,
    }
)


@config_entries.HANDLERS.register(DOMAIN)
class FloodConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Flood config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=BASE_SCHEMA, errors=errors
            )

        entry = await self.async_set_unique_id(f"{DOMAIN}, {user_input.get(CONF_HOST)}")

        if entry:
            self._abort_if_unique_id_configured()

        session = async_create_clientsession(
            self.hass, verify_ssl=False, cookie_jar=CookieJar(unsafe=True)
        )

        controller = FloodApi(
            user_input.get(CONF_HOST),
            user_input.get(CONF_PORT),
            user_input.get(CONF_USERNAME),
            user_input.get(CONF_PASSWORD),
            session=session,
        )

        try:
            await controller.auth()
            await controller.connected
        except FloodInvalidAuthError:
            errors["base"] = "invalid_auth"
            return self.async_show_form(
                step_id="user", data_schema=BASE_SCHEMA, errors=errors
            )
        except FloodCannotConnectError:
            errors["base"] = "cannot_connect"
            return self.async_show_form(
                step_id="user", data_schema=BASE_SCHEMA, errors=errors
            )

        return self.async_create_entry(title=user_input.get(CONF_HOST), data=user_input)
