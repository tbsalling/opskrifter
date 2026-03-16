from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass(frozen=True)
class Nutrient:
    kcal: float
    protein: float
    carbs: float
    fat: float


@dataclass(frozen=True)
class Recipe:
    section: str
    title: str
    servings: int
    finished_weight_g: float
    ingredients: List[str]
    method: List[str]
    nutrient_items: List[Tuple[str, float]]
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SectionStyle:
    ink: str
    panel: str
    accent: str
    soft: str
