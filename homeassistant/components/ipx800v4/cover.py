"""Support for IPX800 V4 covers."""
import logging

from pypx800 import IPX800, X4VR

from homeassistant.components.cover import (
    ATTR_POSITION,
    DEVICE_CLASS_SHUTTER,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
    CoverEntity,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import IpxDevice
from .const import (
    CONF_DEVICES,
    CONF_TYPE,
    CONTROLLER,
    COORDINATOR,
    DOMAIN,
    GLOBAL_PARALLEL_UPDATES,
    TYPE_X4VR,
)

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = GLOBAL_PARALLEL_UPDATES


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """Set up the IPX800 covers."""
    controller = hass.data[DOMAIN][config_entry.entry_id][CONTROLLER]
    devices = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICES]
    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    entities = []

    for device in devices:
        if device.get(CONF_TYPE) == TYPE_X4VR:
            entities.append(X4VRCover(device, controller, coordinator))

    async_add_entities(entities, True)


class X4VRCover(IpxDevice, CoverEntity):
    """Representation of a IPX Cover through X4VR."""

    def __init__(
        self,
        device_config: dict,
        ipx: IPX800,
        coordinator: DataUpdateCoordinator,
    ):
        """Initialize the X4VRCover."""
        super().__init__(device_config, ipx, coordinator)
        self.control = X4VR(ipx, self._ext_id, self._id)

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class or DEVICE_CLASS_SHUTTER

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION

    @property
    def is_closed(self) -> bool:
        """Return the state."""
        return int(self.coordinator.data[f"VR{self._ext_id}-{self._id}"]) == 100

    @property
    def current_cover_position(self) -> int:
        """Return the current cover position."""
        return 100 - int(self.coordinator.data[f"VR{self._ext_id}-{self._id}"])

    async def async_open_cover(self, **kwargs):
        """Open cover."""
        self.control.on()

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        self.control.off()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        self.control.stop()

    def set_cover_position(self, **kwargs):
        """Set the cover to a specific position."""
        self.control.set_level(kwargs.get(ATTR_POSITION))
