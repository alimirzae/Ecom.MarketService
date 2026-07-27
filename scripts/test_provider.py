import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.providers.navasan_provider import NavasanProvider


async def main():

    provider = NavasanProvider()

    prices = await provider.get_latest_prices(
        [
            "usd",
            "18ayar",
            "sekkeh"
        ]
    )

    for item in prices:

        print("--------------------------")

        print(item)


if __name__ == "__main__":
    asyncio.run(main())