"""Constants for the Prix Carburant integration."""
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "prix_carburant"
PLATFORMS: Final = [Platform.SENSOR]

DEFAULT_NAME: Final = "Prix Carburant"

ATTR_ADDRESS = "address"
ATTR_POSTAL_CODE = "postal_code"
ATTR_CITY = "city"
ATTR_FUELS = "fuels"
ATTR_PRICE = "price"
CONF_STATIONS = "stations"
CONF_MAX_KM = "max_km"

ATTR_GASOIL = "Gasoil"
ATTR_E95 = "E95"
ATTR_E98 = "E98"
ATTR_E10 = "E10"
ATTR_GPL = "GPLc"
ATTR_E85 = "E85"
CARBURANTS = [ATTR_E10, ATTR_E85, ATTR_E95, ATTR_E98, ATTR_GASOIL, ATTR_GPL]
