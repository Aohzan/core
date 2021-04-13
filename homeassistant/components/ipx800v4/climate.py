"""Support for IPX800 V4 climates."""
import logging

from pypx800 import IPX800, X4FP, Relay

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_PRESET_MODE,
)
from homeassistant.const import TEMP_CELSIUS
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
    TYPE_X4FP,
)

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = GLOBAL_PARALLEL_UPDATES


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """Set up the IPX800 climates."""
    controller = hass.data[DOMAIN][config_entry.entry_id][CONTROLLER]
    devices = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICES]
    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    entities = []

    for device in devices:
        if device.get(CONF_TYPE) == TYPE_X4FP:
            entities.append(X4FPClimate(device, controller, coordinator))
        elif device.get(CONF_TYPE) == TYPE_RELAY:
            entities.append(RelayClimate(device, controller, coordinator))

    async_add_entities(entities, True)


class X4FPClimate(IpxDevice, ClimateEntity):
    """Representation of a IPX Climate through X4FP."""

    def __init__(
        self,
        device_config: dict,
        ipx: IPX800,
        coordinator: DataUpdateCoordinator,
    ):
        """Initialize the X4FPClimate."""
        super().__init__(device_config, ipx, coordinator)
        self.control = X4FP(ipx, self._ext_id, self._id)

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_PRESET_MODE

    @property
    def temperature_unit(self):
        """Return Celsius indifferently since there is no temperature support."""
        return TEMP_CELSIUS

    @property
    def hvac_modes(self):
        """Return modes."""
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    @property
    def hvac_mode(self):
        """Return current mode if heating or not."""
        if self.coordinator.data[f"FP{self._ext_id} Zone {self._id}"] == "Arret":
            return HVAC_MODE_OFF
        return HVAC_MODE_HEAT

    @property
    def hvac_action(self):
        """Return current action if heating or not."""
        if self.coordinator.data[f"FP{self._ext_id} Zone {self._id}"] == "Arret":
            return CURRENT_HVAC_OFF
        return CURRENT_HVAC_HEAT

    @property
    def preset_modes(self):
        """Return all preset modes."""
        return ["Comfort", "Eco", "Hors Gel", "Arret", "Comfort -1", "Comfort -2"]

    @property
    def preset_mode(self):
        """Return current preset mode."""
        return self.coordinator.data.get(f"FP{self._ext_id} Zone {self._id}")

    def set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        switcher = {
            "Comfort": 0,
            "Eco": 1,
            "Hors Gel": 2,
            "Arret": 3,
            "Comfort -1": 4,
            "Comfort -2": 5,
        }
        _LOGGER.debug(
            "set preset_mode to %s => id %s", preset_mode, switcher.get(preset_mode)
        )
        self.control.set_mode(switcher.get(preset_mode))

    def set_hvac_mode(self, hvac_mode):
        """Set hvac mode."""
        if hvac_mode == HVAC_MODE_HEAT:
            self.control.set_mode(0)
        elif hvac_mode == HVAC_MODE_OFF:
            self.control.set_mode(3)
        else:
            _LOGGER.error("Unrecognized hvac mode: %s", hvac_mode)
            return


class RelayClimate(IpxDevice, ClimateEntity):
    """Representation of a IPX Climate through 2 relais."""

    def __init__(
        self,
        device_config: dict,
        ipx: IPX800,
        coordinator: DataUpdateCoordinator,
    ):
        """Initialize the RelayClimate."""
        super().__init__(device_config, ipx, coordinator)
        self.control_minus = Relay(ipx, self._ids[0])
        self.control_plus = Relay(ipx, self._ids[1])

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_PRESET_MODE

    @property
    def temperature_unit(self):
        """Return Celsius indifferently since there is no temperature support."""
        return TEMP_CELSIUS

    @property
    def hvac_modes(self):
        """Return modes."""
        return [HVAC_MODE_HEAT, HVAC_MODE_OFF]

    @property
    def hvac_mode(self):
        """Return current mode if heating or not."""
        if (
            int(self.coordinator.data[f"R{self._ids[0]}"]) == 0
            and int(self.coordinator.data[f"R{self._ids[1]}"]) == 1
        ):
            return HVAC_MODE_OFF
        return HVAC_MODE_HEAT

    @property
    def hvac_action(self):
        """Return current action if heating or not."""
        if (
            int(self.coordinator.data[f"R{self._ids[0]}"]) == 0
            and int(self.coordinator.data[f"R{self._ids[1]}"]) == 1
        ):
            return CURRENT_HVAC_OFF
        return CURRENT_HVAC_HEAT

    @property
    def preset_modes(self):
        """Return all preset modes."""
        return ["Comfort", "Eco", "Hors Gel", "Stop"]

    @property
    def preset_mode(self):
        """Return current preset mode from 2 relay states."""
        state_minus = int(self.coordinator.data[f"R{self._ids[0]}"])
        state_plus = int(self.coordinator.data[f"R{self._ids[1]}"])
        switcher = {
            (0, 0): "Comfort",
            (0, 1): "Stop",
            (1, 0): "Hors Gel",
            (1, 1): "Eco",
        }
        return switcher.get((state_minus, state_plus), "Inconnu")

    def set_hvac_mode(self, hvac_mode):
        """Set hvac mode."""
        if hvac_mode == HVAC_MODE_HEAT:
            self.control_minus.off()
            self.control_plus.off()
        elif hvac_mode == HVAC_MODE_OFF:
            self.control_minus.off()
            self.control_plus.on()
        else:
            _LOGGER.error("Unrecognized hvac mode: %s", hvac_mode)
            return

    def set_preset_mode(self, preset_mode):
        """Set new target preset mode."""
        if preset_mode == "Comfort":
            self.control_minus.off()
            self.control_plus.off()
        elif preset_mode == "Eco":
            self.control_minus.on()
            self.control_plus.on()
        elif preset_mode == "Hors Gel":
            self.control_minus.on()
            self.control_plus.off()
        else:
            self.control_minus.off()
            self.control_plus.on()
