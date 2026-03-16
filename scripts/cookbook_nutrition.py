from __future__ import annotations

from typing import List, Tuple

from cookbook_recipe_data import NDB

def calc_nutrition(items: List[Tuple[str, float]], servings: int, finished_weight_g: float):
    totals = {"kcal": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for key, grams in items:
        nutrient = NDB[key]
        factor = grams / 100.0
        totals["kcal"] += nutrient.kcal * factor
        totals["protein"] += nutrient.protein * factor
        totals["carbs"] += nutrient.carbs * factor
        totals["fat"] += nutrient.fat * factor

    per_100 = {name: (value / finished_weight_g) * 100.0 for name, value in totals.items()}
    kcal_per_portion = totals["kcal"] / servings
    macro_kcal = {
        "protein": totals["protein"] * 4,
        "carbs": totals["carbs"] * 4,
        "fat": totals["fat"] * 9,
    }
    macro_total = sum(macro_kcal.values()) or 1
    macro_pct = {name: (value / macro_total) * 100.0 for name, value in macro_kcal.items()}
    return per_100, kcal_per_portion, macro_pct
