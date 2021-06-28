"""Support for the Flood sensors."""
import logging

from .const import CONTROLLER, COORDINATOR, DOMAIN
from .entity import FloodEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Flood platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    cont = data[CONTROLLER]
    cdnt = data[COORDINATOR]

    entities = [
        FloodSpeedEntity(
            cont,
            cdnt,
            "Current Download",
            "history",
            "downloadSpeed",
            "mdi:download",
        ),
        FloodSpeedEntity(
            cont,
            cdnt,
            "Current Upload",
            "history",
            "uploadSpeed",
            "mdi:upload",
        ),
        FloodEntity(
            cont,
            cdnt,
            "Last notification",
            "last_notification",
            "title",
            "mdi:comment-outline",
            attributes=["type", "torrent"],
        ),
        FloodEntity(
            cont,
            cdnt,
            "Torrents",
            "torrents",
            "count",
            "mdi:file",
        ),
    ]

    async_add_entities(entities, True)


class FloodSpeedEntity(FloodEntity):
    """Representation of a Flood sensor."""

    @property
    def unit_of_measurement(self) -> str:
        """Return the icon to use in the frontend."""
        return "kB/s"

    @property
    def state(self) -> int:
        """Return the state."""
        byte_value = float(self.coordinator.data.get(self._category, {}).get(self._key))
        return int(byte_value / 1024)

    @property
    def state_attributes(self):
        """Return the state attributes."""
        if self._attributes and self.coordinator.data.get(self._category, {}):
            attributes = {}
            for attribute in self._attributes:
                attributes.update(
                    {
                        attribute: self.coordinator.data.get(self._category, {}).get(
                            attribute
                        )
                    }
                )
            return attributes
