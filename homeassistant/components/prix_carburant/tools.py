"""Tools for Prix Carburant."""
import csv
import urllib.request
import zipfile

import xmltodict

from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, ATTR_NAME

from .const import ATTR_ADDRESS, ATTR_CARBURANTS, ATTR_CITY, ATTR_POSTAL_CODE

STATIONS_DATA_URL = "https://static.data.gouv.fr/resources/prix-des-carburants-en-france/20181117-111538/active-stations.csv"
STATIONS_TARIFS_URL = "https://donnees.roulez-eco.fr/opendata/instantane"


class PrixCarburantTool:
    """Prix Carburant class with stations information"""

    def __init__(self, executor):
        """Init tool."""
        self._executor = executor
        self._stations_information = {}
        self._stations_data = {}

    @property
    def stations(self) -> dict:
        """Return stations information."""
        return self._stations_data

    async def load(self) -> None:
        """Load first information."""
        self._stations_information = await self._get_stations_information()
        await self.update()

    async def update(self) -> None:
        """Update tarifs."""
        if self._stations_information == {}:
            raise Exception("call load() first")
        station_tarifs = await self._get_stations_tarifs()
        # get station name
        for station_id in station_tarifs:
            if station_id in self._stations_data:
                station_tarifs[station_id]["nom"] = self._stations_data[station_id][
                    "nom"
                ]

    async def _get_stations_information(self) -> None:
        filehandle, _ = await self._executor(
            urllib.request.urlretrieve, STATIONS_DATA_URL
        )
        stations_data = {}

        with open(filehandle, newline="", encoding="UTF-8") as file:
            spamreader = csv.reader(file, delimiter=",", quotechar='"')
            for row in spamreader:
                stations_data.update({row[0]: {ATTR_NAME: row[1]}})

        self._stations_information = stations_data

    async def _get_stations_tarifs(self) -> None:
        """Return data from all stations"""
        filehandle, _ = await self._executor(
            urllib.request.urlretrieve(STATIONS_TARIFS_URL)
        )
        zip_file_object = zipfile.ZipFile(filehandle, "r")
        first_file = zip_file_object.namelist()[0]
        file = zip_file_object.open(first_file)
        xml_content = file.read()
        raw_content = xmltodict.parse(xml_content)
        stations_data = {}
        for station in raw_content["pdv_liste"]["pdv"]:
            stations_data.update(
                {
                    station["@id"]: {
                        ATTR_LATITUDE: station["@latitude"],
                        ATTR_LONGITUDE: station["@longitude"],
                        ATTR_ADDRESS: station["adresse"],
                        ATTR_POSTAL_CODE: station["@cp"],
                        ATTR_CITY: station["ville"],
                        ATTR_NAME: None,
                        ATTR_CARBURANTS: {},
                    }
                }
            )
            for carburant in station["prix"]:
                stations_data[station["@id"]][ATTR_CARBURANTS].update(
                    {
                        carburant["@nom"]: {
                            "date": carburant["@maj"],
                            "prix": carburant["@valeur"],
                        }
                    }
                )
        self._stations_data = stations_data
