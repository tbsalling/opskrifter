#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RECIPES_DIR = ROOT / "recipes"
OUTPUT_DIR = ROOT / "output"
PDF_PATH = OUTPUT_DIR / "kogebog.pdf"
DATA_DIR = ROOT / "data"
VERSION_FILE = DATA_DIR / "book_version.txt"

A4_W, A4_H = 2480, 3508
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


@dataclass(frozen=True)
class SectionStyle:
    ink: str
    panel: str
    accent: str
    soft: str


NDB: Dict[str, Nutrient] = {
    "hvedemel": Nutrient(364, 10.0, 76.0, 1.0),
    "rugmel": Nutrient(338, 10.3, 60.7, 1.7),
    "rugkerner": Nutrient(331, 9.5, 62.0, 1.8),
    "boghvedemel": Nutrient(343, 13.3, 71.5, 3.4),
    "grahamsmel": Nutrient(340, 13.0, 67.0, 2.5),
    "surdej": Nutrient(182, 5.0, 38.0, 0.5),
    "gær": Nutrient(105, 8.0, 8.0, 1.0),
    "salt": Nutrient(0, 0, 0, 0),
    "vand": Nutrient(0, 0, 0, 0),
    "oksekød_10": Nutrient(250, 26, 0, 17),
    "oksekød_5": Nutrient(210, 27, 0, 10),
    "svinenakke": Nutrient(270, 18, 0, 22),
    "and": Nutrient(337, 19, 0, 28),
    "kartoffel": Nutrient(77, 2, 17, 0.1),
    "blomkål": Nutrient(25, 1.9, 5.0, 0.3),
    "gulerod": Nutrient(41, 0.9, 10, 0.2),
    "løg": Nutrient(40, 1.1, 9.3, 0.1),
    "skalotteløg": Nutrient(72, 2.5, 16.8, 0.1),
    "hvidløg": Nutrient(149, 6.4, 33, 0.5),
    "tomatpuré": Nutrient(82, 4.3, 19, 0.5),
    "hakkede_tomater": Nutrient(29, 1.2, 4.8, 0.2),
    "oregano": Nutrient(265, 9, 69, 4.3),
    "basilikum": Nutrient(251, 23, 47, 4.1),
    "olivenolie": Nutrient(884, 0, 0, 100),
    "smør": Nutrient(717, 0.9, 0.1, 81),
    "mælk_15": Nutrient(46, 3.5, 4.8, 1.5),
    "mælk_35": Nutrient(64, 3.4, 4.8, 3.5),
    "fløde_38": Nutrient(366, 2.1, 2.8, 38),
    "græsk_yoghurt_10": Nutrient(133, 3.5, 3.8, 10),
    "skyr": Nutrient(63, 11, 4, 0.2),
    "æg": Nutrient(143, 12.5, 1.1, 10),
    "lasagneplader": Nutrient(360, 12, 72, 1.5),
    "pasta_tør": Nutrient(360, 12, 72, 1.5),
    "hytteost": Nutrient(81, 12, 3, 1.5),
    "parmesan": Nutrient(431, 38, 4, 29),
    "revet_ost_13": Nutrient(250, 30, 1, 13),
    "mozzarella": Nutrient(280, 22, 2, 20),
    "tommes_de_savoir": Nutrient(280, 22, 2, 20),
    "cheddar": Nutrient(403, 25, 1.3, 33),
    "parmaskinke": Nutrient(269, 28, 0, 18),
    "mornaysauce": Nutrient(160, 6, 8, 11),
    "hvid_fisk": Nutrient(82, 18, 0, 0.7),
    "spinat": Nutrient(23, 2.9, 1.4, 0.4),
    "agurk": Nutrient(15, 0.7, 2.8, 0.1),
    "citron": Nutrient(29, 1.1, 9.3, 0.3),
    "ris_tør": Nutrient(360, 7, 79, 0.7),
    "rapsolie": Nutrient(884, 0, 0, 100),
    "worcestershire": Nutrient(78, 0.7, 19, 0.2),
    "rødvin": Nutrient(85, 0.1, 2.6, 0),
    "champignon": Nutrient(22, 3.1, 3.3, 0.3),
    "østershatte": Nutrient(33, 3.3, 6.1, 0.4),
    "peberfrugt": Nutrient(31, 1, 6, 0.3),
    "havregryn": Nutrient(372, 13.2, 60, 7),
    "hakket_kylling": Nutrient(160, 21, 0, 8),
    "fiskekraft": Nutrient(10, 1, 1, 0),
    "rejer": Nutrient(99, 24, 0.2, 0.3),
    "blåmuslinger": Nutrient(86, 12, 4, 2),
    "bladselleri": Nutrient(16, 0.7, 3, 0.2),
    "hvidvin": Nutrient(82, 0.1, 2.6, 0),
    "majsstivelse": Nutrient(381, 0.3, 91, 0.1),
    "solsikkekerner": Nutrient(584, 20.8, 11.4, 51.5),
    "sukker": Nutrient(400, 0, 100, 0),
    "mørk_sirup": Nutrient(310, 0, 77, 0),
    "brun_farin": Nutrient(380, 0, 98, 0),
    "æble": Nutrient(52, 0.3, 14, 0.2),
    "cidereddike": Nutrient(21, 0, 0.9, 0),
    "æblejuice": Nutrient(46, 0.1, 11, 0.1),
    "minimælk": Nutrient(37, 3.4, 4.7, 0.5),
    "flødeost_urter": Nutrient(250, 6, 3, 24),
    "kyllingebryst": Nutrient(107, 22, 0, 2.4),
    "kokosmælk": Nutrient(177, 1.8, 2.7, 18),
    "kærnemælk": Nutrient(37, 3.5, 4.7, 0.5),
    "sigtemel": Nutrient(330, 11, 67, 1.5),
}

DISPLAY_NAMES = {
    "surdej": "Surdej",
    "gær": "Gær",
    "hvedemel": "Hvedemel",
    "rugmel": "Rugmel",
    "rugkerner": "Rugkerner",
    "boghvedemel": "Boghvedemel",
    "grahamsmel": "Grahamsmel",
    "salt": "Salt",
    "vand": "Vand",
    "oksekød_10": "Hakket oksekød 10 %",
    "oksekød_5": "Hakket oksekød 5 %",
    "svinenakke": "Svinenakke",
    "and": "And",
    "kartoffel": "Kartoffel",
    "blomkål": "Blomkål",
    "gulerod": "Gulerod",
    "løg": "Løg",
    "skalotteløg": "Skalotteløg",
    "hvidløg": "Hvidløg",
    "tomatpuré": "Tomatpuré",
    "hakkede_tomater": "Hakkede tomater",
    "oregano": "Oregano",
    "basilikum": "Basilikum",
    "olivenolie": "Olivenolie",
    "smør": "Smør",
    "mælk_15": "Letmælk",
    "mælk_35": "Sødmælk",
    "fløde_38": "Piskefløde",
    "græsk_yoghurt_10": "Græsk yoghurt 10 %",
    "skyr": "Skyr",
    "æg": "Æg",
    "lasagneplader": "Lasagneplader",
    "pasta_tør": "Tør pasta",
    "hytteost": "Hytteost",
    "parmesan": "Parmesan",
    "revet_ost_13": "Revet ost 13 %",
    "mozzarella": "Mozzarella",
    "tommes_de_savoir": "Tommes de Savoir",
    "cheddar": "Cheddar",
    "parmaskinke": "Parmaskinke",
    "mornaysauce": "Mornaysauce",
    "hvid_fisk": "Hvid fisk",
    "spinat": "Spinat",
    "agurk": "Agurk",
    "citron": "Citron",
    "ris_tør": "Tørre ris",
    "rapsolie": "Rapsolie",
    "worcestershire": "Worcestershire sauce",
    "rødvin": "Rødvin",
    "champignon": "Champignon",
    "østershatte": "Østershatte",
    "peberfrugt": "Peberfrugt",
    "havregryn": "Havregryn",
    "hakket_kylling": "Hakket kylling",
    "fiskekraft": "Fiskekraft",
    "rejer": "Rejer",
    "blåmuslinger": "Blåmuslinger",
    "bladselleri": "Bladselleri",
    "hvidvin": "Hvidvin",
    "majsstivelse": "Majsstivelse",
    "solsikkekerner": "Solsikkekerner",
    "sukker": "Sukker",
    "mørk_sirup": "Mørk sirup",
    "brun_farin": "Brun farin",
    "æble": "Æble",
    "cidereddike": "Æblecidereddike",
    "æblejuice": "Æblejuice",
    "minimælk": "Minimælk",
    "flødeost_urter": "Flødeost med hvidløg og urter",
    "kyllingebryst": "Kyllingebryst",
    "kokosmælk": "Kokosmælk",
    "kærnemælk": "Kærnemælk",
    "sigtemel": "Sigtemel",
}

SECTION_STYLES = {
    "Bagværk": SectionStyle("#38261d", "#f5ede4", "#c87f4f", "#e6d2be"),
    "Tilbehør": SectionStyle("#18332b", "#edf5f0", "#5d8f77", "#d5e6dc"),
    "Aftensmad": SectionStyle("#2f1f17", "#f8eee8", "#bf6845", "#eed1c3"),
    "Weekend": SectionStyle("#1d2530", "#edf1f6", "#7288a4", "#d5ddea"),
}

RECIPE_SECTION_SIZE = 32
RECIPE_TITLE_SIZE = 70
RECIPE_CHIP_SIZE = 28
RECIPE_BODY_SIZE = 34
RECIPE_BODY_BOLD_SIZE = 36
RECIPE_SMALL_SIZE = 27
COMPONENT_PREFIX = ":: "


RECIPES: List[Recipe] = [
    Recipe(
        section="Bagværk",
        title="Brød i stegeso",
        servings=1,
        finished_weight_g=760,
        ingredients=[
            "500 g hvedemel",
            "15 g frisk gær eller 7 g tørgær",
            "10 g fint salt",
            "3,5 dl koldt vand",
        ],
        method=[
            "Rør mel, gær, salt og vand sammen til en klistret dej. Dejen skal ikke æltes.",
            "Dæk skålen til, og lad dejen hæve 10-12 timer ved stuetemperatur.",
            "Sæt stegesoen uden låg i ovnen, og forvarm til 250 °C i 30 minutter.",
            "Hæld dejen ud på et let meldrysset bord, fold den et par gange, og lad den hvile 15 minutter.",
            "Læg dejen i den varme stegeso, sæt låg på, og bag 30 minutter.",
            "Fjern låget, og bag yderligere 12-15 minutter, til skorpen er mørk og sprød.",
            "Lad brødet køle helt af på rist før udskæring.",
        ],
        nutrient_items=[("hvedemel", 500), ("gær", 15)],
    ),
    Recipe(
        section="Bagværk",
        title="Kanelsnegle",
        servings=12,
        finished_weight_g=1300,
        ingredients=[
            "50 g gær",
            "2,5 dl lun sødmælk",
            "75 g smør, smeltet",
            "1 æg",
            "75 g sukker",
            "1/2 tsk fint salt",
            "ca. 500 g hvedemel",
            "Fyld: 100 g smør, 100 g brun farin, 2 spsk kanel",
            "Evt. glasur af flormelis og lidt vand eller citronsaft",
        ],
        method=[
            "Rør gæren ud i den lune mælk. Tilsæt sukker, salt, æg og smeltet smør.",
            "Rør melet i lidt ad gangen, og ælt dejen 8-10 minutter, til den er glat og smidig.",
            "Lad dejen hæve tildækket 1 time, til den er tydeligt hævet.",
            "Rør fyldet sammen. Rul dejen ud til et rektangel på cirka 40 x 30 cm, og smør fyldet jævnt ud.",
            "Rul dejen stramt sammen fra den lange side, og skær 12 snegle.",
            "Sæt sneglene på bageplade eller i form, og lad dem efterhæve 30 minutter.",
            "Bag ved 200 °C i 12-15 minutter, til de er gyldne. Afkøl let, og pynt eventuelt med glasur.",
        ],
        nutrient_items=[
            ("gær", 50),
            ("mælk_35", 250),
            ("smør", 175),
            ("æg", 55),
            ("sukker", 75),
            ("hvedemel", 500),
            ("brun_farin", 100),
        ],
    ),
    Recipe(
        section="Bagværk",
        title="Surdejsbrød",
        servings=1,
        finished_weight_g=1150,
        ingredients=[
            "200 g aktiv surdej",
            "200 g grahamsmel",
            "400 g hvedemel",
            "1 g gær",
            "15 g fint salt",
            "450 g vand",
            "Solsikkeolie til fad",
        ],
        method=[
            "Bland surdej, gær, mel og vand i røremaskinens skål. Kør dejen 8 minutter ved høj hastighed.",
            "Tilsæt salt, og kør videre cirka 2 minutter, til dejen slipper skålen.",
            "Hæld dejen i et lerfad, der er smurt let med solsikkeolie.",
            "Stræk og fold dejen 3-4 gange med 30 minutters mellemrum.",
            "Sæt dejen på køl natten over, cirka 10-14 timer.",
            "Tag dejen ud cirka 2 timer før bagning, og form den til ét brød eller til boller.",
            "Forvarm ovnen til 250 °C. Hæld 1 kop vand ind i den varme ovn lige før bagning, så der dannes damp.",
            "Bag boller i cirka 18 minutter. Bag et stort brød i cirka 38 minutter, tildækket med sølvpapir indtil de sidste 10 minutter.",
            "Lad brødet køle helt af på rist før udskæring.",
        ],
        nutrient_items=[("surdej", 200), ("grahamsmel", 200), ("hvedemel", 400), ("gær", 1)],
    ),
    Recipe(
        section="Bagværk",
        title="Rugbrød",
        servings=2,
        finished_weight_g=3000,
        ingredients=[
            "200 g aktiv rugsurdej",
            "1 l lunkent vand",
            "3 spsk fint salt (ca. 45 g)",
            "1 tsk sukker",
            "400 g knækkede rugkerner",
            "100 g rugmel",
            "500 g hvedemel",
            "3,5 dl lunkent vand",
            "665 g rugmel",
            "1 dl solsikkekerner",
            "1-2 spsk mørk sirup",
            "Neutral olie til 2 forme og pensling",
        ],
        method=[
            "Rør surdej, 1 l lunkent vand, salt og sukker sammen i en stor skål, til surdejen er opløst.",
            "Tilsæt rugkerner, 100 g rugmel og hvedemel, og rør dejen godt sammen.",
            "Dæk skålen med et rent viskestykke, og lad dejen stå ved stuetemperatur i 24 timer.",
            "Rør 3,5 dl lunkent vand, 665 g rugmel, solsikkekerner og sirup i dejen dagen efter.",
            "Rør dejen grundigt, til den har konsistens som en sej grød.",
            "Tag cirka 1 kop dej fra som surdej til næste bagning, drys toppen med lidt salt, dæk skålen til, og opbevar den i køleskab. Vent cirka 1 uge, før den bruges igen.",
            "Fordel dejen i 2 smurte rugbrødsforme, og glat overfladen med en våd dejskraber eller ske.",
            "Lad brødene hæve 4 timer ved stuetemperatur.",
            "Pensl toppen let med olie, og bag rugbrødene ved 190 °C i cirka 1½ time.",
            "Pensl de varme skorper med olie, tag brødene ud af formene, og lad dem køle af under et viskestykke.",
        ],
        nutrient_items=[
            ("surdej", 200),
            ("vand", 1350),
            ("salt", 45),
            ("sukker", 4),
            ("rugkerner", 400),
            ("rugmel", 765),
            ("hvedemel", 500),
            ("solsikkekerner", 60),
            ("mørk_sirup", 30),
        ],
    ),
    Recipe(
        section="Bagværk",
        title="Sigtebrød",
        servings=2,
        finished_weight_g=1470,
        ingredients=[
            "50 g gær",
            "3 dl koldt vand",
            "4 dl kærnemælk",
            "30 g smør, smeltet",
            "2 tsk fint salt",
            "700 g sigtemel",
            "ca. 300 g hvedemel",
            "Sammenpisket æg, mælk eller vand til pensling",
        ],
        method=[
            "Rør gæren ud i vand og kærnemælk i en røreskål.",
            "Smelt smørret og lad det køle lidt af. Tilsæt det til dejen sammen med salt, sigtemel og hvedemel.",
            "Ælt dejen grundigt i 8-10 minutter, til den er glat og smidig.",
            "Dæk skålen til og lad dejen hæve lunt i ca. 1 time, til den er tydeligt hævet.",
            "Slå dejen ned, del den i to og form hvert stykke til et aflangt brød.",
            "Læg brødene på en bageplade med bagepapir og lad dem efterhæve i 30 minutter.",
            "Rids brødene med en skarp kniv og pensl med sammenpisket æg, mælk eller vand.",
            "Bag ved 200 °C i 30-35 minutter, til brødene er gyldne og hule at høre på underneath.",
            "Lad brødene køle af på rist inden udskæring.",
        ],
        nutrient_items=[
            ("gær", 50),
            ("kærnemælk", 400),
            ("smør", 30),
            ("sigtemel", 700),
            ("hvedemel", 300),
        ],
    ),
    Recipe(
        section="Tilbehør",
        title="Mini hash browns",
        servings=4,
        finished_weight_g=420,
        ingredients=[
            "400 g bagekartofler, groftrevet",
            "1 spsk majsstivelse",
            "1 tsk hvidløgspulver",
            "1 tsk løgpulver",
            "1/2 tsk paprika",
            "Salt og friskkværnet peber",
            "2 spsk neutral olie",
        ],
        method=[
            "Læg de revne kartofler i koldt vand i 5 minutter, og pres dem derefter helt tørre i et rent viskestykke.",
            "Bland kartoflerne med majsstivelse, krydderier og olie, så massen hænger sammen.",
            "Form små ovale hash browns med faste kanter.",
            "Steg dem 2-3 minutter på hver side i olie, eller bag dem i airfryer eller ovn, til de er gyldne og sprøde.",
            "Server straks, mens skorpen stadig er sprød.",
        ],
        nutrient_items=[("kartoffel", 400), ("majsstivelse", 10), ("rapsolie", 20)],
    ),
    Recipe(
        section="Tilbehør",
        title="Tzatziki",
        servings=4,
        finished_weight_g=380,
        ingredients=[
            "250 g græsk yoghurt 10 %",
            "200 g agurk, groftrevet og afdryppet",
            "1-2 fed hvidløg, fintrevet",
            "1 spsk olivenolie",
            "1 tsk citronsaft eller hvidvinseddike",
            "Salt, evt. lidt hakket dild eller mynte",
        ],
        method=[
            "Riv agurken groft, og pres så meget væde ud som muligt.",
            "Rør yoghurt sammen med agurk, hvidløg, olie og citronsaft.",
            "Smag til med salt og eventuelt dild eller mynte.",
            "Sæt tzatzikien på køl mindst 30 minutter før servering, så smagen samler sig.",
        ],
        nutrient_items=[
            ("græsk_yoghurt_10", 250),
            ("agurk", 200),
            ("hvidløg", 6),
            ("olivenolie", 14),
            ("citron", 5),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="Galetter med skinke, ost og æg",
        servings=4,
        finished_weight_g=950,
        ingredients=[
            "2 dl boghvedemel",
            "2 æg",
            "3 dl mælk",
            "1/2 tsk fint salt",
            "4 tsk smør til stegning",
            "Skinkefyld: 4 skiver cheddar eller mozzarella",
            "8 skiver parmaskinke",
            "4 æg",
            "Til servering: 50 g frisk spinat",
        ],
        method=[
            "Pisk boghvedemel, æg, mælk og salt sammen til en glat dej uden klumper.",
            "Varm en pande op ved middel varme, smelt lidt smør, og fordel cirka 1/2 dl dej i et tyndt lag.",
            "Steg galetterne let gyldne på begge sider, og læg dem til side under et viskestykke, så de holder sig bløde.",
            "Læg en skive ost i midten af hver galette, og placér 2 skiver parmaskinke ovenpå.",
            "Fold kanterne let ind mod midten, så der dannes en lille fordybning til ægget.",
            "Slå 1 æg ud i hver galette, læg låg på panden, og steg ved lav varme i cirka 5 minutter, til hviden har sat sig.",
            "Server straks med frisk spinat ved siden af.",
        ],
        nutrient_items=[
            ("boghvedemel", 120),
            ("æg", 330),
            ("mælk_15", 300),
            ("smør", 20),
            ("mozzarella", 80),
            ("parmaskinke", 120),
            ("spinat", 50),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="Bergensk fiskesuppe",
        servings=2,
        finished_weight_g=1400,
        ingredients=[
            "500 g hvid fisk i mundrette stykker",
            "500 g urensede rejer",
            "2 stilke bladselleri",
            "2 gulerødder",
            "3 skalotteløg",
            "2 fed hvidløg",
            "6 dl fiskekraft",
            "2,5 dl blåmuslingekraft",
            "2 spsk olivenolie",
            "1,5 dl hvidvin",
            "2 æggeblommer",
            "1 dl fløde eller sæterømme",
            "Salt, peber og evt. cayenne",
        ],
        method=[
            "Pil rejerne. Skær grøntsagerne fint, og skær fisken i mundrette stykker.",
            "Sautér bladselleri, gulerødder, skalotteløg og hvidløg i olivenolie i cirka 10 minutter uden at de tager farve.",
            "Tilsæt hvidvin, og lad den koge ind, til smagen bliver koncentreret.",
            "Bring en del af fiskekraften til lige under kogepunktet, og pocher fisken forsigtigt 1-2 minutter. Tag den op, så den ikke overtilberedes.",
            "Varm resten af fiskekraften og blåmuslingekraften op i en gryde.",
            "Pisk æggeblommer og fløde sammen. Temperér blandingen med lidt af den varme kraft, og hæld den derefter tilbage i gryden.",
            "Varm suppen op uden at koge, til den er let cremet. Smag til med salt, peber og eventuelt lidt cayenne.",
            "Fordel grøntsager, fisk og rejer i tallerkener, og hæld den varme suppe over ved servering.",
        ],
        nutrient_items=[
            ("hvid_fisk", 500),
            ("rejer", 250),
            ("bladselleri", 80),
            ("gulerod", 140),
            ("skalotteløg", 90),
            ("hvidløg", 8),
            ("fiskekraft", 850),
            ("olivenolie", 28),
            ("hvidvin", 150),
            ("æg", 34),
            ("fløde_38", 100),
            ("blåmuslinger", 100),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="Boller i karry med grønt",
        servings=4,
        finished_weight_g=1800,
        ingredients=[
            "400 g hakket kylling eller svinekød",
            "1 løg, finthakket",
            "1 æg",
            "1 dl mælk",
            "3 spsk havregryn",
            "Salt og peber",
            "Sauce: 2 spsk olie, 2 spsk karry, 1 løg",
            "2 gulerødder, 1 æble, 1-2 fed hvidløg",
            "1-2 spsk hvedemel",
            "6 dl bouillon",
            "1 dl mælk eller fløde",
            "280 g ris, tørvægt",
        ],
        method=[
            "Rør farsen sammen med finthakket løg, æg, mælk, havregryn, salt og peber. Lad farsen hvile 15 minutter.",
            "Form farsen til boller med en ske, og kog dem i letsaltet vand i 8-10 minutter. Gem kogevandet til saucen.",
            "Svits løg, gulerod, æble og hvidløg i olie et par minutter. Tilsæt karry, og lad den kort stege med.",
            "Rør hvedemelet i, og spæd gradvist med bouillon, til saucen er glat.",
            "Lad saucen simre, til grøntsagerne er helt møre, og blend den derefter glat.",
            "Tilsæt mælk eller fløde, smag til, og læg kødbollerne tilbage i saucen.",
            "Kog risene efter pakkens anvisning, og server dem til retten.",
        ],
        nutrient_items=[
            ("hakket_kylling", 400),
            ("løg", 200),
            ("æg", 55),
            ("mælk_15", 200),
            ("havregryn", 30),
            ("rapsolie", 28),
            ("gulerod", 150),
            ("hvidløg", 6),
            ("hvedemel", 20),
            ("æble", 120),
            ("ris_tør", 280),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="Cottage pie, klassisk",
        servings=4,
        finished_weight_g=2200,
        ingredients=[
            "500 g hakket oksekød, 8-12 %",
            "1 stort løg",
            "2 gulerødder",
            "2 fed hvidløg",
            "2 spsk tomatpuré",
            "2 spsk hvedemel",
            "2,5 dl oksebouillon",
            "1 dl rødvin eller ekstra bouillon",
            "1 spsk Worcestershire sauce",
            "1 tsk tørret timian",
            "1 laurbærblad",
            "1 spsk olie",
            "Kartoffelmos: 1 kg kartofler, 50 g smør, 1-1,5 dl mælk",
            "Evt. 50 g cheddar",
        ],
        method=[
            "Skræl kartoflerne, og kog dem møre i letsaltet vand 15-20 minutter. Hæld vandet fra, og damp dem tørre.",
            "Mos kartoflerne med smør og varm mælk, og smag til med salt og peber.",
            "Sautér løg og gulerødder i olie i 5 minutter. Tilsæt hvidløg kort.",
            "Brun oksekødet grundigt. Tilsæt tomatpuré, og lad den stege med 1 minut.",
            "Rør hvedemelet i, og spæd med bouillon og rødvin lidt ad gangen.",
            "Tilsæt Worcestershire sauce, timian og laurbærblad, og lad fyldet simre 10-15 minutter til en tyk sovs.",
            "Fordel kødfyldet i et ovnfast fad. Læg kartoffelmosen over, og lav riller med en gaffel. Drys eventuelt med cheddar.",
            "Bag ved 200 °C i 20-25 minutter, til toppen er gylden. Lad retten hvile 10 minutter før servering.",
        ],
        nutrient_items=[
            ("oksekød_10", 500),
            ("løg", 150),
            ("gulerod", 200),
            ("hvidløg", 8),
            ("tomatpuré", 30),
            ("hvedemel", 16),
            ("rødvin", 100),
            ("worcestershire", 15),
            ("rapsolie", 14),
            ("kartoffel", 1000),
            ("smør", 50),
            ("mælk_35", 150),
            ("cheddar", 50),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="Cottage pie, sundere",
        servings=4,
        finished_weight_g=2300,
        ingredients=[
            "500 g hakket oksekød, 5 %",
            "1 løg",
            "2 gulerødder",
            "1 rød peberfrugt",
            "150 g champignon",
            "2 fed hvidløg",
            "2 spsk tomatpuré",
            "2,5 dl fedtfattig bouillon",
            "1 spsk Worcestershire sauce",
            "1 tsk olie",
            "Mos: 800 g kartofler og 300 g blomkål",
            "2 spsk skyr og 1-2 spsk letmælk",
        ],
        method=[
            "Kog kartofler og blomkål møre i samme gryde. Hæld vandet fra, og mos med skyr og lidt mælk.",
            "Sautér løg, gulerødder, peberfrugt og champignon i lidt olie, til grøntsagerne falder sammen.",
            "Tilsæt oksekødet, og brun det godt af.",
            "Rør tomatpuré i, spæd med bouillon, og tilsæt Worcestershire sauce.",
            "Lad fyldet simre 12-15 minutter, til det er samlet og saftigt.",
            "Fordel fyldet i et ovnfast fad, læg mosen over, og bag 20-25 minutter ved 200 °C.",
        ],
        nutrient_items=[
            ("oksekød_5", 500),
            ("løg", 120),
            ("gulerod", 150),
            ("peberfrugt", 150),
            ("champignon", 150),
            ("hvidløg", 8),
            ("tomatpuré", 30),
            ("worcestershire", 15),
            ("rapsolie", 5),
            ("kartoffel", 800),
            ("blomkål", 300),
            ("skyr", 30),
            ("mælk_15", 30),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="Hjemmelavet lasagne",
        servings=4,
        finished_weight_g=1900,
        ingredients=[
            "500 g hakket oksekød",
            "1 løg",
            "2 fed hvidløg",
            "2 gulerødder",
            "2 spsk tomatpuré",
            "400 g hakkede tomater",
            "1 dl vand eller bouillon",
            "1 tsk oregano",
            "1 tsk basilikum",
            "1 spsk olivenolie",
            "Bechamel: 40 g smør, 40 g hvedemel, 6 dl mælk",
            "10-12 lasagneplader, cirka 250 g",
            "120 g revet ost",
        ],
        method=[
            "Svits finthakket løg og hvidløg i olien, og brun derefter oksekødet grundigt.",
            "Tilsæt gulerødder, tomatpuré, hakkede tomater, vand og krydderier. Lad kødsaucen simre 25 minutter.",
            "Smelt smørret til bechamel, pisk hvedemelet i, og spæd med mælk lidt ad gangen, til saucen er glat og tyk.",
            "Læg lasagnen i lag med kødsauce, lasagneplader og bechamel. Gentag til fadet er fyldt.",
            "Slut med bechamel og revet ost på toppen.",
            "Bag ved 200 °C i 30-35 minutter, til overfladen er gylden. Lad lasagnen hvile 10 minutter før servering.",
        ],
        nutrient_items=[
            ("oksekød_10", 500),
            ("løg", 120),
            ("hvidløg", 8),
            ("gulerod", 150),
            ("tomatpuré", 30),
            ("hakkede_tomater", 400),
            ("oregano", 1),
            ("basilikum", 1),
            ("olivenolie", 14),
            ("smør", 40),
            ("hvedemel", 40),
            ("mælk_35", 600),
            ("lasagneplader", 250),
            ("mozzarella", 120),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="Hvid fisk med spinat og mornaysauce",
        servings=3,
        finished_weight_g=900,
        ingredients=[
            "450 g hvid fisk, fx torsk, kuller eller sej",
            "200 g frisk spinat eller optøet, afdryppet spinat",
            "2 dl mornaysauce",
            "Smør til fadet",
            "Salt, peber og lidt citronsaft",
            "Evt. 30 g revet ost",
        ],
        method=[
            "Forvarm ovnen til 200 °C, og smør et ovnfast fad let.",
            "Krydr fisken med salt, peber og citronsaft.",
            "Fordel spinaten i bunden af fadet, læg fisken ovenpå, og hæld mornaysaucen over.",
            "Drys eventuelt lidt ost på toppen.",
            "Bag retten 20-25 minutter, til fisken netop flager og saucen bobler langs kanten.",
            "Server med kogte kartofler, ris eller kartoffelmos.",
        ],
        nutrient_items=[("hvid_fisk", 450), ("spinat", 200), ("mornaysauce", 200), ("mozzarella", 30)],
    ),
    Recipe(
        section="Aftensmad",
        title="Pastarør med østershatte og fløde",
        servings=3,
        finished_weight_g=1000,
        ingredients=[
            "250 g pastarør, fx rigatoni eller penne",
            "250 g østershatte",
            "3 skalotteløg",
            "2 fed hvidløg",
            "2 spsk smør",
            "1 spsk olivenolie",
            "2 dl piskefløde",
            "1/2 dl hvidvin, valgfrit",
            "1 tsk citronsaft",
            "50 g revet parmesan",
            "Frisk persille, salt og peber",
        ],
        method=[
            "Kog pastaen al dente i rigeligt saltet vand, og gem lidt af kogevandet.",
            "Sautér finthakkede skalotteløg og hvidløg i smør og olivenolie, til de er bløde og søde.",
            "Tilsæt østershattene, og steg dem ved god varme, til de er gyldne og let sprøde i kanterne.",
            "Hæld hvidvin på, hvis du bruger den, og lad den koge let ind.",
            "Tilsæt fløde, og lad saucen simre 5-7 minutter. Smag til med citronsaft, salt og peber.",
            "Vend pastaen i saucen, og justér konsistensen med lidt kogevand.",
            "Server med parmesan og frisk persille.",
        ],
        nutrient_items=[
            ("pasta_tør", 250),
            ("østershatte", 250),
            ("skalotteløg", 90),
            ("hvidløg", 8),
            ("smør", 28),
            ("olivenolie", 14),
            ("fløde_38", 200),
            ("hvidvin", 50),
            ("parmesan", 50),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="Proteinrig pastaret med oksekød",
        servings=4,
        finished_weight_g=1650,
        ingredients=[
            "400 g hakket oksekød, 4-7 %",
            "200 g fusilli",
            "250 g hytteost 1,5 %",
            "420 g pastasauce",
            "100 g frisk spinat",
            "50 g parmesan",
            "50 g revet ost 13 %",
            "1 tsk oregano",
            "1 tsk hvidløgspulver",
            "1 tsk løgpulver",
            "1 tsk sort peber",
            "1 tsk salt",
        ],
        method=[
            "Kog pastaen efter anvisningen, så den stadig har bid, og lad den dryppe godt af.",
            "Brun oksekødet grundigt på en varm pande, og krydr med oregano, hvidløgspulver, løgpulver, peber og salt.",
            "Bland pasta, oksekød, spinat, hytteost og pastasauce i et ovnfast fad.",
            "Fordel parmesan og revet ost på toppen.",
            "Bag ved 200 °C i 10-15 minutter, til retten er gennemvarm og osten er smeltet.",
        ],
        nutrient_items=[
            ("oksekød_5", 400),
            ("pasta_tør", 200),
            ("hytteost", 250),
            ("hakkede_tomater", 420),
            ("spinat", 100),
            ("parmesan", 50),
            ("revet_ost_13", 50),
            ("oregano", 2),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="Spicy Mac & Cheese",
        servings=5,
        finished_weight_g=2015,
        ingredients=[
            ":: Kød og pasta",
            "500 g hakket oksekød, 4-7 %",
            "350 g suppehorn (pasta)",
            "10 g oksebouillon (terning)",
            "6 dl kogende vand",
            ":: Ost og mejeri",
            "100 g revet ost",
            "50 g flødeost med hvidløg og urter",
            "200 g minimælk",
            "2 skiver cheddar (ca. 40 g)",
            ":: Grøntsager og smag",
            "100 g rødløg, hakket",
            "40 g tomatpuré",
            ":: Krydderier",
            "Salt",
            "Sort peber",
            "Løgpulver",
            "Cayennepeber",
            "Paprika",
        ],
        method=[
            ":: Kød og løg",
            "Brun oksekødet i en stor gryde ved høj varme, til det er gennemstegt og let karamelliseret.",
            "Tilsæt hakket rødløg og svits ved middel varme, til løget er blødt og let gyldent.",
            "Krydr med salt, sort peber, løgpulver, paprika og cayennepeber, og rør det godt sammen.",
            ":: Sauce og pasta",
            "Lav et lille hul i midten af gryden og tilsæt tomatpuréen. Lad den stege i 1-2 minutter, så den mister sin råsmag.",
            "Hæld kogende vand, oksebouillon og minimælk i gryden, og rør det hele godt sammen.",
            "Tilsæt suppehornene direkte i gryden. Lad retten simre ved middel varme i 12-15 minutter under jævnlig omrøring, indtil pastaen er mør og det meste af væsken er absorberet.",
            ":: Afslutning",
            "Skru ned for varmen og rør flødeost, revet ost og cheddar i, til retten er ensartet og cremet. Smag til med salt, peber og cayennepeber.",
        ],
        nutrient_items=[
            ("oksekød_5", 500),
            ("pasta_tør", 350),
            ("revet_ost_13", 100),
            ("flødeost_urter", 50),
            ("minimælk", 200),
            ("løg", 100),
            ("tomatpuré", 40),
            ("cheddar", 40),
        ],
    ),
    Recipe(
        section="Aftensmad",
        title="One pot kylling i karry",
        servings=2,
        finished_weight_g=870,
        ingredients=[
            "450 g kyllingebryst",
            "3 tsk karry",
            "1/2 tsk paprika",
            "1 spsk sukker",
            "1/2 tsk stødt spidskommen",
            "400 ml kokosmælk",
            "1 hønsebouillonterning",
            "160 g ris",
            "Frisk persille til servering",
            "Salt og peber",
        ],
        method=[
            "Fjern eventuelle sener fra kyllingen.",
            "Læg kyllingebrysterne hele i en gryde sammen med karry, paprika, sukker, spidskommen, kokosmælk og bouillonterning. Rør rundt.",
            "Tilsæt risene direkte i gryden og rør rundt igen.",
            "Sæt låget på med en lille sprække til damp, og lad retten simre ved middel varme i 30 minutter.",
            "Tag gryden af varmen og brug to gafler til at rive kyllingen i strimler.",
            "Sæt gryden tilbage på blusset i 5 minutter og lad det boble let op. Smag til med salt og peber.",
            "Server med frisk persille.",
        ],
        nutrient_items=[
            ("kyllingebryst", 450),
            ("ris_tør", 160),
            ("kokosmælk", 400),
            ("sukker", 12),
        ],
    ),
    Recipe(
        section="Weekend",
        title="Aligot",
        servings=4,
        finished_weight_g=1650,
        ingredients=[
            "1 kg melede kartofler",
            "2 fed hvidløg, valgfrit",
            "50 g smør",
            "2,5 dl varm fløde",
            "350 g Tommes de Savoir",
            "Salt og hvid peber",
        ],
        method=[
            "Kog kartoflerne møre i letsaltet vand, eventuelt sammen med hvidløget. Hæld vandet fra, og damp dem tørre.",
            "Mos kartoflerne helt glatte, og rør smørret i ved lav varme.",
            "Spæd med den varme fløde lidt ad gangen, til mosen er glat og tyk.",
            "Tilsæt osten gradvist under konstant omrøring, så massen bliver blank og elastisk.",
            "Fortsæt, til aligot kan trækkes i lange tråde.",
            "Smag til med salt og hvid peber, og server straks.",
        ],
        nutrient_items=[("kartoffel", 1000), ("hvidløg", 6), ("smør", 50), ("fløde_38", 250), ("tommes_de_savoir", 350)],
    ),
    Recipe(
        section="Weekend",
        title="Langtidsstegt and",
        servings=6,
        finished_weight_g=2100,
        ingredients=[
            "1 and på ca. 3,5 kg",
            "Salt og peber",
            "Evt. æbler og svesker til fyld",
        ],
        method=[
            "Dup anden tør, og krydr den godt både indvendigt og udvendigt med salt og peber.",
            "Steg anden ved 150 °C i cirka 3-3,5 timer, svarende til omtrent 50-60 minutter pr. kilo.",
            "Mål kernetemperaturen i låret; den bør være omkring 75 °C.",
            "Hæv eventuelt ovntemperaturen til 220-230 °C de sidste 10-15 minutter, hvis skindet skal være ekstra sprødt.",
            "Lad anden hvile 15-20 minutter før udskæring.",
        ],
        nutrient_items=[("and", 2100)],
    ),
    Recipe(
        section="Weekend",
        title="Pulled pork",
        servings=8,
        finished_weight_g=1900,
        ingredients=[
            "2 kg svinenakke",
            "2 spsk paprika",
            "1 spsk brun farin",
            "1 spsk salt",
            "1 tsk peber",
            "1 tsk chilipulver",
            "1 tsk hvidløgspulver",
            "1 tsk løgpulver",
            "1 dl æblecidereddike",
            "1 dl æblejuice eller vand",
            "BBQ-sauce efter smag",
        ],
        method=[
            "Bland krydderierne, og gnid blandingen grundigt ind i kødet.",
            "Læg kødet i stegeso eller et ovnfast fad, og tilsæt æblecidereddike og æblejuice.",
            "Steg ved 110-120 °C i 6-8 timer, til kødet er så mørt, at det let kan trækkes fra hinanden.",
            "Lad kødet hvile 20 minutter, og trevl det derefter med to gafler.",
            "Vend eventuelt kødet med lidt BBQ-sauce lige før servering.",
        ],
        nutrient_items=[("svinenakke", 2000), ("brun_farin", 15), ("cidereddike", 100), ("æblejuice", 100)],
    ),
]

COMPONENT_RULES = {
    "Brød i stegeso": {
        "ingredients": [("Dej", 0, 4)],
        "method": [("Dej", 0, 2), ("Bagning", 2, 7)],
    },
    "Kanelsnegle": {
        "ingredients": [("Dej", 0, 7), ("Fyld", 7, 8), ("Glasur", 8, 9)],
        "method": [("Dej", 0, 3), ("Fyld og formning", 3, 6), ("Bagning", 6, 7)],
    },
    "Surdejsbrød": {
        "ingredients": [("Dej", 0, 6), ("Klargøring", 6, 7)],
        "method": [("Dej", 0, 3), ("Foldning og hævning", 3, 6), ("Bagning", 6, 9)],
    },
    "Rugbrød": {
        "ingredients": [("Dag 1", 0, 7), ("Dag 2", 7, 11), ("Bagning", 11, 12)],
        "method": [("Dag 1", 0, 3), ("Dag 2", 3, 6), ("Formning og hævning", 6, 8), ("Bagning", 8, 10)],
    },
    "Mini hash browns": {
        "ingredients": [("Kartoffelmasse", 0, 7)],
        "method": [("Forberedelse", 0, 2), ("Formning og stegning", 2, 5)],
    },
    "Tzatziki": {
        "ingredients": [("Tzatziki", 0, 6)],
        "method": [("Tzatziki", 0, 4)],
    },
    "Galetter med skinke, ost og æg": {
        "ingredients": [("Galettedej", 0, 5), ("Skinkefyld", 5, 8), ("Til servering", 8, 9)],
        "method": [("Galetter", 0, 3), ("Skinkefyld", 3, 6), ("Servering", 6, 7)],
    },
    "Bergensk fiskesuppe": {
        "ingredients": [("Suppebase", 0, 10), ("Legering og finish", 10, 13)],
        "method": [("Forberedelse", 0, 1), ("Suppebase", 1, 5), ("Legering", 5, 7), ("Servering", 7, 8)],
    },
    "Boller i karry med grønt": {
        "ingredients": [("Boller", 0, 6), ("Sovs", 6, 11), ("Til servering", 11, 12)],
        "method": [("Boller", 0, 2), ("Sovs", 2, 6), ("Til servering", 6, 7)],
    },
    "Cottage pie, klassisk": {
        "ingredients": [("Fyld", 0, 12), ("Kartoffelmos og top", 12, 14)],
        "method": [("Kartoffelmos", 0, 2), ("Fyld", 2, 6), ("Samling og bagning", 6, 8)],
    },
    "Cottage pie, sundere": {
        "ingredients": [("Fyld", 0, 10), ("Mos", 10, 12)],
        "method": [("Mos", 0, 1), ("Fyld", 1, 5), ("Samling og bagning", 5, 6)],
    },
    "Hjemmelavet lasagne": {
        "ingredients": [("Kødsauce", 0, 10), ("Bechamel", 10, 11), ("Samling", 11, 13)],
        "method": [("Kødsauce", 0, 2), ("Bechamel", 2, 3), ("Samling og bagning", 3, 6)],
    },
    "Hvid fisk med spinat og mornaysauce": {
        "ingredients": [("Fiskefad", 0, 6)],
        "method": [("Fiskefad", 0, 6)],
    },
    "Pastarør med østershatte og fløde": {
        "ingredients": [("Pasta og sauce", 0, 11)],
        "method": [("Pasta", 0, 1), ("Sauce", 1, 5), ("Samling", 5, 7)],
    },
    "Proteinrig pastaret med oksekød": {
        "ingredients": [("Pastaret", 0, 12)],
        "method": [("Pasta og kød", 0, 2), ("Samling og bagning", 2, 5)],
    },
    "Aligot": {
        "ingredients": [("Aligot", 0, 6)],
        "method": [("Kartoffelmos", 0, 3), ("Ost og finish", 3, 6)],
    },
    "Langtidsstegt and": {
        "ingredients": [("And", 0, 3)],
        "method": [("Stegning", 0, 5)],
    },
    "Pulled pork": {
        "ingredients": [("Kød og krydderier", 0, 10), ("Servering", 10, 11)],
        "method": [("Klargøring", 0, 2), ("Langtidstilberedning", 2, 4), ("Afslutning", 4, 5)],
    },
}


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
    return (
        componentize_entries(recipe.ingredients, rules["ingredients"]),
        componentize_entries(recipe.method, rules["method"]),
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
            left_height += body_line
            left_height += len(wrap_text(draw, component_name(ingredient), body_bold, ingredient_width)) * body_line
            left_height += int(body_line * 0.2)
        else:
            left_height += len(wrap_text(draw, f"• {ingredient}", body_font, ingredient_width)) * body_line

    right_height = 0
    step_number = 1
    for step in method_entries:
        if is_component_entry(step):
            step_number = 1
            right_height += body_line
            right_height += len(wrap_text(draw, component_name(step), body_bold, method_width)) * body_line
            right_height += int(body_line * 0.2)
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


def draw_cover_illustration(base: Image.Image) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    art_box = [130, 1000, A4_W - 130, A4_H - 250]
    blurred_roundrect(overlay, [art_box[0] + 12, art_box[1] + 18, art_box[2] + 12, art_box[3] + 18], 48, (60, 36, 22, 45), 22)
    draw.rounded_rectangle(art_box, radius=48, fill="#efe1d0", outline="#dac4ae", width=3)

    art_w = art_box[2] - art_box[0]
    art_h = art_box[3] - art_box[1]
    art_bg = vertical_gradient(art_w, art_h, "#f6ede2", "#e7cfb8")
    overlay.paste(art_bg.convert("RGBA"), (art_box[0], art_box[1]))
    draw.rounded_rectangle(art_box, radius=48, outline="#d5b99d", width=3)

    table_top = art_box[1] + art_h * 0.66
    draw.rectangle([art_box[0], int(table_top), art_box[2], art_box[3]], fill="#7a543d")
    draw.rectangle([art_box[0], int(table_top + 48), art_box[2], art_box[3]], fill="#654533")

    cloth = [
        (art_box[0] + 120, int(table_top) - 20),
        (art_box[0] + 430, int(table_top) - 40),
        (art_box[0] + 610, art_box[3] - 60),
        (art_box[0] + 250, art_box[3] - 20),
    ]
    draw.polygon(cloth, fill="#d4ddd8")
    draw.line([cloth[0], cloth[2][0] - 70, cloth[2][1] - 30], fill="#b8c4be", width=4)
    draw.line([cloth[1], cloth[2][0] - 140, cloth[2][1] - 120], fill="#b8c4be", width=4)

    blurred_ellipse(overlay, [art_box[0] + 340, int(table_top) - 10, art_box[0] + 1040, int(table_top) + 180], (40, 20, 12, 70), 28)
    draw.ellipse([art_box[0] + 380, int(table_top) - 80, art_box[0] + 1000, int(table_top) + 120], fill="#f9f4ed", outline="#d8cdc1", width=4)
    draw.ellipse([art_box[0] + 440, int(table_top) - 20, art_box[0] + 940, int(table_top) + 90], fill="#efe5d8")

    tomato_centers = [
        (art_box[0] + 560, int(table_top) - 70, 96),
        (art_box[0] + 690, int(table_top) - 40, 84),
        (art_box[0] + 810, int(table_top) - 72, 92),
        (art_box[0] + 770, int(table_top) + 20, 78),
        (art_box[0] + 620, int(table_top) + 18, 74),
    ]
    for cx, cy, r in tomato_centers:
        blurred_ellipse(overlay, [cx - r + 10, cy - r + 18, cx + r + 10, cy + r + 18], (64, 22, 16, 54), 14)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#c84d3a", outline="#9c3326", width=3)
        draw.ellipse([cx - r + 22, cy - r + 18, cx - 4, cy - 8], fill="#e38773")
        draw.polygon(
            [(cx, cy - r - 8), (cx + 16, cy - r + 16), (cx, cy - r + 8), (cx - 16, cy - r + 16)],
            fill="#517649",
        )

    leaves = [
        [art_box[0] + 880, int(table_top) - 10, art_box[0] + 1010, int(table_top) + 90],
        [art_box[0] + 930, int(table_top) + 20, art_box[0] + 1060, int(table_top) + 120],
        [art_box[0] + 510, int(table_top) + 40, art_box[0] + 650, int(table_top) + 150],
        [art_box[0] + 420, int(table_top) - 10, art_box[0] + 560, int(table_top) + 90],
    ]
    for bbox in leaves:
        draw.ellipse(bbox, fill="#5b7f54", outline="#456540", width=2)
        draw.line([bbox[0] + 22, (bbox[1] + bbox[3]) // 2, bbox[2] - 22, (bbox[1] + bbox[3]) // 2], fill="#dbe7d1", width=2)

    bread = [art_box[0] + 1040, int(table_top) - 10, art_box[0] + 1390, int(table_top) + 210]
    blurred_ellipse(overlay, [bread[0] + 10, bread[1] + 20, bread[2] + 20, bread[3] + 28], (30, 18, 10, 48), 18)
    draw.rounded_rectangle(bread, radius=90, fill="#bf8754", outline="#8d6039", width=4)
    draw.arc([bread[0] + 60, bread[1] + 30, bread[0] + 180, bread[3] - 30], start=300, end=70, fill="#f1d3a4", width=8)
    draw.arc([bread[0] + 150, bread[1] + 26, bread[0] + 270, bread[3] - 34], start=300, end=70, fill="#f1d3a4", width=8)
    draw.arc([bread[0] + 240, bread[1] + 32, bread[0] + 340, bread[3] - 36], start=300, end=70, fill="#f1d3a4", width=8)

    for gx, gy in [(art_box[0] + 1060, int(table_top) + 180), (art_box[0] + 1130, int(table_top) + 210)]:
        blurred_ellipse(overlay, [gx + 10, gy + 16, gx + 126, gy + 126], (40, 24, 16, 44), 12)
        draw.ellipse([gx, gy, gx + 116, gy + 116], fill="#f3ece3", outline="#d7c8b8", width=3)
        draw.arc([gx + 14, gy + 34, gx + 60, gy + 104], start=270, end=70, fill="#dccdbf", width=3)
        draw.arc([gx + 54, gy + 22, gx + 104, gy + 92], start=250, end=60, fill="#dccdbf", width=3)

    spoon_handle = [art_box[0] + 300, int(table_top) + 180, art_box[0] + 760, art_box[3] - 70]
    draw.line([spoon_handle[0], spoon_handle[1], spoon_handle[2], spoon_handle[3]], fill="#a9774f", width=24)
    draw.line([spoon_handle[0], spoon_handle[1], spoon_handle[2], spoon_handle[3]], fill="#c69467", width=14)
    draw.ellipse([art_box[0] + 210, int(table_top) + 110, art_box[0] + 360, int(table_top) + 280], fill="#b78359", outline="#8d6039", width=4)
    draw.ellipse([art_box[0] + 235, int(table_top) + 135, art_box[0] + 335, int(table_top) + 245], fill="#7d5034")

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

    draw_tag(draw, (left_x, tag_y), section_label(recipe.section), section_font, style.accent, "#fffdf9")

    title_y = title_start_y
    for line in title_lines:
        draw.text((left_x, title_y), line, font=title_font, fill=style.ink)
        title_y += fonts["title_line"]

    draw_tag(draw, (left_x, chip_y), f"{recipe.servings} portioner", chip_font, style.soft, style.ink)
    draw_tag(draw, (left_x + 240, chip_y), f"{round(kcal_per_portion)} kcal/portion", chip_font, style.soft, style.ink)

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
            cursor_left += int(body_line * 0.35)
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
            cursor_left += int(body_line * 0.1)
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
            cursor_right += int(body_line * 0.35)
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
            cursor_right += int(body_line * 0.1)
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
    panel = vertical_gradient(A4_W, A4_H, "#f7f0e5", "#eadbc8")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A4_W - 28, A4_H - 28], radius=34, outline="#d7c2ad", width=3, fill="#fbf7f1")
    draw.rounded_rectangle([84, 84, A4_W - 84, A4_H - 84], radius=42, outline="#cdb094", width=2)
    draw.ellipse([A4_W - 620, 120, A4_W - 110, 630], outline="#e3d0be", width=4)
    draw.ellipse([A4_W - 540, 190, A4_W - 20, 710], outline="#efe4d8", width=2)

    title_font = load_font(128, "display")
    subtitle_font = load_font(52, "sans")
    strap_font = load_font(36, "sans")
    meta_font = load_font(30, "sans-bold")

    title_y = 320
    for line in wrap_text(draw, TITLE, title_font, A4_W - 2 * 160):
        draw.text((160, title_y), line, font=title_font, fill="#2f251d")
        title_y += line_height(title_font.size, 1.02)

    draw.text((160, title_y + 12), SUBTITLE, font=subtitle_font, fill="#6c5543")
    draw.text((160, title_y + 80), "Et hæfte med familiens retter og bagværk", font=strap_font, fill="#8b725f")
    draw.rounded_rectangle([160, title_y + 150, 720, title_y + 210], radius=18, fill="#ead9c7")
    draw.rounded_rectangle([760, title_y + 150, 1320, title_y + 210], radius=18, fill="#ead9c7")
    draw.text((184, title_y + 163), f"Version {version}", font=meta_font, fill="#5e4939")
    draw.text((784, title_y + 163), build_date_text, font=meta_font, fill="#5e4939")

    draw_cover_illustration(panel)

    return panel


def draw_contents(ordered: List[Recipe], page_map: Dict[str, int]) -> Image.Image:
    panel = Image.new("RGB", (A4_W, A4_H), "#fcfaf7")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A4_W - 28, A4_H - 28], radius=34, outline="#ddd3c8", width=3, fill="#fffdf9")

    title_font = load_font(96, "display")
    section_font = load_font(38, "sans-bold")
    body_font = load_font(36, "sans")
    small_font = load_font(30, "sans")

    draw.text((INNER_MARGIN, 140), "Indhold", font=title_font, fill="#2b241f")
    draw.text((INNER_MARGIN, 260), "Opskrifter", font=small_font, fill="#756a5f")

    y = 380
    current_section = None
    for recipe in ordered:
        if recipe.section != current_section:
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
        draw.line([INNER_MARGIN + 10, y + 50, A4_W - INNER_MARGIN, y + 50], fill="#ece4da", width=1)
        y += 64

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


def build() -> None:
    build_version = next_book_version()
    build_date_text = format_danish_date(date.today())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ordered = ordered_recipes()
    page_map, nutrition_map, raw_keys = build_markdown_and_page_map(ordered)
    write_contents_file(ordered, page_map)

    pages: List[Image.Image] = [draw_cover(build_version, build_date_text), draw_contents(ordered, page_map)]

    for recipe in ordered:
        per_100, kcal_per_portion, macro_pct = nutrition_map[recipe.title]
        pages.append(
            draw_recipe_page(
                recipe,
                per_100,
                kcal_per_portion,
                macro_pct,
                page_map[recipe.title],
            )
        )

    next_page_number = 3 + len(ordered)
    raw_index = 0
    while raw_index < len(raw_keys):
        table_page, raw_index = draw_raw_table_page(raw_keys, next_page_number, raw_index)
        pages.append(table_page)
        next_page_number += 1

    pages.append(draw_back_cover())

    while len(pages) % 4 != 0:
        pages.append(blank_page())

    pages[0].save(PDF_PATH, save_all=True, append_images=pages[1:], resolution=300.0)
    write_book_version(build_version)

    print(f"Skrev {len(ordered)} opskrifter i {RECIPES_DIR}")
    print(f"A4-sider: {len(pages)}")
    print(f"Forside: version {build_version}, dato {build_date_text}")
    print(f"PDF: {PDF_PATH}")


if __name__ == "__main__":
    build()
