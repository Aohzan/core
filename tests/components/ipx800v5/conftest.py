"""Fixtures for IPX800V5 integration tests."""
from __future__ import annotations

from collections.abc import Generator
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.ipx800v5.const import DOMAIN
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture

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
def mock_ipx800v5() -> MagicMock:
    """Mock a successful IPX800."""
    with patch(
        "homeassistant.components.ipx800v5.config_flow.IPX800",
    ) as service_mock:
        ipx = service_mock.return_value
        ipx.ping = AsyncMock(return_value=None)
        ipx.init_config = AsyncMock(return_value=None)
        ipx.get_ipx_info = AsyncMock(
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


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="IPX800 V5",
        domain=DOMAIN,
        data=USER_INPUT,
        unique_id="IPX800V5",
    )


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.ipx800v5.async_setup_entry", return_value=True
    ) as setup_mock:
        yield setup_mock


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_ipx800v5: MagicMock
) -> MockConfigEntry:
    """Set up the IPX800v5 integration for testing."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry
