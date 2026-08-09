#!/usr/bin/env python3
"""Restore the original uploaded CSV from versioned base64 gzip shards."""
from __future__ import annotations

import argparse
import base64
import gzip
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parts_dir", type=Path)
    ap.add_argument("output_csv", type=Path)
    args = ap.parse_args()

    parts = sorted(args.parts_dir.glob("part-*.b64"))
    if not parts:
        raise SystemExit(f"No part-*.b64 files found in {args.parts_dir}")
    encoded = "".join(p.read_text(encoding="ascii").strip() for p in parts)
    compressed = base64.b64decode(encoded, validate=True)
    raw = gzip.decompress(compressed)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_csv.write_bytes(raw)
    print(f"Restored {args.output_csv} ({len(raw)} bytes) from {len(parts)} parts")


if __name__ == "__main__":
    main()
