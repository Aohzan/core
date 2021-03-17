"""Support for IPX800 V4 binary sensors."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity

from . import IpxController, IpxDevice
from .const import (
    CONF_COMPONENT,
    CONF_DEVICES,
    CONF_TYPE,
    CONTROLLER,
    DOMAIN,
    GLOBAL_PARALLEL_UPDATES,
    TYPE_DIGITALIN,
    TYPE_VIRTUALOUT,
)

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = GLOBAL_PARALLEL_UPDATES


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """Set up the IPX800 binary sensors."""
    controller = hass.data[DOMAIN][config_entry.entry_id][CONTROLLER]
    devices = filter(
        lambda d: d[CONF_COMPONENT] == "binary_sensor", config_entry.data[CONF_DEVICES]
    )

    entities = []

    for device in devices:
        if device.get(CONF_TYPE) == TYPE_VIRTUALOUT:
            entities.append(VirtualOutBinarySensor(device, controller))
        elif device.get(CONF_TYPE) == TYPE_DIGITALIN:
            entities.append(DigitalInBinarySensor(device, controller))

    async_add_entities(entities, True)


class VirtualOutBinarySensor(IpxDevice, BinarySensorEntity):
    """Representation of a IPX Virtual Out."""

    def __init__(self, device_config, controller: IpxController):
        """Initialize the VirtualOutBinarySensor."""
        super().__init__(device_config, controller)

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return self.coordinator.data[f"VO{self._id}"] == 1


class DigitalInBinarySensor(IpxDevice, BinarySensorEntity):
    """Representation of a IPX Virtual In."""

    def __init__(self, device_config, controller: IpxController):
        """Initialize the DigitalInBinarySensor."""
        super().__init__(device_config, controller)

    @property
    def device_class(self):
        """Return the device class."""
        return self._device_class

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return self.coordinator.data[f"D{self._id}"] == 1
