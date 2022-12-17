"""The Polar component."""

import logging


from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):
    """Set up Polar integration from a config entry."""
    _LOGGER.debug("Setting up Polar integration")

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, SENSOR_DOMAIN)
    )

    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading Polar integration")

    await hass.config_entries.async_forward_entry_unload(entry, SENSOR_DOMAIN)

    return True
