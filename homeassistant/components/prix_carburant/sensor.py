"""Prix Carburant sensor platform."""
from __future__ import annotations

from datetime import timedelta
import logging

from prixCarburantClient.prixCarburantClient import PrixCarburantClient
import voluptuous as vol

<<<<<<< HEAD
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

=======
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import ATTR_NAME, CONF_LATITUDE, CONF_LONGITUDE, CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    ATTR_ADDRESS,
    ATTR_CITY,
    ATTR_FUELS,
    ATTR_POSTAL_CODE,
    ATTR_PRICE,
    CARBURANTS,
    CONF_MAX_KM,
    CONF_STATIONS,
    DOMAIN,
)
from .tools import PrixCarburantTool

_LOGGER = logging.getLogger(__name__)
>>>>>>> 20be55e452 (fix bug)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_MAX_KM, default=10): cv.positive_int,
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_STATION_ID, default=[]): cv.ensure_list,
    }
)


<<<<<<< HEAD
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    max_distance = config.get(CONF_MAX_KM)
    station_ids = config.get(CONF_STATION_ID)

    location = [{"lat": str(latitude), "lng": str(longitude)}]

    client = PrixCarburantClient(location, max_distance)
    client.load()
=======
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Prix Carburant sensor."""
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the platform from config_entry."""
    config = entry.data
    # latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    # longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    # max_distance = config.get(CONF_MAX_KM)
    config_stations_ids = [str(s) for s in config.get(CONF_STATIONS, [])]

    tool = await hass.async_add_executor_job(PrixCarburantTool)

    async def async_update_data():
        """Fetch data from API."""
        await hass.async_add_executor_job(tool.update)
        return tool.stations

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=120),
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    # user_stations_ids from location
    # location = [{"lat": str(latitude), "lng": str(longitude)}]
>>>>>>> 20be55e452 (fix bug)

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

<<<<<<< HEAD
    logging.info("%s stations found", str(len(stations)))
    client.clean()
    for station in stations:
        for carburant in CARBURANTS:
            add_devices([PrixCarburant(stations.get(station), client, carburant)])
=======
    # if not station_ids:
    #     _LOGGER.info("No station list, find nearest station")
    #     stations = client.foundNearestStation()
    # else:
    #     logging.info("Precessing station list")
    #     _LOGGER = client.extractSpecificStation(station_ids)

    user_stations_ids = [s for s in tool.stations if s in config_stations_ids]
    _LOGGER.info("%s stations found", str(len(user_stations_ids)))
    entities = []
    for station_id in user_stations_ids:
        for carburant in CARBURANTS:
            if carburant in tool.stations[station_id][ATTR_FUELS]:
                entities.append(
                    PrixCarburant(
                        station_id, tool.stations[station_id], carburant, coordinator
                    )
                )

    async_add_entities(entities, True)
>>>>>>> 20be55e452 (fix bug)


class PrixCarburant(SensorEntity):
    """Representation of a Sensor."""

<<<<<<< HEAD
    def __init__(self, station, client, carburant):
        """Initialize the sensor."""
        self.client = client
        self.station = station
=======
    def __init__(self, station_id, station_info, carburant, coordinator):
        """Initialize the sensor."""
        self.station_id = station_id
        self.station_info = station_info
>>>>>>> 20be55e452 (fix bug)
        self.carburant = carburant
        self.coordinator = coordinator

        self._last_update = None

        self._attr_icon = "mdi:gas-station"
        self._attr_device_class = SensorDeviceClass.MONETARY
<<<<<<< HEAD
        self._attr_unique_id = "_".join([DOMAIN, self.station.id, self.carburant])
        self._attr_unit_of_measurement = CURRENCY_EURO
        if self.station.name and self.station.name != "undefined":
            self._attr_name = f"Station {self.station.name} - {self.carburant}"
        else:
            self._attr_name = f"Station {self.station.id} - {self.carburant}"

        self.update()
=======
        self._attr_unique_id = "_".join([DOMAIN, self.station_id, self.carburant])
        self._attr_native_unit_of_measurement = CURRENCY_EURO
        if self.station_info[ATTR_NAME] != "undefined":
            station_name = f"Station {self.station_info[ATTR_NAME]}"
        else:
            station_name = f"Station {self.station_id}"
        self._attr_name = f"{station_name} - {self.carburant}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.station_id)},
            manufacturer="Station",
            model=self.station_id,
            name=station_name,
            configuration_url="https://www.prix-carburants.gouv.fr/",
        )
>>>>>>> 20be55e452 (fix bug)

    @property
    def extra_attr_state_attributes(self):
        """Return the state attributes."""
        return {
<<<<<<< HEAD
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
=======
            ATTR_NAME: self.station_info[ATTR_NAME],
            ATTR_ADDRESS: self.station_info[ATTR_ADDRESS],
            ATTR_POSTAL_CODE: self.station_info[ATTR_POSTAL_CODE],
            ATTR_CITY: self.station_info[ATTR_CITY],
        }

    @property
    def native_value(self):
        """Return the current price."""
        if self.carburant in self.coordinator.data[self.station_id][ATTR_FUELS]:
            return self.coordinator.data[self.station_id][ATTR_FUELS][self.carburant][
                ATTR_PRICE
            ]
>>>>>>> 20be55e452 (fix bug)
