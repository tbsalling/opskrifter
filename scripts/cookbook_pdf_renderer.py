from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

try:
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas as pdf_canvas
except ImportError:
    HexColor = None
    ImageReader = None
    pdfmetrics = None
    TTFont = None
    pdf_canvas = None

from cookbook_markdown_output import component_name, is_component_entry, recipe_component_entries
from cookbook_recipe_data import DISPLAY_NAMES, NDB, SECTION_STYLES
from cookbook_settings import (
    A4_H,
    A4_W,
    COMPONENT_BOTTOM_GAP,
    COMPONENT_TOP_GAP,
    COVER_IMAGE_PATH,
    INNER_MARGIN,
    OUTER_MARGIN,
    PDF_H,
    PDF_PATH,
    PDF_SCALE,
    PDF_W,
    RECIPE_BODY_BOLD_SIZE,
    RECIPE_BODY_SIZE,
    RECIPE_CHIP_SIZE,
    RECIPE_SECTION_SIZE,
    RECIPE_SMALL_SIZE,
    RECIPE_TITLE_SIZE,
    TITLE,
    SUBTITLE,
)

def font_candidates(style: str) -> List[str]:
    if style == "display":
        return [
            "/System/Library/Fonts/Supplemental/Didot.ttc",
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
            "/System/Library/Fonts/Supplemental/Baskerville.ttc",
        ]
    if style == "serif":
        return [
            "/System/Library/Fonts/Supplemental/Baskerville.ttc",
            "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        ]
    if style == "serif-bold":
        return [
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
            "/System/Library/Fonts/Supplemental/Baskerville.ttc",
        ]
    if style == "sans":
        return [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    if style == "sans-bold":
        return [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        ]
    return ["/System/Library/Fonts/Supplemental/Arial.ttf"]


def load_font(size: int, style: str = "sans"):
    for candidate in font_candidates(style):
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def register_pdf_fonts() -> Dict[str, str]:
    if pdf_canvas is None or pdfmetrics is None or TTFont is None:
        raise RuntimeError(
            "ReportLab er ikke installeret. Installér det med "
            "`python3 -m pip install reportlab` i et virtuelt miljø."
        )
    if hasattr(register_pdf_fonts, "_fonts"):
        return register_pdf_fonts._fonts  # type: ignore[attr-defined]

    styles = {
        "display": ("CookbookDisplay", ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf"], "Helvetica-Bold"),
        "sans": ("CookbookSans", ["/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"], "Helvetica"),
        "sans-bold": ("CookbookSansBold", ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"], "Helvetica-Bold"),
    }
    fonts: Dict[str, str] = {}
    for style, (font_name, candidates, fallback) in styles.items():
        for candidate in candidates:
            path = Path(candidate)
            if not path.exists():
                continue
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(path)))
                fonts[style] = font_name
                break
            except Exception:
                continue
        else:
            fonts[style] = fallback
    register_pdf_fonts._fonts = fonts  # type: ignore[attr-defined]
    return fonts


def px(value: float) -> float:
    return value * PDF_SCALE


def pdf_text_width(text: str, font_name: str, font_size: int) -> float:
    return pdfmetrics.stringWidth(text, font_name, px(font_size)) / PDF_SCALE


def pdf_font_ascent(font_name: str, font_size: int) -> float:
    return (pdfmetrics.getAscent(font_name) / 1000.0) * font_size


def pdf_font_height(font_name: str, font_size: int) -> float:
    ascent = pdfmetrics.getAscent(font_name) / 1000.0
    descent = abs(pdfmetrics.getDescent(font_name) / 1000.0)
    return (ascent + descent) * font_size


def pdf_wrap_text(text: str, font_name: str, font_size: int, width: int) -> List[str]:
    if not text:
        return [""]
    words = text.split()
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        test = f"{current} {word}"
        if pdf_text_width(test, font_name, font_size) <= width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def pdf_tag_size(text: str, font_name: str, font_size: int) -> Tuple[int, int]:
    width = int(round(pdf_text_width(text, font_name, font_size))) + 38
    height = int(round(pdf_font_height(font_name, font_size))) + 20
    return width, height


def pdf_set_fill(canvas, color: str) -> None:
    canvas.setFillColor(HexColor(color))


def pdf_set_stroke(canvas, color: str) -> None:
    canvas.setStrokeColor(HexColor(color))


def pdf_draw_text(canvas, x: float, y: float, text: str, font_name: str, font_size: int, fill: str) -> None:
    pdf_set_fill(canvas, fill)
    canvas.setFont(font_name, px(font_size))
    baseline_y = PDF_H - px(y + pdf_font_ascent(font_name, font_size))
    canvas.drawString(px(x), baseline_y, text)


def pdf_draw_text_block(canvas, x: int, y: int, width: int, text: str, font_name: str, font_size: int, fill: str, step: int) -> int:
    current_y = y
    for line in pdf_wrap_text(text, font_name, font_size, width):
        pdf_draw_text(canvas, x, current_y, line, font_name, font_size, fill)
        current_y += step
    return current_y


def pdf_round_rect(canvas, x: int, y: int, width: int, height: int, radius: int, fill: str, stroke: str | None = None, stroke_width: int = 1) -> None:
    if stroke:
        pdf_set_stroke(canvas, stroke)
    pdf_set_fill(canvas, fill)
    canvas.setLineWidth(px(stroke_width))
    canvas.roundRect(px(x), PDF_H - px(y + height), px(width), px(height), px(radius), fill=1, stroke=1 if stroke else 0)


def pdf_line(canvas, x1: int, y1: int, x2: int, y2: int, color: str, width: int) -> None:
    pdf_set_stroke(canvas, color)
    canvas.setLineWidth(px(width))
    canvas.line(px(x1), PDF_H - px(y1), px(x2), PDF_H - px(y2))


def pdf_ellipse(canvas, x1: int, y1: int, x2: int, y2: int, fill: str | None = None, stroke: str | None = None, stroke_width: int = 1) -> None:
    if stroke:
        pdf_set_stroke(canvas, stroke)
    if fill:
        pdf_set_fill(canvas, fill)
    canvas.setLineWidth(px(stroke_width))
    canvas.ellipse(px(x1), PDF_H - px(y2), px(x2), PDF_H - px(y1), fill=1 if fill else 0, stroke=1 if stroke else 0)


def pdf_tag(canvas, x: int, y: int, text: str, font_name: str, font_size: int, fill: str, ink: str) -> int:
    width, height = pdf_tag_size(text, font_name, font_size)
    pdf_round_rect(canvas, x, y, width, height, 18, fill)
    pdf_draw_text(canvas, x + 19, y + 10, text, font_name, font_size, ink)
    return width


def pdf_measure_recipe_columns(
    ingredient_entries: List[str],
    method_entries: List[str],
    ingredient_width: int,
    method_width: int,
    body_font_name: str,
    body_bold_name: str,
    body_line: int,
) -> Tuple[int, int]:
    left_height = 0
    for ingredient in ingredient_entries:
        if is_component_entry(ingredient):
            left_height += int(body_line * COMPONENT_TOP_GAP)
            left_height += len(pdf_wrap_text(component_name(ingredient), body_bold_name, RECIPE_BODY_BOLD_SIZE, ingredient_width)) * body_line
            left_height += int(body_line * COMPONENT_BOTTOM_GAP)
        else:
            left_height += len(pdf_wrap_text(f"• {ingredient}", body_font_name, RECIPE_BODY_SIZE, ingredient_width)) * body_line

    right_height = 0
    step_number = 1
    for step in method_entries:
        if is_component_entry(step):
            step_number = 1
            right_height += int(body_line * COMPONENT_TOP_GAP)
            right_height += len(pdf_wrap_text(component_name(step), body_bold_name, RECIPE_BODY_BOLD_SIZE, method_width)) * body_line
            right_height += int(body_line * COMPONENT_BOTTOM_GAP)
        else:
            right_height += len(pdf_wrap_text(f"{step_number}. {step}", body_font_name, RECIPE_BODY_SIZE, method_width)) * body_line
            right_height += int(body_line * 0.15)
            step_number += 1
    return left_height, right_height


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> List[str]:
    if not text:
        return [""]
    words = text.split()
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        test = f"{current} {word}"
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def line_height(font_size: int, multiplier: float = 1.28) -> int:
    return int(font_size * multiplier)


def draw_pattern(draw: ImageDraw.ImageDraw, style: SectionStyle) -> None:
    draw.ellipse([A4_W - 520, -120, A4_W - 40, 360], outline=style.soft, width=4)
    draw.ellipse([A4_W - 440, -40, A4_W + 80, 480], outline=style.soft, width=2)
    draw.ellipse([60, A4_H - 400, 420, A4_H - 40], outline=style.soft, width=3)
    draw.line([OUTER_MARGIN, 160, A4_W - OUTER_MARGIN, 160], fill=style.soft, width=3)


def section_label(section: str) -> str:
    labels = {
        "Bagværk": "Bagværk",
        "Tilbehør": "Tilbehør",
        "Aftensmad": "Aftensmad",
        "Weekend": "Weekendret",
    }
    return labels[section]


def recipe_fonts():
    return {
        "title": load_font(RECIPE_TITLE_SIZE, "display"),
        "chip": load_font(RECIPE_CHIP_SIZE, "sans-bold"),
        "section": load_font(RECIPE_SECTION_SIZE, "sans-bold"),
        "body": load_font(RECIPE_BODY_SIZE, "sans"),
        "body_bold": load_font(RECIPE_BODY_BOLD_SIZE, "sans-bold"),
        "small": load_font(RECIPE_SMALL_SIZE, "sans"),
        "body_line": line_height(RECIPE_BODY_SIZE, 1.28),
        "small_line": line_height(RECIPE_SMALL_SIZE, 1.26),
        "title_line": line_height(RECIPE_TITLE_SIZE, 1.05),
    }


def tag_size(draw: ImageDraw.ImageDraw, text: str, font) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0] + 38
    height = bbox[3] - bbox[1] + 20
    return width, height


def measure_recipe_columns(
    ingredient_entries: List[str],
    method_entries: List[str],
    draw: ImageDraw.ImageDraw,
    ingredient_width: int,
    method_width: int,
    body_font,
    body_bold,
    body_line: int,
) -> Tuple[int, int]:
    left_height = 0
    for ingredient in ingredient_entries:
        if is_component_entry(ingredient):
            left_height += int(body_line * COMPONENT_TOP_GAP)
            left_height += len(wrap_text(draw, component_name(ingredient), body_bold, ingredient_width)) * body_line
            left_height += int(body_line * COMPONENT_BOTTOM_GAP)
        else:
            left_height += len(wrap_text(draw, f"• {ingredient}", body_font, ingredient_width)) * body_line

    right_height = 0
    step_number = 1
    for step in method_entries:
        if is_component_entry(step):
            step_number = 1
            right_height += int(body_line * COMPONENT_TOP_GAP)
            right_height += len(wrap_text(draw, component_name(step), body_bold, method_width)) * body_line
            right_height += int(body_line * COMPONENT_BOTTOM_GAP)
        else:
            right_height += len(wrap_text(draw, f"{step_number}. {step}", body_font, method_width)) * body_line
            right_height += int(body_line * 0.15)
            step_number += 1

    return left_height, right_height


def draw_tag(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, font, fill: str, ink: str) -> None:
    x, y = xy
    width, height = tag_size(draw, text, font)
    draw.rounded_rectangle([x, y, x + width, y + height], radius=18, fill=fill)
    draw.text((x + 19, y + 10), text, font=font, fill=ink)


def draw_text_block(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, text: str, font, fill: str, step: int):
    current_y = y
    for line in wrap_text(draw, text, font, width):
        draw.text((x, current_y), line, font=font, fill=fill)
        current_y += step
    return current_y


def hex_to_rgb(value: str) -> Tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def vertical_gradient(width: int, height: int, top_hex: str, bottom_hex: str) -> Image.Image:
    top = hex_to_rgb(top_hex)
    bottom = hex_to_rgb(bottom_hex)
    image = Image.new("RGB", (width, height), top_hex)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)
    return image


def blurred_ellipse(overlay: Image.Image, bbox: List[int], fill, blur_radius: int) -> None:
    shadow = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse(bbox, fill=fill)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    overlay.alpha_composite(shadow)


def blurred_roundrect(overlay: Image.Image, bbox: List[int], radius: int, fill, blur_radius: int) -> None:
    shadow = Image.new("RGBA", overlay.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(bbox, radius=radius, fill=fill)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    overlay.alpha_composite(shadow)


def draw_salad_bowl(overlay: Image.Image, cx: int, cy: int, width: int, height: int) -> None:
    draw = ImageDraw.Draw(overlay)
    blurred_ellipse(overlay, [cx - width // 2 + 18, cy - height // 2 + 36, cx + width // 2 + 18, cy + height // 2 + 40], (0, 0, 0, 74), 28)
    bowl = [cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2]
    draw.ellipse(bowl, fill="#f5f0ea", outline="#d9cec3", width=5)
    fill = [bowl[0] + 26, bowl[1] + 32, bowl[2] - 26, bowl[3] - 20]
    draw.ellipse(fill, fill="#d8e3d0")
    greens = [
        [fill[0] + 40, fill[1] + 26, fill[0] + 170, fill[1] + 120],
        [fill[0] + 130, fill[1] + 58, fill[0] + 270, fill[1] + 156],
        [fill[0] + 250, fill[1] + 24, fill[0] + 410, fill[1] + 140],
        [fill[0] + 330, fill[1] + 68, fill[0] + 470, fill[1] + 170],
    ]
    for leaf in greens:
        draw.ellipse(leaf, fill="#6f9160", outline="#527246", width=3)
        mid_y = (leaf[1] + leaf[3]) // 2
        draw.line([leaf[0] + 16, mid_y, leaf[2] - 16, mid_y], fill="#cfe0c5", width=2)
    for tomato in [(fill[0] + 145, fill[1] + 84, 32), (fill[0] + 300, fill[1] + 90, 28), (fill[0] + 390, fill[1] + 122, 24)]:
        tx, ty, radius = tomato
        draw.ellipse([tx - radius, ty - radius, tx + radius, ty + radius], fill="#d65a44", outline="#a83e30", width=3)
        draw.ellipse([tx - radius + 10, ty - radius + 10, tx - 2, ty - 8], fill="#ec9b88")
    draw.arc([bowl[0] + 26, bowl[1] + 26, bowl[2] - 26, bowl[3] - 26], start=205, end=330, fill="#ffffff", width=6)


def draw_pasta_plate(overlay: Image.Image, cx: int, cy: int, width: int, height: int) -> None:
    draw = ImageDraw.Draw(overlay)
    blurred_ellipse(overlay, [cx - width // 2 + 26, cy - height // 2 + 44, cx + width // 2 + 26, cy + height // 2 + 52], (0, 0, 0, 86), 34)
    plate = [cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2]
    draw.ellipse(plate, fill="#fbf7f1", outline="#ded2c6", width=6)
    draw.ellipse([plate[0] + 26, plate[1] + 24, plate[2] - 26, plate[3] - 24], fill="#eee5da")
    food = [plate[0] + 92, plate[1] + 86, plate[2] - 92, plate[3] - 72]
    draw.ellipse(food, fill="#d86a43")
    noodle_colors = ["#f0c36d", "#e8b45c", "#f5cf82"]
    noodle_arcs = [
        ([food[0] + 28, food[1] + 26, food[0] + 200, food[1] + 164], 205, 10, 20),
        ([food[0] + 140, food[1] + 16, food[0] + 348, food[1] + 178], 170, 350, 22),
        ([food[0] + 280, food[1] + 20, food[0] + 500, food[1] + 186], 185, 20, 22),
        ([food[0] + 54, food[1] + 108, food[0] + 260, food[1] + 248], 160, 350, 18),
        ([food[0] + 226, food[1] + 92, food[0] + 452, food[1] + 250], 200, 25, 20),
        ([food[0] + 120, food[1] + 150, food[0] + 362, food[1] + 292], 185, 18, 20),
    ]
    for index, (bbox, start, end, width_px) in enumerate(noodle_arcs):
        draw.arc(bbox, start=start, end=end, fill=noodle_colors[index % len(noodle_colors)], width=width_px)
    for bx, by, radius in [(food[0] + 124, food[1] + 118, 30), (food[0] + 230, food[1] + 58, 34), (food[0] + 378, food[1] + 126, 30)]:
        draw.ellipse([bx - radius, by - radius, bx + radius, by + radius], fill="#f3dcc1")
        draw.ellipse([bx - radius + 10, by - radius + 10, bx + radius - 10, by + radius - 8], fill="#fff4e7")
    for herb in [
        [food[0] + 124, food[1] + 42, food[0] + 204, food[1] + 102],
        [food[0] + 352, food[1] + 72, food[0] + 432, food[1] + 132],
        [food[0] + 236, food[1] + 150, food[0] + 316, food[1] + 214],
    ]:
        draw.ellipse(herb, fill="#5f8353", outline="#49653f", width=2)
        mid_y = (herb[1] + herb[3]) // 2
        draw.line([herb[0] + 12, mid_y, herb[2] - 12, mid_y], fill="#dcead4", width=2)
    chili = [food[0] + 430, food[1] + 26, food[0] + 492, food[1] + 74]
    draw.arc(chili, start=170, end=350, fill="#a2271b", width=10)
    draw.arc([plate[0] + 40, plate[1] + 32, plate[2] - 40, plate[3] - 34], start=210, end=330, fill="#ffffff", width=8)


def draw_stew_bowl(overlay: Image.Image, cx: int, cy: int, width: int, height: int) -> None:
    draw = ImageDraw.Draw(overlay)
    blurred_ellipse(overlay, [cx - width // 2 + 22, cy - height // 2 + 30, cx + width // 2 + 22, cy + height // 2 + 38], (0, 0, 0, 74), 28)
    bowl = [cx - width // 2, cy - height // 2, cx + width // 2, cy + height // 2]
    draw.ellipse(bowl, fill="#f3ede6", outline="#d7cbc0", width=5)
    fill = [bowl[0] + 26, bowl[1] + 28, bowl[2] - 26, bowl[3] - 26]
    draw.ellipse(fill, fill="#ba6b43")
    chunks = [
        ([fill[0] + 44, fill[1] + 58, fill[0] + 128, fill[1] + 134], "#8c563a"),
        ([fill[0] + 122, fill[1] + 78, fill[0] + 218, fill[1] + 154], "#744731"),
        ([fill[0] + 210, fill[1] + 54, fill[0] + 306, fill[1] + 132], "#8e5e3c"),
        ([fill[0] + 308, fill[1] + 80, fill[0] + 384, fill[1] + 150], "#775241"),
    ]
    for bbox, color in chunks:
        draw.rounded_rectangle(bbox, radius=18, fill=color)
    draw.arc([fill[0] + 56, fill[1] + 20, fill[2] - 40, fill[3] - 46], start=180, end=330, fill="#f2d3b6", width=10)
    for herb in [(fill[0] + 110, fill[1] + 30), (fill[0] + 300, fill[1] + 50), (fill[0] + 210, fill[1] + 118)]:
        hx, hy = herb
        draw.ellipse([hx - 20, hy - 12, hx + 20, hy + 12], fill="#648554")
        draw.ellipse([hx - 10, hy - 20, hx + 30, hy + 4], fill="#6f9160")
    draw.arc([bowl[0] + 28, bowl[1] + 26, bowl[2] - 28, bowl[3] - 32], start=210, end=335, fill="#ffffff", width=6)


def draw_bread_board(overlay: Image.Image, x: int, y: int, width: int, height: int) -> None:
    draw = ImageDraw.Draw(overlay)
    blurred_roundrect(overlay, [x + 18, y + 22, x + width + 18, y + height + 22], 44, (0, 0, 0, 78), 26)
    draw.rounded_rectangle([x, y, x + width, y + height], radius=44, fill="#8f664d", outline="#6f4d39", width=4)
    draw.rounded_rectangle([x + 54, y + 56, x + width - 54, y + height - 54], radius=28, outline="#ad8266", width=4)
    slices = [
        [x + 96, y + 90, x + 244, y + 228],
        [x + 208, y + 108, x + 364, y + 252],
        [x + 328, y + 124, x + 478, y + 262],
    ]
    for index, slice_box in enumerate(slices):
        dx = index * 4
        blurred_roundrect(overlay, [slice_box[0] + 10, slice_box[1] + 12, slice_box[2] + 10, slice_box[3] + 12], 24, (0, 0, 0, 42), 12)
        draw.rounded_rectangle([slice_box[0] + dx, slice_box[1], slice_box[2] + dx, slice_box[3]], radius=24, fill="#efd0a0", outline="#b87d48", width=4)
        draw.rounded_rectangle([slice_box[0] + 26 + dx, slice_box[1] + 26, slice_box[2] - 24 + dx, slice_box[3] - 22], radius=16, fill="#f7e4c2")
    draw.rounded_rectangle([x + 276, y + 162, x + 364, y + 222], radius=16, fill="#f3d872", outline="#d5b958", width=3)
    draw.arc([x + 42, y + 32, x + width - 42, y + height - 26], start=210, end=320, fill="#c79c79", width=6)


def draw_cover_cutlery(overlay: Image.Image, x: int, y: int, length: int) -> None:
    draw = ImageDraw.Draw(overlay)
    draw.line([x, y, x + length, y + 68], fill="#cdc7c2", width=18)
    draw.line([x + 32, y + 12, x + length + 32, y + 80], fill="#f3f0ec", width=7)
    draw.ellipse([x - 54, y - 36, x + 34, y + 48], fill="#ddd7d1", outline="#bdb5ae", width=3)
    for tine_offset in [0, 16, 32, 48]:
        draw.line([x + length - 12 + tine_offset, y + 44, x + length - 2 + tine_offset, y - 18], fill="#e9e5df", width=5)


def draw_cover_illustration(base: Image.Image) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    art_box = [70, 70, A4_W - 70, A4_H - 70]
    blurred_roundrect(overlay, [art_box[0] + 16, art_box[1] + 20, art_box[2] + 16, art_box[3] + 20], 62, (0, 0, 0, 80), 30)
    art_w = art_box[2] - art_box[0]
    art_h = art_box[3] - art_box[1]
    art_bg = vertical_gradient(art_w, art_h, "#6e4a39", "#241915")
    overlay.paste(art_bg.convert("RGBA"), (art_box[0], art_box[1]))
    draw.rounded_rectangle(art_box, radius=62, outline="#cdb39f", width=3)

    vignette_top = Image.new("RGBA", base.size, (0, 0, 0, 0))
    vignette_draw = ImageDraw.Draw(vignette_top)
    vignette_draw.ellipse([art_box[0] - 180, art_box[1] - 260, art_box[2] + 180, art_box[1] + 760], fill=(255, 214, 170, 30))
    vignette_draw.ellipse([art_box[0] - 120, art_box[1] + 740, art_box[2] + 180, art_box[3] + 240], fill=(0, 0, 0, 80))
    vignette_top = vignette_top.filter(ImageFilter.GaussianBlur(80))
    overlay.alpha_composite(vignette_top)

    table_top = art_box[1] + int(art_h * 0.54)
    draw.rectangle([art_box[0], table_top, art_box[2], art_box[3]], fill="#6b4735")
    for offset in range(0, art_w, 180):
        draw.line([art_box[0] + offset, table_top + 18, art_box[0] + offset + 160, art_box[3]], fill="#5b3c2e", width=10)
        draw.line([art_box[0] + offset + 80, table_top + 8, art_box[0] + offset + 210, art_box[3]], fill="#7b5640", width=6)

    cloth = [
        (art_box[0] + 160, table_top - 20),
        (art_box[0] + 720, table_top + 10),
        (art_box[0] + 1120, art_box[3] - 60),
        (art_box[0] + 540, art_box[3] - 10),
        (art_box[0] + 120, art_box[3] - 180),
    ]
    draw.polygon(cloth, fill="#d7dbd4")
    draw.line([cloth[0], cloth[2]], fill="#bcc4bd", width=5)
    draw.line([cloth[1], cloth[4]], fill="#bcc4bd", width=4)
    draw.line([art_box[0] + 238, table_top + 86, art_box[0] + 902, art_box[3] - 92], fill="#eef2ec", width=10)

    draw_salad_bowl(overlay, art_box[0] + 520, table_top + 150, 620, 310)
    draw_stew_bowl(overlay, art_box[2] - 410, art_box[1] + 960, 700, 360)
    draw_pasta_plate(overlay, art_box[0] + 1120, table_top + 120, 980, 470)
    draw_bread_board(overlay, art_box[2] - 700, art_box[3] - 520, 640, 350)
    draw_cover_cutlery(overlay, art_box[0] + 360, art_box[3] - 470, 420)

    for herb in [(art_box[2] - 820, table_top + 350), (art_box[2] - 760, table_top + 390), (art_box[0] + 980, art_box[3] - 270)]:
        hx, hy = herb
        draw.ellipse([hx - 24, hy - 12, hx + 24, hy + 12], fill="#6f8f5d")
        draw.ellipse([hx - 8, hy - 26, hx + 26, hy + 6], fill="#5f8353")
    for flake in [(art_box[0] + 1240, table_top + 70), (art_box[0] + 1310, table_top + 128), (art_box[0] + 1180, table_top + 182)]:
        fx, fy = flake
        draw.ellipse([fx - 10, fy - 6, fx + 10, fy + 6], fill="#f4ddbe")

    merged = Image.alpha_composite(base.convert("RGBA"), overlay)
    base.paste(merged.convert("RGB"))


def draw_recipe_page(recipe: Recipe, per_100: dict, kcal_per_portion: float, macro_pct: dict, page_number: int) -> Image.Image:
    style = SECTION_STYLES[recipe.section]
    panel = Image.new("RGB", (A4_W, A4_H), "#fcfaf7")
    draw = ImageDraw.Draw(panel)
    fonts = recipe_fonts()
    ingredient_entries, method_entries = recipe_component_entries(recipe)

    draw.rounded_rectangle(
        [28, 28, A4_W - 28, A4_H - 28],
        radius=34,
        outline=style.soft,
        width=3,
        fill="#fffdf9",
    )
    draw_pattern(draw, style)
    left_x = INNER_MARGIN
    section_font = fonts["section"]
    title_font = fonts["title"]
    chip_font = fonts["chip"]
    body_font = fonts["body"]
    body_bold = fonts["body_bold"]
    body_line = fonts["body_line"]

    header_top = OUTER_MARGIN + 18
    tag_y = header_top + 26
    title_box_width = A4_W - 2 * INNER_MARGIN - 48
    title_lines = wrap_text(draw, recipe.title, title_font, title_box_width)
    tag_height = tag_size(draw, section_label(recipe.section), section_font)[1]
    chip_height = tag_size(draw, f"{recipe.servings} portioner", chip_font)[1]

    title_start_y = tag_y + tag_height + 28
    title_bottom_y = title_start_y + len(title_lines) * fonts["title_line"]
    chip_y = title_bottom_y + 24
    header_bottom = chip_y + chip_height + 34

    draw.rounded_rectangle(
        [OUTER_MARGIN, header_top, A4_W - OUTER_MARGIN, header_bottom],
        radius=40,
        fill=style.panel,
        outline=style.soft,
        width=2,
    )

    section_text = section_label(recipe.section)
    draw_tag(draw, (left_x, tag_y), section_text, section_font, style.accent, "#fffdf9")
    top_tag_x = left_x + tag_size(draw, section_text, section_font)[0] + 16
    for extra_tag in recipe.tags:
        draw_tag(draw, (top_tag_x, tag_y), extra_tag, section_font, style.soft, style.ink)
        top_tag_x += tag_size(draw, extra_tag, section_font)[0] + 16

    title_y = title_start_y
    for line in title_lines:
        draw.text((left_x, title_y), line, font=title_font, fill=style.ink)
        title_y += fonts["title_line"]

    chip_gap = 20
    chip_texts = [
        f"{recipe.servings} portioner",
        f"{round(kcal_per_portion)} kcal/portion",
        f"{round(per_100['kcal'])} kcal/100 g",
    ]
    chip_x = left_x
    for chip_text in chip_texts:
        draw_tag(draw, (chip_x, chip_y), chip_text, chip_font, style.soft, style.ink)
        chip_x += tag_size(draw, chip_text, chip_font)[0] + chip_gap

    column_gap = 60
    content_x = INNER_MARGIN
    content_w = A4_W - 2 * INNER_MARGIN
    ingredients_w = int(content_w * 0.38)
    method_w = content_w - ingredients_w - column_gap
    ingredients_x = content_x
    method_x = ingredients_x + ingredients_w + column_gap
    body_y = header_bottom + 40
    footer_top = A4_H - 480
    body_bottom = footer_top - 44

    left_content_h, right_content_h = measure_recipe_columns(
        ingredient_entries,
        method_entries,
        draw,
        ingredients_w - 56,
        method_w - 56,
        body_font,
        body_bold,
        body_line,
    )
    available_h = body_bottom - (body_y + 120) - 24
    required_h = max(left_content_h, right_content_h)
    if required_h > available_h:
        raise RuntimeError(
            f"Opskriften '{recipe.title}' passer ikke med den faste typografi. "
            f"Kræver {required_h}px, har {available_h}px."
        )

    draw.rounded_rectangle(
        [ingredients_x, body_y, ingredients_x + ingredients_w, body_bottom],
        radius=24,
        fill="#fff7ef",
        outline=style.soft,
        width=2,
    )
    draw.rounded_rectangle(
        [method_x, body_y, method_x + method_w, body_bottom],
        radius=24,
        fill="#ffffff",
        outline=style.soft,
        width=2,
    )

    draw.text((ingredients_x + 28, body_y + 33), "Ingredienser", font=body_bold, fill=style.ink)
    draw.text((method_x + 28, body_y + 33), "Fremgangsmåde", font=body_bold, fill=style.ink)
    draw.line(
        [ingredients_x + 28, body_y + 96, ingredients_x + ingredients_w - 28, body_y + 96],
        fill=style.soft,
        width=2,
    )
    draw.line(
        [method_x + 28, body_y + 96, method_x + method_w - 28, body_y + 96],
        fill=style.soft,
        width=2,
    )

    cursor_left = body_y + 120
    for ingredient in ingredient_entries:
        if is_component_entry(ingredient):
            cursor_left += int(body_line * COMPONENT_TOP_GAP)
            cursor_left = draw_text_block(
                draw,
                ingredients_x + 28,
                cursor_left,
                ingredients_w - 56,
                component_name(ingredient),
                body_bold,
                style.accent,
                body_line,
            )
            cursor_left += int(body_line * COMPONENT_BOTTOM_GAP)
        else:
            cursor_left = draw_text_block(
                draw,
                ingredients_x + 28,
                cursor_left,
                ingredients_w - 56,
                f"• {ingredient}",
                body_font,
                "#2d2a26",
                body_line,
            )

    cursor_right = body_y + 120
    step_number = 1
    for step in method_entries:
        if is_component_entry(step):
            step_number = 1
            cursor_right += int(body_line * COMPONENT_TOP_GAP)
            cursor_right = draw_text_block(
                draw,
                method_x + 28,
                cursor_right,
                method_w - 56,
                component_name(step),
                body_bold,
                style.accent,
                body_line,
            )
            cursor_right += int(body_line * COMPONENT_BOTTOM_GAP)
        else:
            cursor_right = draw_text_block(
                draw,
                method_x + 28,
                cursor_right,
                method_w - 56,
                f"{step_number}. {step}",
                body_font,
                "#2d2a26",
                body_line,
            )
            cursor_right += int(body_line * 0.15)
            step_number += 1

    draw.rounded_rectangle(
        [INNER_MARGIN, footer_top, A4_W - INNER_MARGIN, A4_H - 110],
        radius=28,
        fill=style.ink,
    )
    draw.text((INNER_MARGIN + 32, footer_top + 26), "Næringsestimat", font=body_bold, fill="#fffdf9")
    nutrition_x = INNER_MARGIN + 32
    nutrition_y = footer_top + 76
    nutrition_width = A4_W - 2 * INNER_MARGIN - 64
    nutrition_lines = [
        f"Energi pr. 100 g: {round(per_100['kcal'])} kcal",
        f"Energi pr. portion: {round(kcal_per_portion)} kcal",
        (
            f"Næringsstoffer pr. 100 g: Protein {per_100['protein']:.1f} g  "
            f"Kulhydrat {per_100['carbs']:.1f} g  "
            f"Fedt {per_100['fat']:.1f} g"
        ),
        (
            f"Fordeling af energi: Protein {macro_pct['protein']:.0f} %  "
            f"Kulhydrat {macro_pct['carbs']:.0f} %  "
            f"Fedt {macro_pct['fat']:.0f} %"
        ),
    ]
    for line in nutrition_lines:
        nutrition_y = draw_text_block(
            draw,
            nutrition_x,
            nutrition_y,
            nutrition_width,
            line,
            body_font,
            "#fffdf9",
            body_line,
        )

    page_font = load_font(30, "sans")
    page_text = f"side {page_number}"
    bbox = draw.textbbox((0, 0), page_text, font=page_font)
    draw.text((A4_W - INNER_MARGIN - (bbox[2] - bbox[0]), A4_H - 84), page_text, font=page_font, fill="#857a6c")
    return panel


def draw_cover(version: int, build_date_text: str) -> Image.Image:
    photo = Image.open(COVER_IMAGE_PATH).convert("RGB")
    fitted = ImageOps.fit(photo, (A4_W - 56, A4_H - 56), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    panel = Image.new("RGB", (A4_W, A4_H), "#f7f2ea")
    panel.paste(fitted, (28, 28))
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A4_W - 28, A4_H - 28], radius=42, outline="#efe5d9", width=4)
    return panel


def draw_contents(ordered: List[Recipe], page_map: Dict[str, int]) -> Image.Image:
    panel = Image.new("RGB", (A4_W, A4_H), "#fcfaf7")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A4_W - 28, A4_H - 28], radius=34, outline="#ddd3c8", width=3, fill="#fffdf9")

    title_font = load_font(96, "display")
    section_font = load_font(38, "sans-bold")
    body_font = load_font(RECIPE_BODY_SIZE, "sans")
    small_font = load_font(30, "sans")
    row_height = line_height(RECIPE_BODY_SIZE, 1.18)
    separator_y = int(row_height * 0.82)

    draw.text((INNER_MARGIN, 140), "Indhold", font=title_font, fill="#2b241f")
    draw.text((INNER_MARGIN, 260), "Opskrifter", font=small_font, fill="#756a5f")

    y = 380
    current_section = None
    for recipe in ordered:
        if recipe.section != current_section:
            if current_section is not None:
                y += 28
            current_section = recipe.section
            style = SECTION_STYLES[current_section]
            draw.rounded_rectangle([INNER_MARGIN, y, A4_W - INNER_MARGIN, y + 64], radius=18, fill=style.panel)
            draw.text((INNER_MARGIN + 18, y + 12), current_section, font=section_font, fill=style.ink)
            y += 92

        draw.text((INNER_MARGIN + 10, y), recipe.title, font=body_font, fill="#2d2a26")
        number_text = str(page_map[recipe.title])
        bbox = draw.textbbox((0, 0), number_text, font=body_font)
        number_x = A4_W - INNER_MARGIN - (bbox[2] - bbox[0])
        draw.text((number_x, y), number_text, font=body_font, fill="#7f7266")
        draw.line([INNER_MARGIN + 10, y + separator_y, A4_W - INNER_MARGIN, y + separator_y], fill="#ece4da", width=1)
        y += row_height

    draw.text((A4_W - 200, A4_H - 84), "side 2", font=small_font, fill="#857a6c")
    return panel


def draw_raw_table_page(keys: List[str], page_number: int, start_index: int) -> Tuple[Image.Image, int]:
    panel = Image.new("RGB", (A4_W, A4_H), "#fbfaf8")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A4_W - 28, A4_H - 28], radius=34, outline="#d6dbe0", width=3, fill="#fffdf9")

    title_font = load_font(84, "display")
    header_font = load_font(34, "sans-bold")
    row_font = load_font(34, "sans")
    small_font = load_font(30, "sans")

    draw.text((INNER_MARGIN, 130), "Råvarer og energi", font=title_font, fill="#24313c")
    draw.text((INNER_MARGIN, 230), "Energiindhold pr. 100 g for de råvarer, der indgår i hæftet.", font=small_font, fill="#66727d")

    col1_x = INNER_MARGIN
    col2_x = 1300
    top = 360
    draw.text((col1_x, top), "Råvare", font=header_font, fill="#24313c")
    draw.text((col1_x + 700, top), "kcal", font=header_font, fill="#24313c")
    draw.text((col2_x, top), "Råvare", font=header_font, fill="#24313c")
    draw.text((col2_x + 700, top), "kcal", font=header_font, fill="#24313c")
    top += 60
    draw.line([col1_x, top, A4_W - INNER_MARGIN, top], fill="#cfd6dc", width=2)
    top += 28

    row_h = 54
    left_y = top
    right_y = top
    index = start_index

    while index < len(keys):
        target_x = col1_x if left_y <= right_y else col2_x
        target_y = left_y if left_y <= right_y else right_y
        if target_y + row_h > A4_H - 150:
            if target_x == col1_x and right_y <= left_y:
                target_x = col2_x
                target_y = right_y
            else:
                break

        key = keys[index]
        draw.text((target_x, target_y), DISPLAY_NAMES.get(key, key), font=row_font, fill="#2d2a26")
        draw.text((target_x + 700, target_y), str(round(NDB[key].kcal)), font=row_font, fill="#2d2a26")
        if target_x == col1_x:
            left_y += row_h
        else:
            right_y += row_h
        index += 1

    draw.text((A4_W - 200, A4_H - 84), f"side {page_number}", font=small_font, fill="#857a6c")
    return panel, index


def draw_back_cover() -> Image.Image:
    panel = Image.new("RGB", (A4_W, A4_H), "#f2f5f8")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A4_W - 28, A4_H - 28], radius=34, outline="#cfd7df", width=3, fill="#f7fafc")

    title_font = load_font(90, "display")
    body_font = load_font(40, "sans")
    small_font = load_font(30, "sans")

    draw.text((INNER_MARGIN, 320), "Kogebogen er sat op", font=title_font, fill="#223241")
    draw.text((INNER_MARGIN, 430), "til print, hæftning og køkkenbrug.", font=title_font, fill="#223241")

    draw.rounded_rectangle([INNER_MARGIN, 750, A4_W - INNER_MARGIN, 1200], radius=26, fill="#e8eef4")
    draw.text((INNER_MARGIN + 36, 810), "Format", font=body_font, fill="#223241")
    draw.text((INNER_MARGIN + 36, 870), "A4 portræt med 1 opskrift pr. side", font=body_font, fill="#4f6376")
    draw.text((INNER_MARGIN + 36, 990), "Udtryk", font=body_font, fill="#223241")
    draw.text((INNER_MARGIN + 36, 1050), "Renskrevet, standardiseret og ernæringsberegnet", font=body_font, fill="#4f6376")

    draw.text(
        (INNER_MARGIN, A4_H - 150),
        "Dannet med hjælp fra AI: OpenAI GPT-5, Codex-agent.",
        font=small_font,
        fill="#6c7a88",
    )
    return panel


def blank_page() -> Image.Image:
    panel = Image.new("RGB", (A4_W, A4_H), "#fffdf9")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A4_W - 28, A4_H - 28], radius=34, outline="#ece5dc", width=2, fill="#fffdf9")
    return panel


def pdf_draw_pattern(canvas, style: SectionStyle) -> None:
    pdf_ellipse(canvas, A4_W - 520, -120, A4_W - 40, 360, stroke=style.soft, stroke_width=4)
    pdf_ellipse(canvas, A4_W - 440, -40, A4_W + 80, 480, stroke=style.soft, stroke_width=2)
    pdf_ellipse(canvas, 60, A4_H - 400, 420, A4_H - 40, stroke=style.soft, stroke_width=3)
    pdf_line(canvas, OUTER_MARGIN, 160, A4_W - OUTER_MARGIN, 160, style.soft, 3)


def draw_cover_pdf(canvas, version: int, build_date_text: str, fonts: Dict[str, str]) -> None:
    del fonts
    cover = draw_cover(version, build_date_text)
    cover_buffer = io.BytesIO()
    cover.save(cover_buffer, format="JPEG", quality=88, optimize=True, progressive=True)
    cover_buffer.seek(0)
    canvas.drawImage(ImageReader(cover_buffer), 0, 0, width=PDF_W, height=PDF_H, preserveAspectRatio=False, mask="auto")


def draw_contents_pdf(canvas, ordered: List[Recipe], page_map: Dict[str, int], fonts: Dict[str, str]) -> None:
    pdf_round_rect(canvas, 28, 28, A4_W - 56, A4_H - 56, 34, "#fffdf9", "#ddd3c8", 3)
    row_height = line_height(RECIPE_BODY_SIZE, 1.18)
    separator_y = int(row_height * 0.82)

    pdf_draw_text(canvas, INNER_MARGIN, 140, "Indhold", fonts["display"], 96, "#2b241f")
    pdf_draw_text(canvas, INNER_MARGIN, 260, "Opskrifter", fonts["sans"], 30, "#756a5f")

    y = 380
    current_section = None
    for recipe in ordered:
        if recipe.section != current_section:
            if current_section is not None:
                y += 28
            current_section = recipe.section
            style = SECTION_STYLES[current_section]
            pdf_round_rect(canvas, INNER_MARGIN, y, A4_W - 2 * INNER_MARGIN, 64, 18, style.panel)
            pdf_draw_text(canvas, INNER_MARGIN + 18, y + 12, current_section, fonts["sans-bold"], 38, style.ink)
            y += 92

        pdf_draw_text(canvas, INNER_MARGIN + 10, y, recipe.title, fonts["sans"], RECIPE_BODY_SIZE, "#2d2a26")
        number_text = str(page_map[recipe.title])
        number_x = A4_W - INNER_MARGIN - int(round(pdf_text_width(number_text, fonts["sans"], RECIPE_BODY_SIZE)))
        pdf_draw_text(canvas, number_x, y, number_text, fonts["sans"], RECIPE_BODY_SIZE, "#7f7266")
        pdf_line(canvas, INNER_MARGIN + 10, y + separator_y, A4_W - INNER_MARGIN, y + separator_y, "#ece4da", 1)
        y += row_height

    pdf_draw_text(canvas, A4_W - 200, A4_H - 84, "side 2", fonts["sans"], 30, "#857a6c")


def draw_raw_table_page_pdf(canvas, keys: List[str], page_number: int, start_index: int, fonts: Dict[str, str]) -> int:
    pdf_round_rect(canvas, 28, 28, A4_W - 56, A4_H - 56, 34, "#fffdf9", "#d6dbe0", 3)

    pdf_draw_text(canvas, INNER_MARGIN, 130, "Råvarer og energi", fonts["display"], 84, "#24313c")
    pdf_draw_text(canvas, INNER_MARGIN, 230, "Energiindhold pr. 100 g for de råvarer, der indgår i hæftet.", fonts["sans"], 30, "#66727d")

    col1_x = INNER_MARGIN
    col2_x = 1300
    top = 360
    pdf_draw_text(canvas, col1_x, top, "Råvare", fonts["sans-bold"], 34, "#24313c")
    pdf_draw_text(canvas, col1_x + 700, top, "kcal", fonts["sans-bold"], 34, "#24313c")
    pdf_draw_text(canvas, col2_x, top, "Råvare", fonts["sans-bold"], 34, "#24313c")
    pdf_draw_text(canvas, col2_x + 700, top, "kcal", fonts["sans-bold"], 34, "#24313c")
    top += 60
    pdf_line(canvas, col1_x, top, A4_W - INNER_MARGIN, top, "#cfd6dc", 2)
    top += 28

    row_h = 54
    left_y = top
    right_y = top
    index = start_index
    while index < len(keys):
        target_x = col1_x if left_y <= right_y else col2_x
        target_y = left_y if left_y <= right_y else right_y
        if target_y + row_h > A4_H - 150:
            if target_x == col1_x and right_y <= left_y:
                target_x = col2_x
                target_y = right_y
            else:
                break
        key = keys[index]
        pdf_draw_text(canvas, target_x, target_y, DISPLAY_NAMES.get(key, key), fonts["sans"], 34, "#2d2a26")
        pdf_draw_text(canvas, target_x + 700, target_y, str(round(NDB[key].kcal)), fonts["sans"], 34, "#2d2a26")
        if target_x == col1_x:
            left_y += row_h
        else:
            right_y += row_h
        index += 1

    pdf_draw_text(canvas, A4_W - 200, A4_H - 84, f"side {page_number}", fonts["sans"], 30, "#857a6c")
    return index


def draw_back_cover_pdf(canvas, fonts: Dict[str, str]) -> None:
    pdf_round_rect(canvas, 0, 0, A4_W, A4_H, 0, "#f2f5f8")
    pdf_round_rect(canvas, 28, 28, A4_W - 56, A4_H - 56, 34, "#f7fafc", "#cfd7df", 3)

    pdf_draw_text(canvas, INNER_MARGIN, 320, "Kogebogen er sat op", fonts["display"], 90, "#223241")
    pdf_draw_text(canvas, INNER_MARGIN, 430, "til print, hæftning og køkkenbrug.", fonts["display"], 90, "#223241")

    pdf_round_rect(canvas, INNER_MARGIN, 750, A4_W - 2 * INNER_MARGIN, 450, 26, "#e8eef4")
    pdf_draw_text(canvas, INNER_MARGIN + 36, 810, "Format", fonts["sans"], 40, "#223241")
    pdf_draw_text(canvas, INNER_MARGIN + 36, 870, "A4 portræt med 1 opskrift pr. side", fonts["sans"], 40, "#4f6376")
    pdf_draw_text(canvas, INNER_MARGIN + 36, 990, "Udtryk", fonts["sans"], 40, "#223241")
    pdf_draw_text(canvas, INNER_MARGIN + 36, 1050, "Renskrevet, standardiseret og ernæringsberegnet", fonts["sans"], 40, "#4f6376")
    pdf_draw_text(canvas, INNER_MARGIN, A4_H - 150, "Dannet med hjælp fra AI: OpenAI GPT-5, Codex-agent.", fonts["sans"], 30, "#6c7a88")


def draw_blank_page_pdf(canvas) -> None:
    pdf_round_rect(canvas, 0, 0, A4_W, A4_H, 0, "#fffdf9")
    pdf_round_rect(canvas, 28, 28, A4_W - 56, A4_H - 56, 34, "#fffdf9", "#ece5dc", 2)


def draw_recipe_page_pdf(
    canvas,
    recipe: Recipe,
    per_100: dict,
    kcal_per_portion: float,
    macro_pct: dict,
    page_number: int,
    fonts: Dict[str, str],
) -> None:
    style = SECTION_STYLES[recipe.section]
    ingredient_entries, method_entries = recipe_component_entries(recipe)

    pdf_round_rect(canvas, 28, 28, A4_W - 56, A4_H - 56, 34, "#fffdf9", style.soft, 3)
    pdf_draw_pattern(canvas, style)
    left_x = INNER_MARGIN
    body_line = line_height(RECIPE_BODY_SIZE, 1.28)

    header_top = OUTER_MARGIN + 18
    tag_y = header_top + 26
    title_box_width = A4_W - 2 * INNER_MARGIN - 48
    title_lines = pdf_wrap_text(recipe.title, fonts["display"], RECIPE_TITLE_SIZE, title_box_width)
    tag_height = pdf_tag_size(section_label(recipe.section), fonts["sans-bold"], RECIPE_SECTION_SIZE)[1]
    chip_height = pdf_tag_size(f"{recipe.servings} portioner", fonts["sans-bold"], RECIPE_CHIP_SIZE)[1]

    title_start_y = tag_y + tag_height + 28
    title_bottom_y = title_start_y + len(title_lines) * line_height(RECIPE_TITLE_SIZE, 1.05)
    chip_y = title_bottom_y + 24
    header_bottom = chip_y + chip_height + 34

    pdf_round_rect(canvas, OUTER_MARGIN, header_top, A4_W - 2 * OUTER_MARGIN, header_bottom - header_top, 40, style.panel, style.soft, 2)

    section_text = section_label(recipe.section)
    top_tag_x = left_x
    top_tag_x += pdf_tag(canvas, top_tag_x, tag_y, section_text, fonts["sans-bold"], RECIPE_SECTION_SIZE, style.accent, "#fffdf9") + 16
    for extra_tag in recipe.tags:
        top_tag_x += pdf_tag(canvas, top_tag_x, tag_y, extra_tag, fonts["sans-bold"], RECIPE_SECTION_SIZE, style.soft, style.ink) + 16

    title_y = title_start_y
    for line in title_lines:
        pdf_draw_text(canvas, left_x, title_y, line, fonts["display"], RECIPE_TITLE_SIZE, style.ink)
        title_y += line_height(RECIPE_TITLE_SIZE, 1.05)

    chip_gap = 20
    chip_texts = [
        f"{recipe.servings} portioner",
        f"{round(kcal_per_portion)} kcal/portion",
        f"{round(per_100['kcal'])} kcal/100 g",
    ]
    chip_x = left_x
    for chip_text in chip_texts:
        chip_x += pdf_tag(canvas, chip_x, chip_y, chip_text, fonts["sans-bold"], RECIPE_CHIP_SIZE, style.soft, style.ink) + chip_gap

    column_gap = 60
    content_w = A4_W - 2 * INNER_MARGIN
    ingredients_w = int(content_w * 0.38)
    method_w = content_w - ingredients_w - column_gap
    ingredients_x = INNER_MARGIN
    method_x = ingredients_x + ingredients_w + column_gap
    body_y = header_bottom + 40
    footer_top = A4_H - 480
    body_bottom = footer_top - 44

    left_content_h, right_content_h = pdf_measure_recipe_columns(
        ingredient_entries,
        method_entries,
        ingredients_w - 56,
        method_w - 56,
        fonts["sans"],
        fonts["sans-bold"],
        body_line,
    )
    available_h = body_bottom - (body_y + 120) - 24
    required_h = max(left_content_h, right_content_h)
    if required_h > available_h:
        raise RuntimeError(
            f"Opskriften '{recipe.title}' passer ikke med den faste typografi. "
            f"Kræver {required_h}px, har {available_h}px."
        )

    pdf_round_rect(canvas, ingredients_x, body_y, ingredients_w, body_bottom - body_y, 24, "#fff7ef", style.soft, 2)
    pdf_round_rect(canvas, method_x, body_y, method_w, body_bottom - body_y, 24, "#ffffff", style.soft, 2)
    pdf_draw_text(canvas, ingredients_x + 28, body_y + 33, "Ingredienser", fonts["sans-bold"], RECIPE_BODY_BOLD_SIZE, style.ink)
    pdf_draw_text(canvas, method_x + 28, body_y + 33, "Fremgangsmåde", fonts["sans-bold"], RECIPE_BODY_BOLD_SIZE, style.ink)
    pdf_line(canvas, ingredients_x + 28, body_y + 96, ingredients_x + ingredients_w - 28, body_y + 96, style.soft, 2)
    pdf_line(canvas, method_x + 28, body_y + 96, method_x + method_w - 28, body_y + 96, style.soft, 2)

    cursor_left = body_y + 120
    for ingredient in ingredient_entries:
        if is_component_entry(ingredient):
            cursor_left += int(body_line * COMPONENT_TOP_GAP)
            cursor_left = pdf_draw_text_block(
                canvas,
                ingredients_x + 28,
                cursor_left,
                ingredients_w - 56,
                component_name(ingredient),
                fonts["sans-bold"],
                RECIPE_BODY_BOLD_SIZE,
                style.accent,
                body_line,
            )
            cursor_left += int(body_line * COMPONENT_BOTTOM_GAP)
        else:
            cursor_left = pdf_draw_text_block(
                canvas,
                ingredients_x + 28,
                cursor_left,
                ingredients_w - 56,
                f"• {ingredient}",
                fonts["sans"],
                RECIPE_BODY_SIZE,
                "#2d2a26",
                body_line,
            )

    cursor_right = body_y + 120
    step_number = 1
    for step in method_entries:
        if is_component_entry(step):
            step_number = 1
            cursor_right += int(body_line * COMPONENT_TOP_GAP)
            cursor_right = pdf_draw_text_block(
                canvas,
                method_x + 28,
                cursor_right,
                method_w - 56,
                component_name(step),
                fonts["sans-bold"],
                RECIPE_BODY_BOLD_SIZE,
                style.accent,
                body_line,
            )
            cursor_right += int(body_line * COMPONENT_BOTTOM_GAP)
        else:
            cursor_right = pdf_draw_text_block(
                canvas,
                method_x + 28,
                cursor_right,
                method_w - 56,
                f"{step_number}. {step}",
                fonts["sans"],
                RECIPE_BODY_SIZE,
                "#2d2a26",
                body_line,
            )
            cursor_right += int(body_line * 0.15)
            step_number += 1

    pdf_round_rect(canvas, INNER_MARGIN, footer_top, A4_W - 2 * INNER_MARGIN, A4_H - 110 - footer_top, 28, style.ink)
    pdf_draw_text(canvas, INNER_MARGIN + 32, footer_top + 26, "Næringsestimat", fonts["sans-bold"], RECIPE_BODY_BOLD_SIZE, "#fffdf9")
    nutrition_x = INNER_MARGIN + 32
    nutrition_y = footer_top + 76
    nutrition_width = A4_W - 2 * INNER_MARGIN - 64
    nutrition_lines = [
        f"Energi pr. 100 g: {round(per_100['kcal'])} kcal",
        f"Energi pr. portion: {round(kcal_per_portion)} kcal",
        f"Næringsstoffer pr. 100 g: Protein {per_100['protein']:.1f} g  Kulhydrat {per_100['carbs']:.1f} g  Fedt {per_100['fat']:.1f} g",
        f"Fordeling af energi: Protein {macro_pct['protein']:.0f} %  Kulhydrat {macro_pct['carbs']:.0f} %  Fedt {macro_pct['fat']:.0f} %",
    ]
    for line in nutrition_lines:
        nutrition_y = pdf_draw_text_block(
            canvas,
            nutrition_x,
            nutrition_y,
            nutrition_width,
            line,
            fonts["sans"],
            RECIPE_BODY_SIZE,
            "#fffdf9",
            body_line,
        )

    pdf_draw_text(canvas, A4_W - INNER_MARGIN - 120, A4_H - 84, f"side {page_number}", fonts["sans"], 30, "#857a6c")


def build_pdf_vector(
    build_version: int,
    build_date_text: str,
    ordered: List[Recipe],
    page_map: Dict[str, int],
    nutrition_map: Dict[str, Tuple[dict, float, dict]],
    raw_keys: List[str],
) -> None:
    fonts = register_pdf_fonts()
    canvas = pdf_canvas.Canvas(str(PDF_PATH), pagesize=(PDF_W, PDF_H), pageCompression=1)
    canvas.setTitle(TITLE)
    canvas.setAuthor("GitHub Copilot CLI")

    draw_cover_pdf(canvas, build_version, build_date_text, fonts)
    canvas.showPage()

    draw_contents_pdf(canvas, ordered, page_map, fonts)
    canvas.showPage()

    for recipe in ordered:
        per_100, kcal_per_portion, macro_pct = nutrition_map[recipe.title]
        draw_recipe_page_pdf(canvas, recipe, per_100, kcal_per_portion, macro_pct, page_map[recipe.title], fonts)
        canvas.showPage()

    next_page_number = 3 + len(ordered)
    raw_index = 0
    while raw_index < len(raw_keys):
        raw_index = draw_raw_table_page_pdf(canvas, raw_keys, next_page_number, raw_index, fonts)
        canvas.showPage()
        next_page_number += 1

    draw_back_cover_pdf(canvas, fonts)
    canvas.showPage()

    total_pages = 2 + len(ordered) + (next_page_number - (3 + len(ordered))) + 1
    while total_pages % 4 != 0:
        draw_blank_page_pdf(canvas)
        canvas.showPage()
        total_pages += 1

    canvas.save()
