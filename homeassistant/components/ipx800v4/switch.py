"""Support for IPX800 V4 switches."""
import logging

from pypx800 import IPX800, Relay, VInput, VOutput

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import IpxDevice
from .const import (
    CONF_DEVICES,
    CONF_TYPE,
    CONTROLLER,
    COORDINATOR,
    DOMAIN,
    GLOBAL_PARALLEL_UPDATES,
    TYPE_RELAY,
    TYPE_VIRTUALIN,
    TYPE_VIRTUALOUT,
)

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = GLOBAL_PARALLEL_UPDATES


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """Set up the IPX800 switches."""
    controller = hass.data[DOMAIN][config_entry.entry_id][CONTROLLER]
    devices = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICES]
    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    entities = []

    for device in devices:
        if device.get(CONF_TYPE) == TYPE_RELAY:
            entities.append(RelaySwitch(device, controller, coordinator))
        elif device.get(CONF_TYPE) == TYPE_VIRTUALOUT:
            entities.append(VirtualOutSwitch(device, controller, coordinator))
        elif device.get(CONF_TYPE) == TYPE_VIRTUALIN:
            entities.append(VirtualInSwitch(device, controller, coordinator))

    async_add_entities(entities, True)


class RelaySwitch(IpxDevice, SwitchEntity):
    """Representation of a IPX Switch through relay."""

    def __init__(
        self,
        device_config: dict,
        ipx: IPX800,
        coordinator: DataUpdateCoordinator,
    ):
        """Initialize the RelaySwitch."""
        super().__init__(device_config, ipx, coordinator)
        self.control = Relay(ipx, self._id)

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return self.coordinator.data[f"R{self._id}"] == 1

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        self.control.on()

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        self.control.off()

    def toggle(self, **kwargs):
        """Toggle the switch."""
        self.control.toggle()


class VirtualOutSwitch(IpxDevice, SwitchEntity):
    """Representation of a IPX Virtual Out."""

    def __init__(
        self,
        device_config: dict,
        ipx: IPX800,
        coordinator: DataUpdateCoordinator,
    ):
        """Initialize the VirtualOutSwitch."""
        super().__init__(device_config, ipx, coordinator)
        self.control = VOutput(ipx, self._id)

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return self.coordinator.data[f"VO{self._id}"] == 1

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        self.control.on()

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        self.control.off()

    def toggle(self, **kwargs):
        """Toggle the switch."""
        self.control.toggle()


class VirtualInSwitch(IpxDevice, SwitchEntity):
    """Representation of a IPX Virtual In."""

    def __init__(
        self,
        device_config: dict,
        ipx: IPX800,
        coordinator: DataUpdateCoordinator,
    ):
        """Initialize the VirtualInSwitch."""
        super().__init__(device_config, ipx, coordinator)
        self.control = VInput(ipx, self._id)

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return self.coordinator.data[f"VI{self._id}"] == 1

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        self.control.on()

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        self.control.off()

    def toggle(self, **kwargs):
        """Toggle the switch."""
        self.control.toggle()
