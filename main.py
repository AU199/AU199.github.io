#!/usr/bin/env python3
"""Build a static scouting data bundle from the Statbotics REST API."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

API_BASE = "https://api.statbotics.io/v3"


@dataclass(frozen=True)
class Endpoint:
    key: str
    path: str


DEFAULT_ENDPOINTS: list[Endpoint] = [
    Endpoint("team", "team/{team}"),
    Endpoint("team_year", "team_year/{team}/{year}"),
    Endpoint("team_matches", "team_matches/{team}/{year}"),
    Endpoint("team_events", "team_events/{team}/{year}"),
]


def fetch_json(url: str, timeout: int) -> Any:
    with urlopen(url, timeout=timeout) as response:  # noqa: S310
        return json.load(response)


def build_bundle(team: int, year: int, timeout: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "meta": {
            "team": team,
            "year": year,
            "source": "Statbotics REST API",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "base_url": API_BASE,
        },
        "data": {},
        "errors": {},
    }

    for endpoint in DEFAULT_ENDPOINTS:
        path = endpoint.path.format(team=team, year=year)
        url = f"{API_BASE}/{path}"
        try:
            payload["data"][endpoint.key] = fetch_json(url, timeout=timeout)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            payload["errors"][endpoint.key] = str(exc)

    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Statbotics data and write a static scouting-data.json file."
    )
    parser.add_argument("--team", type=int, required=True, help="FRC team number")
    parser.add_argument("--year", type=int, required=True, help="Season year")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("scouting-data.json"),
        help="Output JSON path (default: scouting-data.json)",
    )
    parser.add_argument(
        "--timeout", type=int, default=15, help="HTTP timeout in seconds (default: 15)"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = build_bundle(team=args.team, year=args.year, timeout=args.timeout)
    args.output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    errors = bundle.get("errors", {})
    if errors:
        print("Completed with endpoint errors:")
        for key, message in errors.items():
            print(f"  - {key}: {message}")
        return 1

    print(f"Wrote {args.output} with Statbotics data for team {args.team} ({args.year}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
