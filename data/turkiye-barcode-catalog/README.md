# Türkiye Barcode Catalog → iMonitor Market API

This folder contains a deterministic normalization pipeline and a restartable enrichment client for **BarcodeSpider's official API**. A sample of the Turkish barcode input and a full dataset manifest are versioned here.

## Why API instead of website scraping?

BarcodeSpider's Terms of Service prohibit scraping/data-mining the website except through its API Services. This project therefore does **not** attempt browser fingerprint spoofing, CAPTCHA bypass, IP rotation, stealth crawling, or other anti-bot evasion. It uses the documented API endpoint only.

Current documented endpoint:

```text
GET https://api.barcodespider.com/v2/products/{barcode}
Authorization: Bearer YOUR_API_KEY
```

The official documentation currently describes rate limits of 1 request / 5 seconds for Free/Trial and 1 request / second for Paid plans. Configure the interval to match the subscription actually used.

## Dataset snapshot

The uploaded source contains 19,593 physical product rows. The normalizer produces 19,578 unique barcodes, repairs 4 malformed CSV rows, and removes 15 duplicate barcode rows. See `data/input/manifest.json` for exact validation statistics.

The complete source and cleaned CSV were prepared as a local handoff artifact. The current ChatGPT GitHub connector cannot stream the ~816 KB uploaded conversation file directly into a repository blob, so only `sample.csv` is committed here. Place the full source at the path below before running the entire enrichment job.

## Files

```text
data/input/sample.csv                            committed smoke-test sample
data/input/manifest.json                         full dataset statistics
scripts/prepare_input.py                         robust CSV normalizer
scripts/enrich_barcodespider.py                  official API enrichment client
schema/product_record.schema.json                normalized output contract
data/output/raw/                                 one API JSON response per barcode (runtime)
data/output/images/                              downloaded primary product images (runtime)
data/output/products.csv                         final flattened import file (runtime)
```

Expected full-data paths after copying the handoff artifact into this folder:

```text
data/source/Turkiye_barcode_database.csv
data/input/Turkiye_barcode_database.cleaned.csv
```

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate
pip install -r requirements.txt
```

Set the API key in the environment (do not commit it):

```bash
# PowerShell
$env:BARCODESPIDER_API_KEY="YOUR_KEY"
$env:BARCODESPIDER_REQUEST_INTERVAL_SECONDS="1.1"   # paid plan example

# Trial example: use 5.2 or slower
# $env:BARCODESPIDER_REQUEST_INTERVAL_SECONDS="5.2"
```

## Rebuild normalized input

```bash
python scripts/prepare_input.py \
  data/source/Turkiye_barcode_database.csv \
  data/input/Turkiye_barcode_database.cleaned.csv \
  --manifest data/input/manifest.json
```

## Enrich products

Smoke-test using the committed sample:

```bash
python scripts/enrich_barcodespider.py \
  data/input/sample.csv \
  --output-dir data/output \
  --limit 20
```

Then continue all remaining products after the full cleaned file is present:

```bash
python scripts/enrich_barcodespider.py \
  data/input/Turkiye_barcode_database.cleaned.csv \
  --output-dir data/output
```

The process is restartable. Successful and not-found barcodes are skipped on later runs. Failed items can be retried with `--retry-errors`.

## Output fields useful for iMonitor

`barcode`, source name, BarcodeSpider product name, brand, manufacturer, category ID/path, derived group/subgroup, model, MPN, ASIN, size, weight, color, description, attributes/features, image URLs, locally cached primary image path, country/ISO, raw response path, status and timestamp.

## Git and licensing note

The enrichment output is ignored by `.gitignore` by default because BarcodeSpider's terms restrict making Product Data publicly available. If your BarcodeSpider subscription/license explicitly permits repository storage/redistribution, use a **private repository** and change the ignore rules deliberately. The code and user-provided source can be versioned independently.
