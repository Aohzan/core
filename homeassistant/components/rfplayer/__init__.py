"""Support for rfplayer."""

import logging
import asyncio
import serial
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr

DOMAIN = "rfplayer"
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


async def async_setup(hass, config):
    """Set up the Eco-Devices integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, entry):
    """Set up Eco-Devices from a config entry."""
    config = entry.data
    _LOGGER.debug("setup %s", config)

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, config[CONF_DEVICE])},
        manufacturer="GCE",
        model="RfPlayer",
        name="RfPlayer",
    )

    # for platform in PLATFORMS:
    #     hass.async_create_task(
    #         hass.config_entries.async_forward_entry_setup(entry, platform)
    #     )

    return True
