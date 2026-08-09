import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_input", ROOT / "scripts" / "prepare_input.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_gtin_known_valid():
    assert mod.gtin_check("8693275000107") is True


def test_parse_normal():
    barcode, name, repaired = mod.parse_line("8693275000107,COTANAK AYCICEK YAGI 1LT.", 2)
    assert barcode == "8693275000107"
    assert name == "COTANAK AYCICEK YAGI 1LT."
    assert repaired is False


def test_parse_malformed_quoted_comma():
    line = '"8694778004029,""LEZZET GOF,KAKAOLU"",,"'
    barcode, name, repaired = mod.parse_line(line, 2)
    assert barcode == "8694778004029"
    assert name == "LEZZET GOF,KAKAOLU"
    assert repaired is True
