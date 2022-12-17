"""Config flow for Polar Flow."""
import logging

import aiohttp
import requests
import voluptuous as vol

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import callback
from homeassistant.components.http import HomeAssistantView

from .accesslink import AccessLink

from .const import (
    DOMAIN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_USER_ID,
    CONF_ACCESS_TOKEN,
    AUTH_CALLBACK_NAME,
    AUTH_CALLBACK_PATH,
)

_LOGGER = logging.getLogger(__name__)

BASE_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_CLIENT_ID, default="bcc5105e-257d-41ed-a33c-5f485170a87e"
        ): str,
        vol.Required(
            CONF_CLIENT_SECRET, default="322976b3-96cc-4cd6-b7f8-9a858e320e7b"
        ): str,
    }
)


@config_entries.HANDLERS.register(DOMAIN)
class PolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Polar config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize class variables."""
        self.data = {}
        self.accesslink: AccessLink = None

    def get_callback_url(self) -> str:
        return f"{self.hass.config.external_url}{AUTH_CALLBACK_PATH}"

    # @property
    # def accesslink(self):
    #     callback_url = get_url_callback(self.hass)

    #     if not self.accesslink_client:
    #         self.accesslink_client = AccessLink(
    #             client_id=self.data[CONF_CLIENT_ID],
    #             client_secret=self.data[CONF_CLIENT_SECRET],
    #             redirect_url=callback_url,
    #         )

    #     return self.accesslink_client

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is None:

            self.hass.http.register_view(PolarAuthCallbackView())

            return self.async_show_form(
                step_id="user",
                description_placeholders={"callback_url": self.get_callback_url()},
                data_schema=BASE_SCHEMA,
                errors=errors,
            )

        self.data = user_input
        self.accesslink = AccessLink(
            client_id=self.data[CONF_CLIENT_ID],
            client_secret=self.data[CONF_CLIENT_SECRET],
            redirect_url=self.get_callback_url,
        )

        return await self.async_step_oauth()

    async def async_step_oauth(self, user_input=None):
        if not user_input:
            return self.async_external_step(
                step_id="oauth",
                url=self.accesslink.authorization_url,
            )

        token_response = await self.hass.async_add_executor_job(
            self.accesslink.get_access_token, user_input["code"]
        )

        self.data[CONF_USER_ID] = token_response["x_user_id"]
        self.data[CONF_ACCESS_TOKEN] = token_response["access_token"]

        return self.async_external_step_done(next_step_id="finish")

    async def async_step_finish(self, user_input=None):

        try:
            await self.hass.async_add_executor_job(
                self.accesslink.users.register, self.data[CONF_ACCESS_TOKEN]
            )
        except requests.exceptions.HTTPError as err:
            # Error 409 Conflict means that the user has already been registered for this client, which is okay.
            if err.response.status_code != 409:
                raise err

        return self.async_create_entry(title="Polar", data=self.data)


class PolarAuthCallbackView(HomeAssistantView):
    """Polar Accesslink Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME

    @callback
    async def get(self, request):
        """Receive authorization token."""
        hass = request.app["hass"]

        flow_id = request.query["state"]
        code = request.query["code"]

        _LOGGER.debug("Received auth code from external call")

        try:
            await hass.config_entries.flow.async_configure(flow_id, {"code": code})

            return aiohttp.web_response.Response(
                status=200,
                headers={"content-type": "text/html"},
                text="<script>window.close()</script>",
            )

        except data_entry_flow.UnknownFlow:
            return aiohttp.web_response.Response(status=400, text="Unknown flow")
