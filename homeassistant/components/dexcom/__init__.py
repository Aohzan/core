"""The Dexcom integration."""
from datetime import timedelta
import logging

from pydexcom import AccountError, Dexcom, SessionError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_UNIT_OF_MEASUREMENT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_SERVER,
    COORDINATOR,
    DOMAIN,
    MG_DL,
    PLATFORMS,
    SERVER_OUS,
    UNDO_UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=180)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dexcom from a config entry."""
    try:
        dexcom = await hass.async_add_executor_job(
            Dexcom,
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            entry.data[CONF_SERVER] == SERVER_OUS,
        )
    except AccountError:
        return False
    except SessionError as error:
        raise ConfigEntryNotReady from error

    if not entry.options:
        hass.config_entries.async_update_entry(
            entry, options={CONF_UNIT_OF_MEASUREMENT: MG_DL}
        )

    async def async_update_data():
        try:
            return await hass.async_add_executor_job(dexcom.get_current_glucose_reading)
        except SessionError as error:
            raise UpdateFailed(error) from error

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=async_update_data,
            update_interval=SCAN_INTERVAL,
        ),
        UNDO_UPDATE_LISTENER: entry.add_update_listener(update_listener),
    }

    await hass.data[DOMAIN][entry.entry_id][
        COORDINATOR
    ].async_config_entry_first_refresh()

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def update_listener(hass, entry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
