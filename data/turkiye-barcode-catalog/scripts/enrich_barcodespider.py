#!/usr/bin/env python3
"""Enrich a barcode CSV through BarcodeSpider's official API.

This intentionally does NOT scrape barcodespider.com pages or bypass anti-bot controls.
It uses the documented /v2/products/{barcode} endpoint, respects rate limits, caches
raw responses, is restartable, and optionally downloads the primary image returned by API.
"""
from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

API_BASE = "https://api.barcodespider.com/v2/products"
FIELDS = [
    "barcode", "source_product_name", "lookup_status", "http_status", "source_provider",
    "barcode_type", "upc", "ean13", "country", "country_iso", "name", "brand",
    "manufacturer", "category_id", "category_path", "group", "subgroup", "model",
    "mpn", "asin", "size", "weight", "color", "description", "features_json",
    "attributes_json", "image_urls_json", "primary_image_url", "primary_image_path",
    "raw_json_path", "fetched_at_utc", "error"
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def nested(obj: dict[str, Any], *keys, default=None):
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def split_category(path: Any):
    if not path:
        return None, None
    text = str(path).strip()
    for delim in (" > ", ">", " / ", "/", "|", "→"):
        if delim in text:
            parts = [p.strip() for p in text.split(delim) if p.strip()]
            return (parts[0] if parts else None, parts[1] if len(parts) > 1 else None)
    return text, None


def image_extension(url: str, content_type: str | None) -> str:
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            return ".jpg" if ext == ".jpeg" else ext
    ext = Path(urlparse(url).path).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"


def load_input(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            barcode = (row.get("barcode") or row.get("Barcode_ID") or "").strip()
            if not barcode:
                continue
            yield barcode, (row.get("source_product_name") or row.get("Product_Name") or "").strip()


def load_existing(path: Path):
    existing: dict[str, dict[str, str]] = {}
    if path.exists() and path.stat().st_size:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("barcode"):
                    existing[row["barcode"]] = row
    return existing


def save_rows(path: Path, rows: dict[str, dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for barcode in sorted(rows):
            writer.writerow(rows[barcode])
    tmp.replace(path)


def api_lookup(session: requests.Session, api_key: str, barcode: str, timeout: float,
               max_retries: int):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "iMonitor-MarketCatalog/1.0 (BarcodeSpider official API client)",
    }
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            resp = session.get(f"{API_BASE}/{barcode}", headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt >= max_retries:
                raise
            time.sleep(min(60, (2 ** attempt) + random.random()))
            continue

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            try:
                wait = float(retry_after) if retry_after else min(60, 2 ** (attempt + 1))
            except ValueError:
                wait = min(60, 2 ** (attempt + 1))
            if attempt >= max_retries:
                return resp, None
            time.sleep(wait + random.uniform(0.1, 0.6))
            continue
        if 500 <= resp.status_code < 600 and attempt < max_retries:
            time.sleep(min(60, (2 ** attempt) + random.random()))
            continue
        try:
            return resp, resp.json()
        except ValueError:
            return resp, None
    raise RuntimeError(last_error or "lookup failed")


def download_primary_image(session: requests.Session, url: str, barcode: str, image_dir: Path,
                           timeout: float):
    image_dir.mkdir(parents=True, exist_ok=True)
    resp = session.get(url, timeout=timeout, allow_redirects=True, headers={
        "User-Agent": "iMonitor-MarketCatalog/1.0"
    })
    resp.raise_for_status()
    ctype = resp.headers.get("Content-Type")
    if ctype and not ctype.lower().startswith("image/"):
        raise ValueError(f"Image URL returned non-image Content-Type: {ctype}")
    ext = image_extension(url, ctype)
    out = image_dir / f"{barcode}{ext}"
    out.write_bytes(resp.content)
    return out


def normalize(barcode: str, source_name: str, payload: dict[str, Any] | None,
              status_code: int, raw_rel: str | None):
    now = utc_now()
    if not payload:
        return {
            "barcode": barcode, "source_product_name": source_name, "lookup_status": "error",
            "http_status": status_code, "source_provider": "barcodespider_api",
            "raw_json_path": raw_rel, "fetched_at_utc": now,
            "error": "API response was not valid JSON"
        }
    meta = payload.get("meta") or {}
    if status_code == 404 or meta.get("code") == 404:
        return {
            "barcode": barcode, "source_product_name": source_name, "lookup_status": "not_found",
            "http_status": status_code, "source_provider": "barcodespider_api",
            "raw_json_path": raw_rel, "fetched_at_utc": now,
            "error": meta.get("message")
        }
    if status_code >= 400 or meta.get("success") is False:
        return {
            "barcode": barcode, "source_product_name": source_name, "lookup_status": "error",
            "http_status": status_code, "source_provider": "barcodespider_api",
            "raw_json_path": raw_rel, "fetched_at_utc": now,
            "error": meta.get("message") or f"HTTP {status_code}"
        }

    product = payload.get("product") or {}
    identifiers = payload.get("identifiers") or {}
    values = identifiers.get("values") or {}
    region = identifiers.get("region") or {}
    category = product.get("category") or {}
    category_path = category.get("path")
    group, subgroup = split_category(category_path)
    images = product.get("images") or []
    if isinstance(images, str):
        images = [images]
    images = [str(x) for x in images if x]
    return {
        "barcode": barcode,
        "source_product_name": source_name,
        "lookup_status": "found",
        "http_status": status_code,
        "source_provider": "barcodespider_api",
        "barcode_type": identifiers.get("barcode_type"),
        "upc": values.get("upc"),
        "ean13": values.get("ean13"),
        "country": region.get("name") or nested(identifiers, "gs1_allocation", "name"),
        "country_iso": region.get("iso"),
        "name": product.get("name"),
        "brand": product.get("brand"),
        "manufacturer": product.get("manufacturer"),
        "category_id": category.get("id"),
        "category_path": category_path,
        "group": group,
        "subgroup": subgroup,
        "model": product.get("model"),
        "mpn": product.get("mpn"),
        "asin": product.get("asin"),
        "size": product.get("size"),
        "weight": product.get("weight"),
        "color": product.get("color"),
        "description": product.get("description"),
        "features_json": json.dumps(product.get("features") or [], ensure_ascii=False),
        "attributes_json": json.dumps(product.get("attributes") or {}, ensure_ascii=False),
        "image_urls_json": json.dumps(images, ensure_ascii=False),
        "primary_image_url": images[0] if images else None,
        "raw_json_path": raw_rel,
        "fetched_at_utc": now,
        "error": None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_csv", type=Path)
    ap.add_argument("--output-dir", type=Path, default=Path("data/output"))
    ap.add_argument("--api-key", default=os.getenv("BARCODESPIDER_API_KEY"))
    ap.add_argument("--interval", type=float, default=float(os.getenv("BARCODESPIDER_REQUEST_INTERVAL_SECONDS", "1.1")))
    ap.add_argument("--timeout", type=float, default=25.0)
    ap.add_argument("--max-retries", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0, help="0 = all remaining rows")
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--retry-errors", action="store_true")
    args = ap.parse_args()

    if not args.api_key:
        raise SystemExit("BARCODESPIDER_API_KEY is required. Use the official BarcodeSpider API key.")
    if args.interval < 1.0:
        raise SystemExit("Refusing interval < 1 second; current paid API docs specify 1 request/sec.")

    outdir = args.output_dir
    rawdir = outdir / "raw"
    imgdir = outdir / "images"
    products_csv = outdir / "products.csv"
    checkpoint = outdir / "checkpoint.json"
    rawdir.mkdir(parents=True, exist_ok=True)
    imgdir.mkdir(parents=True, exist_ok=True)

    rows = load_existing(products_csv)
    session = requests.Session()
    processed_this_run = 0

    for barcode, source_name in load_input(args.input_csv):
        previous = rows.get(barcode)
        if previous and previous.get("lookup_status") in {"found", "not_found"}:
            continue
        if previous and previous.get("lookup_status") == "error" and not args.retry_errors:
            continue
        if args.limit and processed_this_run >= args.limit:
            break

        started = time.monotonic()
        raw_path = rawdir / f"{barcode}.json"
        try:
            resp, payload = api_lookup(session, args.api_key, barcode, args.timeout, args.max_retries)
            if resp.status_code == 401:
                raise SystemExit("BarcodeSpider API returned 401. Check BARCODESPIDER_API_KEY.")
            raw_rel = None
            if payload is not None:
                raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                raw_rel = str(raw_path.as_posix())
            record = normalize(barcode, source_name, payload, resp.status_code, raw_rel)

            if record.get("lookup_status") == "found" and record.get("primary_image_url") and not args.no_images:
                try:
                    image_path = download_primary_image(session, record["primary_image_url"], barcode, imgdir, args.timeout)
                    record["primary_image_path"] = image_path.as_posix()
                except Exception as exc:
                    record["error"] = (record.get("error") or "") + f" image_download: {exc}"

        except SystemExit:
            raise
        except Exception as exc:
            record = {
                "barcode": barcode, "source_product_name": source_name,
                "lookup_status": "error", "http_status": "",
                "source_provider": "barcodespider_api", "fetched_at_utc": utc_now(),
                "error": str(exc),
            }

        rows[barcode] = record
        save_rows(products_csv, rows)
        checkpoint.write_text(json.dumps({
            "last_barcode": barcode,
            "processed_this_run": processed_this_run + 1,
            "total_saved": len(rows),
            "updated_at_utc": utc_now(),
        }, indent=2), encoding="utf-8")
        processed_this_run += 1

        elapsed = time.monotonic() - started
        sleep_for = args.interval - elapsed
        if sleep_for > 0:
            time.sleep(sleep_for)

    print(f"Saved {len(rows)} rows to {products_csv}")


if __name__ == "__main__":
    main()
