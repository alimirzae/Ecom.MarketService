#!/usr/bin/env python3
"""Normalize the uploaded Turkish barcode CSV without losing barcode leading zeros."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

MALFORMED = re.compile(r'^"(\d{8,14}),""(.*)"",,"$')


def gtin_check(code: str):
    if not code.isdigit() or len(code) not in (8, 12, 13, 14):
        return None
    digits = [int(x) for x in code]
    check = digits[-1]
    total = 0
    for i, digit in enumerate(reversed(digits[:-1])):
        total += digit * (3 if i % 2 == 0 else 1)
    return ((10 - total % 10) % 10) == check


def parse_line(line: str, line_no: int):
    row = next(csv.reader([line]))
    if len(row) >= 2 and re.fullmatch(r"\d{8,14}", row[0].strip()):
        return row[0].strip(), row[1].strip(), False

    m = MALFORMED.match(line)
    if m:
        name = m.group(2).replace('""""', '"').strip()
        return m.group(1), name, True

    m = re.match(r'^\s*"?(\d{8,14})[,;]', line)
    if not m:
        raise ValueError(f"Cannot parse line {line_no}: {line[:120]!r}")
    barcode = m.group(1)
    remainder = line[m.end():].strip().strip(',').strip('"').replace('""', '"').strip()
    return barcode, remainder, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--manifest", type=Path, required=True)
    args = ap.parse_args()

    lines = args.source.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    if not lines:
        raise SystemExit("Input file is empty")

    parsed = []
    malformed_count = 0
    for line_no, line in enumerate(lines[1:], start=2):
        barcode, product_name, repaired = parse_line(line, line_no)
        malformed_count += int(repaired)
        parsed.append({
            "barcode": barcode,
            "source_product_name": product_name or None,
            "source_line": line_no,
            "gtin_check_digit_valid": gtin_check(barcode),
        })

    seen = {}
    duplicate_rows = 0
    for item in parsed:
        if item["barcode"] in seen:
            duplicate_rows += 1
            continue
        seen[item["barcode"]] = item

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "barcode", "source_product_name", "source_line", "gtin_check_digit_valid"
        ])
        writer.writeheader()
        writer.writerows(seen.values())

    check_counts = Counter(str(x["gtin_check_digit_valid"]) for x in parsed)
    manifest = {
        "source_file": args.source.name,
        "source_rows": len(parsed),
        "unique_barcodes": len(seen),
        "duplicate_rows_removed": duplicate_rows,
        "repaired_malformed_rows": malformed_count,
        "gtin_check_digit": {
            "valid": check_counts.get("True", 0),
            "invalid": check_counts.get("False", 0),
            "not_applicable_length": check_counts.get("None", 0),
        },
        "barcode_lengths": dict(sorted(Counter(len(x["barcode"]) for x in parsed).items())),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
