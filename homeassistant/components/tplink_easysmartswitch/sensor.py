"""Support for the TP-Link Easy Smart Switch."""
import logging

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify
from .tplink import EasySwitch
from .const import (
    CONTROLLER,
    COORDINATOR,
    DOMAIN,
    TPLINK_PORT_LINK_STATUS,
    TPLINK_PORT_RX_BAD_PKT,
    TPLINK_PORT_RX_GOOD_PKT,
    TPLINK_PORT_STATE,
    TPLINK_PORT_TX_BAD_PKT,
    TPLINK_PORT_TX_GOOD_PKT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the TP-Link Easy Smart Switch platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    controller: EasySwitch = data[CONTROLLER]
    coordinator = data[COORDINATOR]

    entities = []
    ports_count = controller.port_number
    for port in range(ports_count):
        entities.append(
            TpLinkSwitchSensor(
                controller,
                coordinator,
                port_number=port + 1,
                attribut=TPLINK_PORT_RX_GOOD_PKT,
            )
        )
        entities.append(
            TpLinkSwitchSensor(
                controller,
                coordinator,
                port_number=port + 1,
                attribut=TPLINK_PORT_TX_GOOD_PKT,
            )
        )
    if entities:
        async_add_entities(entities)


class TpLinkSwitchSensor(CoordinatorEntity, SensorEntity):
    """Representation of a generic TP-Link Easy Smart Switch sensor."""

    def __init__(
        self,
        controller,
        coordinator,
        port_number,
        attribut,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.controller = controller
        self._port_number = port_number
        self._attribut = attribut
        self._attr_unit_of_measurement = "packets"

        self._attr_name = f"Port {port_number:02} - {attribut}"
        self._attr_unique_id = slugify(
            "_".join(
                [
                    DOMAIN,
                    self.controller.mac_address,
                    "sensor",
                    str(port_number),
                    attribut,
                ]
            )
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.controller.mac_address)},
            "via_device": (DOMAIN, self.controller.mac_address),
        }

        self._state = None

    @property
    def native_value(self):
        """Return the state."""
        return int(self.coordinator.data[self._port_number][self._attribut])
