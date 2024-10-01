"""MCZ Maestro integration."""

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONTROLLER, COORDINATOR, DOMAIN, UNDO_UPDATE_LISTENER
from .maestro import MaestroController

_LOGGER = logging.getLogger(__name__)


PLATFORMS = [Platform.CLIMATE, Platform.NUMBER, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MCZ Maestro from a config entry."""
    config = entry.data

    controller = MaestroController(config[CONF_HOST], config[CONF_PORT])

    if not controller.connected:
        _LOGGER.error("Can't connect to MCZ")
        raise ConfigEntryNotReady
    _LOGGER.debug("Connected to MCZ")

    async def async_update_data():
        """Fetch data from API."""
        controller.send("C|RecuperoInfo")
        return controller.receive()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=config[CONF_SCAN_INTERVAL]),
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(_async_update_listener)

    hass.data[DOMAIN][entry.entry_id] = {
        CONTROLLER: controller,
        COORDINATOR: coordinator,
        CONF_HOST: controller.host,
        CONF_PORT: controller.port,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, controller.host + controller.port)},
        manufacturer="MCZ",
        model="Maestro",
        name=f"MCZ Maestro {controller.host}:{controller.port}",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
