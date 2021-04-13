"""Support for the GCE IPX800 V4."""
from datetime import timedelta
import logging
import re

from aiohttp import web
from pypx800 import IPX800, Ipx800CannotConnectError, Ipx800InvalidAuthError
import voluptuous as vol

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_DEVICE_CLASS,
    CONF_HOST,
    CONF_ICON,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_USERNAME,
    HTTP_OK,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.typing import ConfigType, HomeAssistantType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_COMPONENT,
    CONF_COMPONENT_ALLOWED,
    CONF_DEVICES,
    CONF_EXT_ID,
    CONF_ID,
    CONF_IDS,
    CONF_TRANSITION,
    CONF_TYPE,
    CONF_TYPE_ALLOWED,
    CONTROLLER,
    COORDINATOR,
    DEFAULT_TRANSITION,
    DOMAIN,
    REQUEST_REFRESH_DELAY,
    TYPE_RELAY,
    TYPE_X4VR,
    TYPE_XPWM_RGB,
    TYPE_XPWM_RGBW,
    UNDO_UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)

DEVICE_CONFIG_SCHEMA_ENTRY = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_COMPONENT): cv.string,
        vol.Required(CONF_TYPE): cv.string,
        vol.Optional(CONF_ID): cv.positive_int,
        vol.Optional(CONF_IDS): cv.ensure_list,
        vol.Optional(CONF_EXT_ID): cv.positive_int,
        vol.Optional(CONF_ICON): cv.icon,
        vol.Optional(CONF_TRANSITION, default=DEFAULT_TRANSITION): vol.Coerce(float),
        vol.Optional(CONF_DEVICE_CLASS): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    }
)

GATEWAY_CONFIG = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=80): cv.port,
        vol.Optional(CONF_SCAN_INTERVAL, default=10): cv.positive_int,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_DEVICES, default=[]): vol.All(
            cv.ensure_list, [DEVICE_CONFIG_SCHEMA_ENTRY]
        ),
    }
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.All(cv.ensure_list, [GATEWAY_CONFIG])})


async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    """Set up the IPX800v4 components."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry) -> bool:
    """Set up the IPX800v4."""
    session = async_get_clientsession(hass, False)

    ipx = IPX800(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        api_key=entry.data[CONF_API_KEY],
        username=entry.data.get(CONF_USERNAME),
        password=entry.data.get(CONF_PASSWORD),
        session=session,
    )

    try:
        await ipx.ping()
    except Ipx800CannotConnectError as exception:
        raise ConfigEntryNotReady from exception

    async def async_update_data():
        """Fetch data from API."""
        try:
            return await ipx.global_get()
        except Ipx800InvalidAuthError as err:
            raise UpdateFailed("Authentication error on Eco-Devices") from err
        except Ipx800CannotConnectError as err:
            raise UpdateFailed(f"Failed to communicating with API: {err}") from err

    scan_interval = entry.data.get(CONF_SCAN_INTERVAL)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
        request_refresh_debouncer=Debouncer(
            hass,
            _LOGGER,
            cooldown=REQUEST_REFRESH_DELAY,
            immediate=True,
        ),
    )

    undo_listener = entry.add_update_listener(_async_update_listener)

    await coordinator.async_refresh()

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, ipx.host)},
        manufacturer="GCE",
        model="IPX800 V4",
        name=ipx.host,
    )

    devices = build_device_list(entry.data.get(CONF_DEVICES))

    hass.data[DOMAIN][entry.entry_id] = {
        CONTROLLER: ipx,
        COORDINATOR: coordinator,
        CONF_DEVICES: devices,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for component in CONF_COMPONENT_ALLOWED:
        _LOGGER.debug("Load component %s.", component)
        devices_by_component = filter(lambda d: d[CONF_COMPONENT] == component, devices)
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, devices_by_component)
        )

    # Provide endpoints for the IPX to call to push states
    hass.http.register_view(IpxRequestView)
    hass.http.register_view(IpxRequestDataView)

    return True


async def async_unload_entry(hass: HomeAssistantType, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    for component in CONF_COMPONENT_ALLOWED:
        await hass.config_entries.async_forward_entry_unload(entry, component)

    del hass.data[DOMAIN]

    return True


async def _async_update_listener(hass, config_entry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


def build_device_list(devices_config: dict = []) -> dict:
    """Check and build device list from config."""
    _LOGGER.debug("Check and build devices configuration")

    devices = []
    for device_config in devices_config:
        _LOGGER.debug("Read device name: %s", device_config.get(CONF_NAME))

        # Check if component is supported
        if device_config[CONF_COMPONENT] not in CONF_COMPONENT_ALLOWED:
            _LOGGER.error(
                "Device %s skipped: %s %s not correct or supported.",
                device_config[CONF_NAME],
                CONF_COMPONENT,
                device_config[CONF_COMPONENT],
            )
            continue

        # Check if type is supported
        if device_config[CONF_TYPE] not in CONF_TYPE_ALLOWED:
            _LOGGER.error(
                "Device %s skipped: %s %s not correct or supported.",
                device_config[CONF_NAME],
                CONF_TYPE,
                device_config[CONF_TYPE],
            )
            continue

        # Check if X4VR have extension id set
        if device_config[CONF_TYPE] == TYPE_X4VR and CONF_EXT_ID not in device_config:
            _LOGGER.error(
                "Device %s skipped: %s must have %s set.",
                device_config[CONF_NAME],
                TYPE_X4VR,
                CONF_EXT_ID,
            )
            continue

        # Check if RGB/RBW or FP/RELAY have ids set
        if (
            device_config[CONF_TYPE] == TYPE_XPWM_RGB
            or device_config[CONF_TYPE] == TYPE_XPWM_RGBW
            or (
                device_config[CONF_TYPE] == TYPE_RELAY
                and device_config[CONF_COMPONENT] == "climate"
            )
        ) and CONF_IDS not in device_config:
            _LOGGER.error(
                "Device %s skipped: RGB/RGBW must have %s set.",
                device_config[CONF_NAME],
                CONF_IDS,
            )
            continue

        # Check if other device types have id set
        if (
            device_config[CONF_TYPE] != TYPE_XPWM_RGB
            and device_config[CONF_TYPE] != TYPE_XPWM_RGBW
            and not (
                device_config[CONF_TYPE] == TYPE_RELAY
                and device_config[CONF_COMPONENT] == "climate"
            )
            and CONF_ID not in device_config
        ):
            _LOGGER.error(
                "Device %s skipped: must have %s set.",
                device_config[CONF_NAME],
                CONF_ID,
            )
            continue

        devices.append(device_config)
        _LOGGER.info(
            "Device %s added (component: %s).",
            device_config[CONF_NAME],
            device_config[CONF_COMPONENT],
        )
    return devices


class IpxRequestView(HomeAssistantView):
    """Provide a page for the device to call."""

    requires_auth = False
    url = "/api/ipx800v4/{entity_id}/{state}"
    name = "api:ipx800v4"

    async def get(self, request, entity_id, state):
        """Respond to requests from the device."""
        hass = request.app["hass"]
        old_state = hass.states.get(entity_id)
        _LOGGER.debug("Update %s to state %s.", entity_id, state)
        if old_state:
            hass.states.async_set(entity_id, state, old_state.attributes)
            return web.Response(status=HTTP_OK, text="OK")
        _LOGGER.warning("Entity not found for state updating: %s", entity_id)


class IpxRequestDataView(HomeAssistantView):
    """Provide a page for the device to call for send multiple data at once."""

    requires_auth = False
    url = "/api/ipx800v4_data/{data}"
    name = "api:ipx800v4_data"

    async def get(self, request, data):
        """Respond to requests from the device."""
        hass = request.app["hass"]
        entities_data = data.split("&")
        for entity_data in entities_data:
            entity_id = entity_data.split("=")[0]
            state = "on" if entity_data.split("=")[1] in ["1", "on", "true"] else "off"

            old_state = hass.states.get(entity_id)
            _LOGGER.debug("Update %s to state %s.", entity_id, state)
            if old_state:
                hass.states.async_set(entity_id, state, old_state.attributes)
            else:
                _LOGGER.warning("Entity not found for state updating: %s", entity_id)

        return web.Response(status=HTTP_OK, text="OK")


class IpxDevice(CoordinatorEntity):
    """Representation of a IPX800 generic device entity."""

    def __init__(
        self,
        device_config: dict,
        ipx: IPX800,
        coordinator: DataUpdateCoordinator,
        suffix_name: str = "",
    ):
        """Initialize the device."""
        super().__init__(coordinator)

        self.ipx = ipx

        self._name = device_config.get(CONF_NAME)
        self._device_name = self._name
        if suffix_name:
            self._name += f" {suffix_name}"

        self._device_class = device_config.get(CONF_DEVICE_CLASS)
        self._unit_of_measurement = device_config.get(CONF_UNIT_OF_MEASUREMENT)
        self._transition = int(
            device_config.get(CONF_TRANSITION, DEFAULT_TRANSITION) * 1000
        )
        self._icon = device_config.get(CONF_ICON)
        self._ipx_type = device_config.get(CONF_TYPE)
        self._component = device_config.get(CONF_COMPONENT)
        self._id = device_config.get(CONF_ID)
        self._ext_id = device_config.get(CONF_EXT_ID)
        self._ids = device_config.get(CONF_IDS, [])

        self._supported_features = 0

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.ipx.host)},
            "via_device": (DOMAIN, self.ipx.host),
        }

    @property
    def unique_id(self):
        """Return an unique id."""
        return "_".join(
            [
                DOMAIN,
                self.ipx.host,
                self._component,
                re.sub("[^A-Za-z0-9_]+", "", self._name.replace(" ", "_")).lower(),
            ]
        )

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features
