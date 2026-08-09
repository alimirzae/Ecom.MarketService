import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("enrich", ROOT / "scripts" / "enrich_barcodespider.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_split_category():
    assert mod.split_category("Food > Beverages > Water") == ("Food", "Beverages")


def test_normalize_product():
    payload = {
        "meta": {"success": True, "code": 200},
        "identifiers": {"barcode_type": "EAN-13", "values": {"ean13": "8693275000107"}, "region": {"name": "Turkey", "iso": "TR"}},
        "product": {"name": "Test", "brand": "Brand", "manufacturer": "Maker", "category": {"id": 7, "path": "Food > Oils"}, "images": ["https://example.com/a.jpg"]}
    }
    row = mod.normalize("8693275000107", "source", payload, 200, "raw/8693275000107.json")
    assert row["lookup_status"] == "found"
    assert row["group"] == "Food"
    assert row["subgroup"] == "Oils"
    assert row["manufacturer"] == "Maker"
