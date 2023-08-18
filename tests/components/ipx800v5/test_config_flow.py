"""Tests for the IPX800V5 config flow."""
from unittest.mock import Mock

from pypx800v5 import EXT_X8R

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
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant

from .conftest import PARAM_INPUT, USER_INPUT


async def test_user(hass: HomeAssistant, mock_ipx800v5: Mock) -> None:
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
