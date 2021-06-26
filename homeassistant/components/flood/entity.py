"""Support for the generic Flood entity."""
import logging

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class FloodEntity(CoordinatorEntity):
    """Representation of a Flood generic entity."""

    def __init__(
        self,
        controller,
        coordinator,
        name: str,
        category: str,
        key: str,
        icon: str = None,
        attributes: dict = None,
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self._controller = controller
        self._name = name
        self._category = category
        self._key = key
        self._icon = icon
        self._attributes = attributes

    @property
    def device_info(self):
        """Return device information identifier."""
        return {
            "identifiers": {(DOMAIN, self._controller.host)},
            "via_device": (DOMAIN, self._controller.host),
        }

    @property
    def unique_id(self):
        """Return an unique id."""
        return "_".join(
            [
                DOMAIN,
                self._controller.host,
                self._name,
            ]
        )

    @property
    def name(self):
        """Return the name."""
        return self._name

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon

    @property
    def state(self):
        """Return the state."""
        return self.coordinator.data.get(self._category, {}).get(self._key)

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
