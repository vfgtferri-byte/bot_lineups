#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("vessel_schedule_bot")


@dataclass
class PortTarget:
    port_name: str
    country: str
    url: str
    method: str = "html"
    notes: str = ""


class SimpleTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_td = False
        self.current_cell = ""
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"td", "th"}:
            self.in_td = True
            self.current_cell = ""
        elif tag == "tr":
            self.current_row = []

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"}:
            self.in_td = False
            self.current_row.append(self.current_cell.strip())
        elif tag == "tr":
            if any(cell for cell in self.current_row):
                self.rows.append(self.current_row)

    def handle_data(self, data: str) -> None:
        if self.in_td:
            self.current_cell += data


def load_targets(config_path: Path) -> list[PortTarget]:
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    ports = data.get("ports", [])
    return [
        PortTarget(
            port_name=str(item.get("port_name", "Unknown Port")),
            country=str(item.get("country", "Unknown Country")),
            url=str(item.get("url", "")).strip(),
            method=str(item.get("method", "html")).strip().lower(),
            notes=str(item.get("notes", "")),
        )
        for item in ports
    ]


def fetch_content(url: str, timeout: int = 30) -> tuple[str, bytes]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        payload = response.read()
    return content_type, payload


def _pick(raw: dict[str, Any], candidates: list[str]) -> str:
    lowered = {str(k).lower(): v for k, v in raw.items()}
    for key in candidates:
        if key in lowered:
            value = lowered[key]
            return "" if value is None else str(value).strip()
    return ""


def normalize_record(raw: dict[str, Any], target: PortTarget) -> dict[str, Any]:
    return {
        "scraped_at_utc": datetime.now(timezone.utc).isoformat(),
        "port_name": target.port_name,
        "country": target.country,
        "source_url": target.url,
        "vessel_name": _pick(raw, ["vessel", "vessel_name", "ship", "name", "col_1"]),
        "voyage": _pick(raw, ["voyage", "voy", "voy_no", "voyage_number", "col_2"]),
        "eta": _pick(raw, ["eta", "arrival", "estimated_arrival", "col_3"]),
        "etd": _pick(raw, ["etd", "departure", "estimated_departure", "col_4"]),
        "terminal": _pick(raw, ["terminal", "berth", "pier", "col_5"]),
        "status": _pick(raw, ["status", "remark", "remarks", "col_6"]),
    }


def parse_json_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ["data", "results", "items", "schedules", "vessels"]:
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
        return [payload]
    return []


def parse_html_tables(html_text: str) -> list[dict[str, Any]]:
    parser = SimpleTableParser()
    parser.feed(html_text)
    return [
        {f"col_{i+1}": value for i, value in enumerate(row)}
        for row in parser.rows
        if row
    ]


def scrape_target(target: PortTarget) -> list[dict[str, Any]]:
    if not target.url:
        return []
    try:
        content_type, payload = fetch_content(target.url)
        if target.method == "json" or "application/json" in content_type:
            raw_records = parse_json_payload(json.loads(payload.decode("utf-8", errors="ignore")))
        else:
            raw_records = parse_html_tables(payload.decode("utf-8", errors="ignore"))
        return [normalize_record(r, target) for r in raw_records]
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("No se pudo extraer %s: %s", target.port_name, exc)
        return []


def save_output(records: list[dict[str, Any]], output_file: Path, fmt: str) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        headers = sorted({key for row in records for key in row.keys()}) if records else []
        with output_file.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if headers:
                writer.writeheader()
                writer.writerows(records)
    else:
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bot de vessel schedules para puertos de África")
    parser.add_argument("--config", default="ports_africa.json")
    parser.add_argument("--output", default="data/schedules.json")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    targets = load_targets(Path(args.config))
    if args.limit > 0:
        targets = targets[: args.limit]

    records: list[dict[str, Any]] = []
    for target in targets:
        records.extend(scrape_target(target))

    save_output(records, Path(args.output), args.format)
    logger.info("Puertos procesados: %s | Registros: %s", len(targets), len(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
