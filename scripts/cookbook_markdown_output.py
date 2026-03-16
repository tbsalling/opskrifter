from __future__ import annotations

import re
from typing import Dict, List, Tuple

from cookbook_models import Recipe
from cookbook_nutrition import calc_nutrition
from cookbook_recipe_data import COMPONENT_RULES, DISPLAY_NAMES, RECIPES
from cookbook_settings import COMPONENT_PREFIX, RECIPES_DIR, ROOT

def slugify(value: str) -> str:
    replacements = {
        "æ": "ae",
        "ø": "oe",
        "å": "aa",
        "Æ": "Ae",
        "Ø": "Oe",
        "Å": "Aa",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    return value

def is_component_entry(text: str) -> bool:
    return text.startswith(COMPONENT_PREFIX)


def component_name(text: str) -> str:
    return text[len(COMPONENT_PREFIX):]


def componentize_entries(entries: List[str], specs: List[Tuple[str, int, int]]) -> List[str]:
    output: List[str] = []
    for label, start, end in specs:
        output.append(f"{COMPONENT_PREFIX}{label}")
        output.extend(entries[start:end])
    return output


def recipe_component_entries(recipe: Recipe) -> Tuple[List[str], List[str]]:
    rules = COMPONENT_RULES.get(recipe.title)
    if not rules:
        return recipe.ingredients, recipe.method
    ingredient_entries = recipe.ingredients if any(is_component_entry(item) for item in recipe.ingredients) else componentize_entries(recipe.ingredients, rules["ingredients"])
    method_entries = recipe.method if any(is_component_entry(item) for item in recipe.method) else componentize_entries(recipe.method, rules["method"])
    return (
        ingredient_entries,
        method_entries,
    )


def ordered_recipes() -> List[Recipe]:
    order = ["Bagværk", "Tilbehør", "Aftensmad", "Weekend"]
    grouped = {name: [] for name in order}
    for recipe in RECIPES:
        grouped[recipe.section].append(recipe)

    result: List[Recipe] = []
    for section in order:
        result.extend(sorted(grouped[section], key=lambda item: item.title.lower()))
    return result


def render_markdown(recipe: Recipe, per_100: dict, kcal_per_portion: float, macro_pct: dict) -> str:
    ingredient_entries, method_entries = recipe_component_entries(recipe)
    lines = [
        f"# {recipe.title}",
        "",
        f"- Kategori: {recipe.section}",
        f"- Portioner: {recipe.servings}",
        "",
        "## Ingredienser",
    ]
    for item in ingredient_entries:
        if is_component_entry(item):
            lines.extend(["", f"### {component_name(item)}"])
        else:
            lines.append(f"- {item}")
    lines.extend(["", "## Fremgangsmåde"])
    step_number = 1
    for step in method_entries:
        if is_component_entry(step):
            step_number = 1
            lines.extend(["", f"### {component_name(step)}"])
        else:
            lines.append(f"{step_number}. {step}")
            step_number += 1
    lines.extend(
        [
            "",
            "## Næringsestimat",
            f"- Energi pr. 100 g: {round(per_100['kcal'])} kcal",
            f"- Energi pr. portion: {round(kcal_per_portion)} kcal",
            (
                "- Næringsstoffer pr. 100 g: "
                f"Protein {per_100['protein']:.1f} g, "
                f"Kulhydrat {per_100['carbs']:.1f} g, "
                f"Fedt {per_100['fat']:.1f} g"
            ),
            (
                "- Fordeling af energi: "
                f"Protein {macro_pct['protein']:.0f} %, "
                f"Kulhydrat {macro_pct['carbs']:.0f} %, "
                f"Fedt {macro_pct['fat']:.0f} %"
            ),
        ]
    )
    return "\n".join(lines) + "\n"

def build_markdown_and_page_map(ordered: List[Recipe]):
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    expected_paths = {RECIPES_DIR / f"{slugify(recipe.title)}.md" for recipe in ordered}

    for existing_path in RECIPES_DIR.glob("*.md"):
        if existing_path not in expected_paths:
            existing_path.unlink()

    page_map: Dict[str, int] = {}
    nutrition_map: Dict[str, Tuple[dict, float, dict]] = {}
    used_keys: List[str] = []
    page_number = 3

    for recipe in ordered:
        per_100, kcal_per_portion, macro_pct = calc_nutrition(
            recipe.nutrient_items,
            recipe.servings,
            recipe.finished_weight_g,
        )
        nutrition_map[recipe.title] = (per_100, kcal_per_portion, macro_pct)
        page_map[recipe.title] = page_number
        page_number += 1
        used_keys.extend([key for key, _grams in recipe.nutrient_items])

        markdown = render_markdown(recipe, per_100, kcal_per_portion, macro_pct)
        path = RECIPES_DIR / f"{slugify(recipe.title)}.md"
        path.write_text(markdown, encoding="utf-8")

    return page_map, nutrition_map, sorted(set(used_keys), key=lambda item: DISPLAY_NAMES.get(item, item))


def write_contents_file(ordered: List[Recipe], page_map: Dict[str, int]) -> None:
    lines = ["# Opskrifter", ""]
    current_section = None
    for recipe in ordered:
        if recipe.section != current_section:
            current_section = recipe.section
            lines.extend([f"## {current_section}", ""])
        lines.append(f"- {recipe.title} (side {page_map[recipe.title]})")
    (ROOT / "INDHOLD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
