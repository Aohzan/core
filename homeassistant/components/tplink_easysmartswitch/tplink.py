"""Query the TP-Link switch"""
import re
import requests
from bs4 import BeautifulSoup
import asyncio
import socket

import async_timeout

import aiohttp
from .const import (
    TPLINK_PORT_LINK_STATUS,
    TPLINK_PORT_RX_BAD_PKT,
    TPLINK_PORT_RX_GOOD_PKT,
    TPLINK_PORT_STATE,
    TPLINK_PORT_TX_BAD_PKT,
    TPLINK_PORT_TX_GOOD_PKT,
    TPLINK_STATE,
    TPLINK_STATUS,
)


class EasySwitch:
    """Get information from a TP-Link Easy Smart Switch"""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        request_timeout: int = 10,
        session: aiohttp.client.ClientSession = None,
    ) -> None:
        self._host = host
        self._mac_address = "temporary"
        self._port_number = 0
        self._url = f"http://{host}"
        self._user = user
        self._password = password

        self._request_timeout = request_timeout
        self._session = session
        self._close_session = False

    @property
    def host(self) -> str:
        """Switch's host."""
        return self._host

    @property
    def mac_address(self) -> str:
        """Switch's mac address."""
        return self._mac_address

    @property
    def version(self) -> str:
        """Switch's firmware version."""
        return "1.0"

    @property
    def port_number(self) -> int:
        """Switch's ports number."""
        return self._port_number

    async def login(self) -> bool:
        """Log on the switch."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._close_session = True

        data = {"logon": "Login", "username": self._user, "password": self._password}
        headers = {"Referer": f"{self._url}/Logout.htm"}

        try:
            with async_timeout.timeout(self._request_timeout):
                response = await self._session.post(
                    f"{self._url}/logon.cgi",
                    data=data,
                    headers=headers,
                    timeout=self._request_timeout,
                )
        except asyncio.TimeoutError as exception:
            raise TpLinkSwitchCannotConnectError("Timeout error") from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise TpLinkSwitchCannotConnectError(exception) from exception

        # if response.status == 401:
        #     raise TpLinkSwitchInvalidAuthError("Authentication failed")

        return True

    async def get_data(self) -> dict:
        """Get all port informations."""
        headers = {
            "Referer": f"{self._url}/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
        }
        request = await self._session.get(
            f"{self._url}/PortStatisticsRpm.htm",
            headers=headers,
            timeout=self._request_timeout,
        )
        soup = BeautifulSoup(await request.text(), "html.parser")

        convoluted = soup.script == soup.head.script

        if request.status != 200:
            raise TpLinkSwitchInvalidAuthError("Authentication failed")

        pattern = re.compile(r"var (max_port_num) = (.*?);$", re.MULTILINE)

        if convoluted:
            port_number = int(
                pattern.search(str(soup.head.find_all("script"))).group(2)
            )
        else:
            port_number = int(pattern.search(str(soup.script)).group(2))
        self._port_number = port_number

        if convoluted:
            i1 = (
                re.compile(r'tmp_info = "(.*?)";$', re.MULTILINE | re.DOTALL)
                .search(str(soup.body.script))
                .group(1)
            )
            i2 = (
                re.compile(r'tmp_info2 = "(.*?)";$', re.MULTILINE | re.DOTALL)
                .search(str(soup.body.script))
                .group(1)
            )
            # We simulate bug for bug the way the variables are loaded on the "normal" switch models. In those, each
            # data array has two extra 0 cells at the end. To remain compatible with the balance of the code here,
            # we need to add in these redundant entries so they can be removed later. (smh)
            script_vars = (
                "tmp_info:[" + i1.rstrip() + " " + i2.rstrip() + ",0,0]"
            ).replace(" ", ",")
        else:
            script_vars = (
                re.compile(r"var all_info = {\n?(.*?)\n?};$", re.MULTILINE | re.DOTALL)
                .search(str(soup.script))
                .group(1)
            )

        entries = re.split(",?\n+", script_vars)

        edict = {}
        drop2 = re.compile(r"\[(.*),0,0]")
        for entry in entries:
            e2 = re.split(":", entry)
            edict[str(e2[0])] = drop2.search(e2[1]).group(1)

        if convoluted:
            e3 = {}
            e4 = {}
            e5 = {}
            ee = re.split(",", edict["tmp_info"])
            for port in range(0, port_number):
                e3[port] = ee[(port * 6)]
                e4[port] = ee[(port * 6) + 1]
                e5[(port * 4)] = ee[(port * 6) + 2]
                e5[(port * 4) + 1] = ee[(port * 6) + 3]
                e5[(port * 4) + 2] = ee[(port * 6) + 4]
                e5[(port * 4) + 3] = ee[(port * 6) + 5]
        else:
            e3 = re.split(",", edict["state"])
            e4 = re.split(",", edict["link_status"])
            e5 = re.split(",", edict["pkts"])

        ports = {}
        for port in range(1, port_number + 1):
            ports[port] = {
                TPLINK_PORT_STATE: TPLINK_STATE[e3[port - 1]],
                TPLINK_PORT_LINK_STATUS: TPLINK_STATUS[e4[port - 1]],
                TPLINK_PORT_TX_GOOD_PKT: e5[((port - 1) * 4)],
                TPLINK_PORT_TX_BAD_PKT: e5[((port - 1) * 4) + 1],
                TPLINK_PORT_RX_GOOD_PKT: e5[((port - 1) * 4) + 2],
                TPLINK_PORT_RX_BAD_PKT: e5[((port - 1) * 4) + 3],
            }
        return ports

    async def close(self) -> None:
        """Close open client session."""
        if self._session and self._close_session:
            await self._session.close()

    async def __aenter__(self):
        """Async enter."""
        return self

    async def __aexit__(self, *_exc_info) -> None:
        """Async exit."""
        await self.close()


class TpLinkSwitchCannotConnectError(Exception):
    """Exception to indicate an error in connection."""


class TpLinkSwitchInvalidAuthError(Exception):
    """Exception to indicate an error in authentication."""
