"""Get information from Flood."""
import asyncio
import socket

import aiohttp
import async_timeout


class FloodApi:
    """Class representing the Flood and its API."""

    def __init__(
        self,
        host: str,
        port: int = 80,
        username: str = None,
        password: str = None,
        request_timeout: int = 10,
        session: aiohttp.client.ClientSession = None,
        # auth_cookie_path: str = "./.flood_auth"
    ) -> None:
        """Init a Flood API."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._request_timeout = request_timeout
        self._api_url = f"http://{host}:{port}/api/"
        self._version = None
        self._mac_address = None

        self._session = session
        self._close_session = False

    async def _request(self, url: str, method: str, content: dict = None) -> dict:
        """Make a request to get data."""
        if self._session is None:
            jar = aiohttp.CookieJar(unsafe=True)
            self._session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}, cookie_jar=jar
            )
            self._close_session = True

        try:
            with async_timeout.timeout(self._request_timeout):
                response = await self._session.request(
                    method=method, url=url, json=content
                )
        except asyncio.TimeoutError as exception:
            raise FloodCannotConnectError(
                "Timeout occurred while connecting to Flood."
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise FloodCannotConnectError(
                "Error occurred while communicating with Flood."
            ) from exception
        if response.status == 401:
            raise FloodInvalidAuthError("Authentication failed with Flood.")

        if response.status:  # == 200:
            result = await response.json()
            response.close()
            return result
        else:
            raise FloodCannotConnectError("Unknown error")

    async def auth(self) -> bool:
        """Get authentication status after send credentials."""
        data = await self._request(
            method="POST",
            url=self._api_url + "auth/authenticate",
            content={"username": self._username, "password": self._password},
        )
        if data.get("success"):
            return True
        else:
            return False

    async def client_settings(self) -> dict:
        """Get all client settings."""
        return await self._request(method="GET", url=self._api_url + "client/settings")

    async def connected(self) -> bool:
        """Check if flood is connected to torrent client."""
        data = await self._request(
            method="GET", url=self._api_url + "client/connection-test"
        )
        return bool(data.get("isConnected"))

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


class FloodCannotConnectError(Exception):
    """Exception to indicate an error in connection."""


class FloodInvalidAuthError(Exception):
    """Exception to indicate an error in authentication."""
