"""Test the GCE IPX800 V4 config flow."""
from homeassistant import config_entries, data_entry_flow
from homeassistant.components.ipx800v4.const import DOMAIN
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
)

FIXTURE_USER_INPUT = {
    CONF_NAME: "My IPX800",
    CONF_HOST: "127.0.0.1",
    CONF_PORT: 80,
    CONF_API_KEY: "abcdefghijklmnopqrstuvwxyz",
    CONF_SCAN_INTERVAL: 20,
}


async def test_config_flow_user(hass):
    """Test user initiated flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result2["reason"] == "yaml_only"


async def test_import(hass):
    """Test yaml configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=FIXTURE_USER_INPUT,
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "My IPX800"
