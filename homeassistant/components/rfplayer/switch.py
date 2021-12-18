"""Support for Rfplayer switch."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_DEVICES, CONF_PROTOCOL, STATE_ON
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import DATA_DEVICE_REGISTER, EVENT_KEY_COMMAND, RfplayerDevice
from .const import (
    CONF_AUTOMATIC_ADD,
    CONF_DEVICE_ADDRESS,
    CONF_DEVICE_ID,
    DOMAIN,
    RFPLAYER_PROTOCOL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Rfplayer platform."""
    config = entry.data
    options = entry.options

    async def add_new_device(event):
        """Check if device is known, otherwise create device entity."""
        # create entity
        device = RfplayerSwitch(
            protocol=event[CONF_PROTOCOL],
            device_address=event.get(CONF_DEVICE_ADDRESS),
            device_id=event.get(CONF_DEVICE_ID),
            initial_event=event,
        )
        _LOGGER.debug("Add switch entity %s", event)
        async_add_entities([device])

    if CONF_DEVICES in config:
        for device_id, event in config[CONF_DEVICES].items():
            if EVENT_KEY_COMMAND in event:
                await add_new_device(event)

    if options.get(CONF_AUTOMATIC_ADD, config[CONF_AUTOMATIC_ADD]):
        hass.data[DATA_DEVICE_REGISTER][EVENT_KEY_COMMAND] = add_new_device


class RfplayerSwitch(RfplayerDevice, SwitchEntity):
    """Representation of a Rfplayer sensor."""

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    async def async_added_to_hass(self):
        """Restore RFLink device state (ON/OFF)."""
        await super().async_added_to_hass()

        if self._event is None:
            old_state = await self.async_get_last_state()
            if old_state is not None:
                self._state = old_state.state == STATE_ON

    @callback
    def _handle_event(self, event):
        command = event["command"]
        if command in ["ON", "ALLON"]:
            self._state = True
        elif command in ["OFF", "ALLOFF"]:
            self._state = False

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        await self._async_send_command("ON")
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        await self._async_send_command("OFF")
        self._state = False
        self.async_write_ha_state()
