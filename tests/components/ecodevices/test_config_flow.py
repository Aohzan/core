"""Test the GCE Eco-Devices config flow."""

from unittest.mock import MagicMock, patch

import aiohttp
from bluemaestro_ble import SensorDeviceClass

from homeassistant import config_entries, data_entry_flow
from homeassistant.components.ecodevices import config_flow
from homeassistant.components.ecodevices.const import (
    CONF_C1_DEVICE_CLASS,
    CONF_C1_DIVIDER_FACTOR,
    CONF_C1_ENABLED,
    CONF_C1_TOTAL_UNIT_OF_MEASUREMENT,
    CONF_C1_UNIT_OF_MEASUREMENT,
    CONF_C2_ENABLED,
    CONF_T1_ENABLED,
    CONF_T1_TYPE,
    CONF_T2_ENABLED,
    CONF_TI_TYPE_HCHP,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, UnitOfVolume
from homeassistant.core import HomeAssistant

from tests.test_util.aiohttp import AiohttpClientMocker

FIXTURE_USER_INPUT = {
    CONF_HOST: "127.0.0.1",
    CONF_PORT: 80,
    CONF_T1_ENABLED: True,
    CONF_C1_ENABLED: True,
}


async def test_show_authenticate_form(hass: HomeAssistant) -> None:
    """Test that the setup form is served."""
    flow = config_flow.EcoDevicesConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user(user_input=None)

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"


async def test_complete_form_user(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.ecodevices.config_flow.EcoDevices.get_info",
            return_value=MagicMock(),
        ),
        patch(
            "homeassistant.components.ecodevices.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )
    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "params"

    with (
        patch(
            "homeassistant.components.ecodevices.config_flow.EcoDevices.get_info",
            return_value=MagicMock(),
        ),
        patch(
            "homeassistant.components.ecodevices.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
    assert result3["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result3["step_id"] == "params"

    with (
        patch(
            "homeassistant.components.ecodevices.config_flow.EcoDevices.get_info",
            return_value=MagicMock(),
        ),
        patch(
            "homeassistant.components.ecodevices.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_T1_TYPE: CONF_TI_TYPE_HCHP,
                CONF_C1_DEVICE_CLASS: SensorDeviceClass.GAS,
                CONF_C1_UNIT_OF_MEASUREMENT: UnitOfVolume.CUBIC_METERS,
                CONF_C1_DIVIDER_FACTOR: 1,
                CONF_C1_TOTAL_UNIT_OF_MEASUREMENT: UnitOfVolume.CUBIC_METERS,
            },
        )

    assert result4["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result4["title"] == "Eco-Devices 127.0.0.1:80"
    assert result4["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_PORT: 80,
        CONF_C1_ENABLED: True,
        CONF_C2_ENABLED: False,
        CONF_T1_ENABLED: True,
        CONF_T2_ENABLED: False,
        CONF_T1_TYPE: CONF_TI_TYPE_HCHP,
        CONF_SCAN_INTERVAL: 5,
        CONF_C1_DEVICE_CLASS: SensorDeviceClass.GAS,
        CONF_C1_UNIT_OF_MEASUREMENT: UnitOfVolume.CUBIC_METERS,
        CONF_C1_DIVIDER_FACTOR: 1,
        CONF_C1_TOTAL_UNIT_OF_MEASUREMENT: UnitOfVolume.CUBIC_METERS,
    }

    assert len(mock_setup_entry.mock_calls) == 1


async def test_connection_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test we show user form on EcoDevices Home connection error."""
    aioclient_mock.get(
        f"http://{FIXTURE_USER_INPUT[CONF_HOST]}"
        f":{FIXTURE_USER_INPUT[CONF_PORT]}/status.xml",
        exc=aiohttp.ClientError,
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_USER_INPUT,
    )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}
