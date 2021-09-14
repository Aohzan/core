"""Support for rfplayer."""

import glob
import socket
import threading
import time
import logging
import asyncio
from serial import SerialException
from .rfplayer.rfpprotocol import create_rfplayer_connection
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from time import sleep
import asyncio
import binascii
import copy
import functools
import logging

import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.binary_sensor import DEVICE_CLASSES_SCHEMA
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_STATE,
    CONF_COMMAND,
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
    STATE_ON,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, ATTR_EVENT, DATA_RFOBJECT

_LOGGER = logging.getLogger(__name__)
from homeassistant.const import (
    ATTR_DEVICE_ID,
    CONF_COMMAND_OFF,
    CONF_COMMAND_ON,
    CONF_DEVICE,
    CONF_DEVICE_CLASS,
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_HOST,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
)

PLATFORMS = ["sensor"]

SIGNAL_AVAILABILITY = "rfplayer_device_available"
SIGNAL_EVENT = "rfplayer_event"

EVENT_BUTTON_PRESSED = "button_pressed"
EVENT_KEY_COMMAND = "command"
EVENT_KEY_ID = "id"
EVENT_KEY_SENSOR = "sensor"
EVENT_KEY_UNIT = "unit"

SERVICE_SEND_COMMAND = "send_command"
SEND_COMMAND_SCHEMA = vol.Schema(
    {vol.Required(CONF_DEVICE_ID): cv.string, vol.Required(CONF_COMMAND): cv.string}
)


async def async_setup(hass, config):
    """Set up the Eco-Devices integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, entry):
    """Set up Eco-Devices from a config entry."""
    config = entry.data

    async def async_send_command(call):
        """Send Rflink command."""
        _LOGGER.debug("Rflink command for %s", str(call.data))
        async_dispatcher_send(
            hass,
            SIGNAL_EVENT,
            {
                EVENT_KEY_ID: call.data.get(CONF_DEVICE_ID),
                EVENT_KEY_COMMAND: call.data.get(CONF_COMMAND),
            },
        )

    hass.services.async_register(
        DOMAIN, SERVICE_SEND_COMMAND, async_send_command, schema=SEND_COMMAND_SCHEMA
    )

    @callback
    def event_callback(event):
        _LOGGER.info("event receive %s", event)

    @callback
    def reconnect(exc=None):
        """Schedule reconnect after connection has been unexpectedly lost."""
        _LOGGER.warning("Disconnected from Rfplayer, reconnecting")
        async_dispatcher_send(hass, SIGNAL_AVAILABILITY, False)
        hass.async_create_task(connect())

    async def connect():
        """Set up connection and hook it into HA for reconnect/shutdown."""
        _LOGGER.info("Initiating Rfplayer connection")
        connection = create_rfplayer_connection(
            port=config[CONF_DEVICE],
            event_callback=event_callback,
            disconnect_callback=reconnect,
            loop=hass.loop,
            # ignore=config[DOMAIN][CONF_IGNORE_DEVICES],
        )

        try:
            with async_timeout.timeout(30):
                transport, protocol = await connection

        except (
            SerialException,
            OSError,
            asyncio.TimeoutError,
        ) as exc:
            reconnect_interval = 10
            _LOGGER.exception(
                "Error connecting to Rflink, reconnecting in %s", reconnect_interval
            )
            # Connection to Rflink device is lost, make entities unavailable
            async_dispatcher_send(hass, SIGNAL_AVAILABILITY, False)

            hass.loop.call_later(reconnect_interval, reconnect, exc)
            return

        async_dispatcher_send(hass, SIGNAL_AVAILABILITY, True)

        # handle shutdown of Rfplayer asyncio transport
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, lambda x: transport.close()
        )

        _LOGGER.info("Connected to Rfplayer")

    hass.async_create_task(connect())
    async_dispatcher_connect(hass, SIGNAL_EVENT, event_callback)

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, config[CONF_DEVICE])},
        manufacturer="GCE",
        model="RFPlayer",
        name="RFPlayer",
    )

    # for platform in PLATFORMS:
    #     hass.async_create_task(
    #         hass.config_entries.async_forward_entry_setup(entry, platform)
    #     )

    return True
