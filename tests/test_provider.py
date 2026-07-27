import sys
from pathlib import Path
import asyncio

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.providers.navasan_provider import NavasanProvider


async def main():
    provider = NavasanProvider()

    result = await provider.get_latest_prices(
        [
            "usd",
            "sekkeh",
            "18ayar"
        ]
    )

    print(result["url"])
    print(result["status_code"])
    print(result["text"])


if __name__ == "__main__":
    asyncio.run(main())