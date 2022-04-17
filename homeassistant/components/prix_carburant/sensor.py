"""Prix Carburant sensor platform."""
from datetime import timedelta
import logging

from prixCarburantClient.prixCarburantClient import PrixCarburantClient
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorDeviceClass
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CURRENCY_EURO
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

DOMAIN = "prix_carburant"

ATTR_ID = "Station ID"
ATTR_GASOIL = "Gasoil"
ATTR_E95 = "E95"
ATTR_E98 = "E98"
ATTR_E10 = "E10"
ATTR_GPL = "GPLc"
ATTR_E85 = "E85"
ATTR_GASOIL_LAST_UPDATE = "Last Update Gasoil"
ATTR_E95_LAST_UPDATE = "Last Update E95"
ATTR_E98_LAST_UPDATE = "Last Update E98"
ATTR_E10_LAST_UPDATE = "Last Update E10"
ATTR_GPL_LAST_UPDATE = "Last Update GPLc"
ATTR_E85_LAST_UPDATE = "Last Update E85"
ATTR_ADDRESS = "Station Address"
ATTR_NAME = "Station name"
ATTR_LAST_UPDATE = "Last update"

CONF_MAX_KM = "maxDistance"
CONF_STATION_ID = "stationID"
CARBURANTS = [ATTR_E10, ATTR_E85, ATTR_E95, ATTR_E98, ATTR_GASOIL, ATTR_GPL]

SCAN_INTERVAL = timedelta(seconds=3600)


# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_MAX_KM, default=10): cv.positive_int,
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_STATION_ID, default=[]): cv.ensure_list,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    max_distance = config.get(CONF_MAX_KM)
    station_ids = config.get(CONF_STATION_ID)

    location = [{"lat": str(latitude), "lng": str(longitude)}]

    client = PrixCarburantClient(location, max_distance)
    client.load()

    if not station_ids:
        logging.info("No station list, find nearest station")
        stations = client.foundNearestStation()
    else:
        logging.info("Precessing station list")
        stations = []
        for station in station_ids:
            stations.append(str(station))
            logging.info("- %s", str(station))
        stations = client.extractSpecificStation(stations)

    logging.info("%s stations found", str(len(stations)))
    client.clean()
    for station in stations:
        for carburant in CARBURANTS:
            add_devices([PrixCarburant(stations.get(station), client, carburant)])


class PrixCarburant(Entity):
    """Representation of a Sensor."""

    def __init__(self, station, client, carburant):
        """Initialize the sensor."""
        self.client = client
        self.station = station
        self.carburant = carburant

        self._last_update = None

        self._attr_icon = "mdi:gas-station"
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_unique_id = "_".join([DOMAIN, self.station.id, self.carburant])
        self._attr_unit_of_measurement = CURRENCY_EURO
        if self.station.name and self.station.name != "undefined":
            self._attr_name = f"Station {self.station.name} - {self.carburant}"
        else:
            self._attr_name = f"Station {self.station.id} - {self.carburant}"

        self.update()

    @property
    def extra_attr_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ADDRESS: self.station.adress,
            ATTR_NAME: self.station.name,
        }

    @Throttle(SCAN_INTERVAL)
    def update(self):
        """Fetch new state data."""

        self.client.reloadIfNecessary()
        if self.client.lastUpdate == self._last_update:
            logging.debug("%s already updated", self.station.id)
        else:
            logging.debug("%s needs update", self.station.id)
            station = self.client.extractSpecificStation([str(self.station.id)])
            self.station = station.get(self.station.id)
            self._last_update = self.client.lastUpdate

        if self.carburant == ATTR_GASOIL:
            self._attr_state = self.station.gazoil["valeur"]
        elif self.carburant == ATTR_E10:
            self._attr_state = self.station.e10["valeur"]
        elif self.carburant == ATTR_E85:
            self._attr_state = self.station.e85["valeur"]
        elif self.carburant == ATTR_E95:
            self._attr_state = self.station.e95["valeur"]
        elif self.carburant == ATTR_E98:
            self._attr_state = self.station.e98["valeur"]
        elif self.carburant == ATTR_GPL:
            self._attr_state = self.station.gpl["valeur"]
        self.client.clean()
