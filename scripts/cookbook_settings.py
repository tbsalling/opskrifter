from __future__ import annotations

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPES_DIR = ROOT / "recipes"
OUTPUT_DIR = ROOT / "output"
PDF_PATH = OUTPUT_DIR / "kogebog.pdf"
DATA_DIR = ROOT / "data"
VERSION_FILE = DATA_DIR / "book_version.txt"
COVER_IMAGE_PATH = DATA_DIR / "forside.png"

A4_W, A4_H = 2480, 3508
PDF_SCALE = 72 / 300
PDF_W, PDF_H = A4_W * PDF_SCALE, A4_H * PDF_SCALE
OUTER_MARGIN = 90
INNER_MARGIN = 120
TITLE = "Vores opskrifter"
SUBTITLE = "Mad fra Solsidens køkken"

MONTH_NAMES = {
    1: "januar",
    2: "februar",
    3: "marts",
    4: "april",
    5: "maj",
    6: "juni",
    7: "juli",
    8: "august",
    9: "september",
    10: "oktober",
    11: "november",
    12: "december",
}

def format_danish_date(build_date: date) -> str:
    return f"{build_date.day}. {MONTH_NAMES[build_date.month]} {build_date.year}"


def next_book_version() -> int:
    if not VERSION_FILE.exists():
        return 1
    raw = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return 1
    return int(raw) + 1


def write_book_version(version: int) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(f"{version}\n", encoding="utf-8")

RECIPE_SECTION_SIZE = 32
RECIPE_TITLE_SIZE = 70
RECIPE_CHIP_SIZE = 36
RECIPE_BODY_SIZE = 42
RECIPE_BODY_BOLD_SIZE = 44
RECIPE_SMALL_SIZE = 36
COMPONENT_PREFIX = ":: "
COMPONENT_TOP_GAP = 1.1
COMPONENT_BOTTOM_GAP = 0.14
