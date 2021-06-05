"""Support for the Flood."""
import logging

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONTROLLER, COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Flood platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    controller = data[CONTROLLER]
    coordinator = data[COORDINATOR]

    entities = []

    entities.append(FloodEntity(controller, coordinator))

    if entities:
        async_add_entities(entities, True)


class FloodEntity(CoordinatorEntity):
    """Representation of a Flood sensor."""

    def __init__(self, controller, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.controller = controller

    @property
    def device_info(self):
        """Return device information identifier."""
        return {
            "identifiers": {(DOMAIN, self.controller.host)},
            "via_device": (DOMAIN, self.controller.host),
        }

    @property
    def unique_id(self):
        """Return an unique id."""
        return "_".join(
            [
                DOMAIN,
                self.controller.host,
                "sensor",
                "flood",
            ]
        )

    @property
    def name(self):
        """Return the name."""
        return "Flood"

    @property
    def state(self):
        """Return the state."""
        return 1

    @property
    def state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data:
            return {
                "throttleGlobalDownSpeed": self.coordinator.data.get(
                    "throttleGlobalDownSpeed"
                ),
                "throttleGlobalUpSpeed": self.coordinator.data.get(
                    "throttleGlobalUpSpeed"
                ),
            }
