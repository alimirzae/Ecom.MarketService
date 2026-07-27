import ast
import codecs
import re

import httpx
from bs4 import BeautifulSoup

from app.dto.provider_result import ProviderResult
from app.utils.persian import normalize_number


from app.providers.base_provider import BaseMarketProvider

class NavasanProvider(BaseMarketProvider):
    
    BASE_URL = "https://www.navasan.tech/wp-navasan.php"

    PROVIDER = "navasan"

    async def get_latest_prices(
        self,
        codes: list[str]
    ) -> list[ProviderResult]:

        url = f"{self.BASE_URL}?{'&'.join(codes)}"

        async with httpx.AsyncClient(
            timeout=20,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        ) as client:

            response = await client.get(url)

            response.raise_for_status()

        text = response.text

        #
        # Response format:
        # navasanret("....");
        #

        match = re.search(
            r"navasanret\((.*)\)\s*;?\s*$",
            text,
            re.DOTALL,
        )

        if match is None:
            raise RuntimeError("Cannot parse Navasan response.")

        js_string = match.group(1).strip()

        #
        # Convert JavaScript string literal
        #

        html = ast.literal_eval(js_string)

        #
        # Remove extra quotes
        #

        if html.startswith('"') and html.endswith('"'):
            html = html[1:-1]

        #
        # Decode unicode escape sequences
        #

        html = codecs.decode(html, "unicode_escape")

        #
        # Fix escaped slashes
        #

        html = html.replace("\\/", "/")

        soup = BeautifulSoup(html, "html.parser")

        prices: list[ProviderResult] = []

        for row in soup.select("tbody tr[id]"):

            code = row.get("id", "").strip()

            tds = row.find_all("td")

            if len(tds) != 4:
                continue

            from app.utils.text import decode_js_string

            title = decode_js_string(
                tds[0].get_text(strip=True)
            )

            value = normalize_number(
                tds[1].get_text(strip=True)
            )

            change = normalize_number(
                tds[2].get_text(strip=True)
            )

            update_time = decode_js_string(
                tds[3].get_text(strip=True)
            )

            #
            # normalize provider time
            #

            update_time = (
                update_time
                .translate(str.maketrans(
                    "۰۱۲۳۴۵۶۷۸۹",
                    "0123456789"
                ))
                .translate(str.maketrans(
                    "٠١٢٣٤٥٦٧٨٩",
                    "0123456789"
                ))
            )

            prices.append(
                ProviderResult(
                    code=code,
                    title=title,
                    price=value,
                    change=change,
                    provider_time=update_time,
                )
            )

        return prices