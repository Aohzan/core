"""Test flood."""

import asyncio

from pyflood import FloodApi


async def main():
    """Run tests on flood."""
    async with FloodApi(
        "192.168.1.243", "80", "matthieu", "7tp57Mu9UKrnEVLwzZ2Y"
    ) as flood:
        await flood.auth()
        settings = await flood.client_settings()
        print(settings)


if __name__ == "__main__":
    """start."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
