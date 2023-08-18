"""Tests for the IPX800V5 config flow."""
import json
from unittest.mock import AsyncMock, Mock, patch

from pypx800v5 import EXT_X8R
import pytest

from homeassistant import data_entry_flow
from homeassistant.components.ipx800v5.const import (
    CONF_COMPONENT,
    CONF_EXT_TYPE,
    CONF_IO_NUMBER,
    DEFAULT_IPX_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant

from tests.common import load_fixture

USER_INPUT = {
    CONF_HOST: "192.168.1.123",
    CONF_PORT: 80,
    CONF_API_KEY: "apikey",
}
PARAM_INPUT = {
    "scan_interval": 15,
    "api_key": "apikey",
    "push_password": "password",
    "ipx_0_1": "light",
    "ipx_0_2": "switch",
    "ipx_0_3": "switch",
    "ipx_0_4": "switch",
    "ipx_0_5": "switch",
    "ipx_0_6": "switch",
    "ipx_0_7": "switch",
    "ipx_0_8": "switch",
    "x8r_0_1": "light",
    "x8r_0_2": "switch",
    "x8r_0_3": "switch",
    "x8r_0_4": "switch",
    "x8r_0_5": "switch",
    "x8r_0_6": "switch",
    "x8r_0_7": "switch",
    "x8r_0_8": "switch",
}


@pytest.fixture
def mock_ipx800():
    """Mock a successful IPX800."""
    with patch(
        "homeassistant.components.ipx800v5.config_flow.IPX800",
    ) as service_mock:
        ipx = service_mock.return_value
        ipx.ping = AsyncMock(return_value=True)
        ipx.init_config = AsyncMock(return_value=True)
        ipx.ipx_info = AsyncMock(
            return_value=json.loads(load_fixture("ipx800v5/ipx_info.json"))
        )
        ipx.global_get = AsyncMock(
            return_value=json.loads(load_fixture("ipx800v5/global_get.json"))
        )
        ipx.ipx_config = json.loads(load_fixture("ipx800v5/ipx_config.json"))
        ipx.extensions_config = json.loads(
            load_fixture("ipx800v5/extensions_config.json")
        )
        ipx.objects_config = json.loads(load_fixture("ipx800v5/objects_config.json"))
        yield service_mock


async def test_user(hass: HomeAssistant, mock_ipx800: Mock) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "params"
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], PARAM_INPUT
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == USER_INPUT[CONF_HOST]

    assert result["data"][CONF_NAME] == DEFAULT_IPX_NAME
    assert result["data"][CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL

    # Devices
    devices = result["data"]["devices"]
    device_ipx_relay_1 = [
        d for d in devices if d[CONF_EXT_TYPE] == "ipx" and d[CONF_IO_NUMBER] == 1
    ][0]
    assert device_ipx_relay_1[CONF_COMPONENT] == "light"
    assert device_ipx_relay_1[CONF_NAME] == "IPX N°0 Relais 1"
    device_ipx_relay_2 = [
        d for d in devices if d[CONF_EXT_TYPE] == "ipx" and d[CONF_IO_NUMBER] == 2
    ][0]
    assert device_ipx_relay_2[CONF_COMPONENT] == "switch"
    assert device_ipx_relay_2[CONF_NAME] == "IPX N°0 Relais 2"

    device_x8r_relay_1 = [
        d for d in devices if d[CONF_EXT_TYPE] == EXT_X8R and d[CONF_IO_NUMBER] == 1
    ][0]
    assert device_x8r_relay_1[CONF_COMPONENT] == "light"
    assert device_x8r_relay_1[CONF_NAME] == "X8R N°0 Relais 1"
    device_x8r_relay_2 = [
        d for d in devices if d[CONF_EXT_TYPE] == EXT_X8R and d[CONF_IO_NUMBER] == 2
    ][0]
    assert device_x8r_relay_2[CONF_COMPONENT] == "switch"
    assert device_x8r_relay_2[CONF_NAME] == "X8R N°0 Relais 2"
