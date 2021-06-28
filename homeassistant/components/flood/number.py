"""Support for the Flood number."""
import logging

from homeassistant.components.number import NumberEntity

from .const import CONF_MAX_SPEED_LIMIT, CONTROLLER, COORDINATOR, DOMAIN
from .entity import FloodEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Flood platform."""
    data = hass.data[DOMAIN][config_entry.entry_id]
    cont = data[CONTROLLER]
    cdnt = data[COORDINATOR]

    entities = [
        FloodSpeedLimitEntity(
            cont,
            cdnt,
            "Download Limit",
            "client_settings",
            "throttleGlobalDownSpeed",
            "mdi:download-lock",
            max_speed_limit=data.get(CONF_MAX_SPEED_LIMIT),
        ),
        FloodSpeedLimitEntity(
            cont,
            cdnt,
            "Upload Limit",
            "client_settings",
            "throttleGlobalUpSpeed",
            "mdi:upload-lock",
            max_speed_limit=data.get(CONF_MAX_SPEED_LIMIT),
        ),
    ]

    async_add_entities(entities, True)


class FloodSpeedLimitEntity(FloodEntity, NumberEntity):
    """Representation of a Flood speed limit entity."""

    @property
    def unit_of_measurement(self) -> str:
        """Return the icon to use in the frontend."""
        return "kB/s"

    @property
    def value(self) -> int:
        """Return the state."""
        byte_value = float(self.coordinator.data.get(self._category, {}).get(self._key))
        return int(byte_value / 1024)

    @property
    def step(self) -> float:
        return 5

    @property
    def max_value(self) -> int:
        """Return the max value."""
        return self._max_speed_limit

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        speed = int(value)
        if self._key == "throttleGlobalDownSpeed":
            await self._controller.set_download_limit(speed)
        elif self._key == "throttleGlobalUpSpeed":
            await self._controller.set_upload_limit(speed)
