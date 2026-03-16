#!/usr/bin/env python3
from __future__ import annotations

from datetime import date

from cookbook_markdown_output import build_markdown_and_page_map, ordered_recipes, write_contents_file
from cookbook_pdf_renderer import build_pdf_vector, pdf_canvas
from cookbook_settings import OUTPUT_DIR, PDF_PATH, format_danish_date, next_book_version, write_book_version


def build() -> None:
    if pdf_canvas is None:
        raise RuntimeError(
            "Den vektorbaserede PDF-generator kræver ReportLab. "
            "Installér den i et virtuelt miljø med `python3 -m pip install reportlab`."
        )
    build_version = next_book_version()
    build_date_text = format_danish_date(date.today())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ordered = ordered_recipes()
    page_map, nutrition_map, raw_keys = build_markdown_and_page_map(ordered)
    write_contents_file(ordered, page_map)
    build_pdf_vector(build_version, build_date_text, ordered, page_map, nutrition_map, raw_keys)
    write_book_version(build_version)

    raw_page_count = 1
    left_capacity = int((3508 - 150 - (360 + 28 + 60 + 28)) / 54)
    right_capacity = left_capacity
    raw_capacity = left_capacity + right_capacity
    if raw_keys:
        raw_page_count = (len(raw_keys) + raw_capacity - 1) // raw_capacity
    page_count = 2 + len(ordered) + raw_page_count + 1
    while page_count % 4 != 0:
        page_count += 1

    print(f"Skrev {len(ordered)} opskrifter i {OUTPUT_DIR.parent / 'recipes'}")
    print(f"A4-sider: {page_count}")
    print(f"Forside: version {build_version}, dato {build_date_text}")
    print(f"PDF: {PDF_PATH}")


if __name__ == "__main__":
    try:
        build()
    except RuntimeError as exc:
        raise SystemExit(str(exc))
