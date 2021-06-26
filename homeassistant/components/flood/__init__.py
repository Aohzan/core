"""Flood integration."""
import asyncio
from datetime import timedelta
import logging

from .pyflood import FloodApi, FloodCannotConnectError, FloodInvalidAuthError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from aiohttp import CookieJar

from .const import (
    CONTROLLER,
    COORDINATOR,
    DOMAIN,
    PLATFORMS,
    UNDO_UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Flood integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Flood from a config entry."""
    config = entry.data

    session = async_create_clientsession(
        hass, verify_ssl=False, cookie_jar=CookieJar(unsafe=True)
    )

    controller = FloodApi(
        config.get(CONF_HOST),
        config.get(CONF_PORT),
        config.get(CONF_USERNAME),
        config.get(CONF_PASSWORD),
        session=session,
    )

    try:
        await controller.auth()
    except FloodInvalidAuthError as exception:
        raise UpdateFailed("Authentication error on Flood") from exception
    except FloodCannotConnectError as exception:
        raise ConfigEntryNotReady from exception

    async def async_update_data():
        """Fetch data from API."""
        try:
            return await controller.global_get()
        except FloodInvalidAuthError as err:
            raise UpdateFailed("Authentication error on Flood") from err
        except FloodCannotConnectError as err:
            raise UpdateFailed(f"Failed to communicating with API: {err}") from err

    scan_interval = config.get(CONF_SCAN_INTERVAL, 30)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(_async_update_listener)

    hass.data[DOMAIN][entry.entry_id] = {
        CONTROLLER: controller,
        COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, controller.host)},
        manufacturer="Jesec",
        model="Flood",
        name=controller.host,
    )

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
