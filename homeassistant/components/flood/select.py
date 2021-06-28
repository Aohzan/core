"""Support for the Flood select"""

from homeassistant.components.select import SelectEntity

from .const import CONTROLLER, COORDINATOR, DOMAIN
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
        ),
        FloodSpeedLimitEntity(
            cont,
            cdnt,
            "Upload Limit",
            "client_settings",
            "throttleGlobalUpSpeed",
            "mdi:upload-lock",
        ),
    ]

    async_add_entities(entities, True)


class FloodSpeedLimitEntity(FloodEntity, SelectEntity):
    """Representation of a Flood speed limit entity."""

    @property
    def unit_of_measurement(self) -> str:
        """Return the icon to use in the frontend."""
        return "kB/s"

    @property
    def current_option(self) -> int:
        """Return the state."""
        byte_value = float(self.coordinator.data.get(self._category, {}).get(self._key))
        return int(byte_value / 1024)

    @property
    def options(self) -> list:
        return self.coordinator.data.get("test")

    async def async_select_option(self, option: str) -> None:
        """Update the current value."""
        speed = int(option)
        if self._key == "throttleGlobalDownSpeed":
            await self._controller.set_download_limit(speed)
        elif self._key == "throttleGlobalUpSpeed":
            await self._controller.set_upload_limit(speed)
