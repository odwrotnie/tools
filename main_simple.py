"""
Minimalny przykład użycia pakietu `ignorant` (jak w README),
z prostymi flagami CLI do podania numeru i kodu kraju.

Uruchomienie:
  python main_simple.py --country 48 --phone 603036765

Repo: https://github.com/megadose/ignorant
"""

from __future__ import annotations

import argparse
import json

import trio
import httpx

from ignorant.modules.shopping.amazon import amazon


async def run(country_code: str, phone: str) -> None:
    client = httpx.AsyncClient()
    out = []
    await amazon(phone, country_code, client, out)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    await client.aclose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimalne wywołanie ignorant -> amazon")
    parser.add_argument("--country", required=True, help="Kod kraju, np. 48")
    parser.add_argument("--phone", required=True, help="Numer telefonu bez prefiksu kraju")
    args = parser.parse_args()

    trio.run(run, args.country, args.phone)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


