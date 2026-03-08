#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RECIPES_DIR = ROOT / "recipes"
OUTPUT_DIR = ROOT / "output"
PDF_PATH = OUTPUT_DIR / "kogebog.pdf"

A4_W, A4_H = 3508, 2480
A5_W, A5_H = A4_W // 2, A4_H
OUTER_MARGIN = 70
INNER_MARGIN = 96
TITLE = "[INDSÆT TITEL HER]"


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
    "cheddar": Nutrient(403, 25, 1.3, 33),
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
    "sukker": Nutrient(400, 0, 100, 0),
    "brun_farin": Nutrient(380, 0, 98, 0),
    "æble": Nutrient(52, 0.3, 14, 0.2),
    "cidereddike": Nutrient(21, 0, 0.9, 0),
    "æblejuice": Nutrient(46, 0.1, 11, 0.1),
}

DISPLAY_NAMES = {
    "surdej": "Surdej",
    "gær": "Gær",
    "hvedemel": "Hvedemel",
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
    "cheddar": "Cheddar",
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
    "sukker": "Sukker",
    "brun_farin": "Brun farin",
    "æble": "Æble",
    "cidereddike": "Æblecidereddike",
    "æblejuice": "Æblejuice",
}

SECTION_STYLES = {
    "Bagværk": SectionStyle("#38261d", "#f5ede4", "#c87f4f", "#e6d2be"),
    "Tilbehør": SectionStyle("#18332b", "#edf5f0", "#5d8f77", "#d5e6dc"),
    "Aftensmad": SectionStyle("#2f1f17", "#f8eee8", "#bf6845", "#eed1c3"),
    "Weekend": SectionStyle("#1d2530", "#edf1f6", "#7288a4", "#d5ddea"),
}


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
            "150 g grahamsmel",
            "450 g hvedemel",
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
        nutrient_items=[("surdej", 200), ("grahamsmel", 150), ("hvedemel", 450), ("gær", 1)],
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
        section="Weekend",
        title="Aligot",
        servings=4,
        finished_weight_g=1650,
        ingredients=[
            "1 kg melede kartofler",
            "2 fed hvidløg, valgfrit",
            "50 g smør",
            "2,5 dl varm fløde",
            "350 g ost, fx tomme fraîche, mozzarella og emmentaler",
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
        nutrient_items=[("kartoffel", 1000), ("hvidløg", 6), ("smør", 50), ("fløde_38", 250), ("mozzarella", 350)],
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
    lines = [
        f"# {recipe.title}",
        "",
        f"- Kategori: {recipe.section}",
        f"- Portioner: {recipe.servings}",
        "",
        "## Ingredienser",
    ]
    lines.extend([f"- {item}" for item in recipe.ingredients])
    lines.extend(["", "## Fremgangsmåde"])
    lines.extend([f"{index}. {step}" for index, step in enumerate(recipe.method, start=1)])
    lines.extend(
        [
            "",
            "## Næringsestimat",
            f"- Energi pr. 100 g: {round(per_100['kcal'])} kcal",
            f"- Energi pr. portion: {round(kcal_per_portion)} kcal",
            (
                "- Makro pr. 100 g: "
                f"Protein {per_100['protein']:.1f} g, "
                f"Kulhydrat {per_100['carbs']:.1f} g, "
                f"Fedt {per_100['fat']:.1f} g"
            ),
            (
                "- Makro i energiprocent: "
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
    draw.ellipse([A5_W - 520, -120, A5_W - 40, 360], outline=style.soft, width=4)
    draw.ellipse([A5_W - 440, -40, A5_W + 80, 480], outline=style.soft, width=2)
    draw.ellipse([60, A5_H - 400, 420, A5_H - 40], outline=style.soft, width=3)
    draw.line([OUTER_MARGIN, 160, A5_W - OUTER_MARGIN, 160], fill=style.soft, width=3)


def section_label(section: str) -> str:
    labels = {
        "Bagværk": "Bagværk",
        "Tilbehør": "Tilbehør",
        "Aftensmad": "Aftensmad",
        "Weekend": "Weekendret",
    }
    return labels[section]


def fit_recipe_fonts(recipe: Recipe, draw: ImageDraw.ImageDraw, column_width: int, body_top: int, footer_h: int):
    for size in [33, 31, 29, 27, 25, 23]:
        title_font = load_font(size + 18, "display")
        chip_font = load_font(size - 3, "sans-bold")
        section_font = load_font(size - 4, "sans-bold")
        body_font = load_font(size, "sans")
        body_bold = load_font(size, "sans-bold")
        small_font = load_font(size - 4, "sans")

        body_line = line_height(size, 1.28)
        small_line = line_height(size - 4, 1.26)

        left_height = body_line * 2
        for ingredient in recipe.ingredients:
            left_height += len(wrap_text(draw, f"• {ingredient}", body_font, column_width - 28)) * body_line

        right_height = body_line * 2
        for index, step in enumerate(recipe.method, start=1):
            right_height += len(wrap_text(draw, f"{index}. {step}", body_font, column_width - 28)) * body_line

        title_lines = wrap_text(draw, recipe.title, title_font, A5_W - 2 * INNER_MARGIN - 60)
        title_height = len(title_lines) * line_height(size + 18, 1.08)
        header_height = 290 + title_height
        needed = body_top + max(left_height, right_height) + footer_h + small_line * 3
        if needed < A5_H - OUTER_MARGIN:
            return {
                "title": title_font,
                "chip": chip_font,
                "section": section_font,
                "body": body_font,
                "body_bold": body_bold,
                "small": small_font,
                "body_line": body_line,
                "small_line": small_line,
                "title_height": title_height,
                "header_height": header_height,
            }
    raise RuntimeError(f"Kunne ikke få opskriften til at passe på siden: {recipe.title}")


def draw_tag(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, font, fill: str, ink: str) -> None:
    x, y = xy
    bbox = draw.textbbox((x, y), text, font=font)
    width = bbox[2] - bbox[0] + 38
    height = bbox[3] - bbox[1] + 20
    draw.rounded_rectangle([x, y, x + width, y + height], radius=18, fill=fill)
    draw.text((x + 19, y + 10), text, font=font, fill=ink)


def draw_text_block(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, text: str, font, fill: str, step: int):
    current_y = y
    for line in wrap_text(draw, text, font, width):
        draw.text((x, current_y), line, font=font, fill=fill)
        current_y += step
    return current_y


def draw_recipe_page(recipe: Recipe, per_100: dict, kcal_per_portion: float, macro_pct: dict, page_number: int) -> Image.Image:
    style = SECTION_STYLES[recipe.section]
    panel = Image.new("RGB", (A5_W, A5_H), "#fcfaf7")
    draw = ImageDraw.Draw(panel)

    draw.rounded_rectangle(
        [28, 28, A5_W - 28, A5_H - 28],
        radius=34,
        outline=style.soft,
        width=3,
        fill="#fffdf9",
    )
    draw_pattern(draw, style)
    draw.rounded_rectangle(
        [OUTER_MARGIN, OUTER_MARGIN, A5_W - OUTER_MARGIN, 240],
        radius=40,
        fill=style.panel,
    )

    left_x = INNER_MARGIN
    top_y = 120
    section_font = load_font(28, "sans-bold")
    draw_tag(draw, (left_x, top_y), section_label(recipe.section), section_font, style.accent, "#fffdf9")

    sizing = fit_recipe_fonts(recipe, draw, 520, 720, 300)
    title_font = sizing["title"]
    chip_font = sizing["chip"]
    body_font = sizing["body"]
    body_bold = sizing["body_bold"]
    small_font = sizing["small"]
    body_line = sizing["body_line"]
    small_line = sizing["small_line"]

    title_y = 215
    for line in wrap_text(draw, recipe.title, title_font, A5_W - 2 * INNER_MARGIN - 30):
        draw.text((left_x, title_y), line, font=title_font, fill=style.ink)
        title_y += line_height(title_font.size, 1.05)

    meta_y = title_y + 16
    draw_tag(draw, (left_x, meta_y), f"{recipe.servings} portioner", chip_font, style.soft, style.ink)
    draw_tag(draw, (left_x + 220, meta_y), f"{round(kcal_per_portion)} kcal/portion", chip_font, style.soft, style.ink)

    header_bottom = meta_y + 88
    column_gap = 40
    content_x = INNER_MARGIN
    content_w = A5_W - 2 * INNER_MARGIN
    ingredients_w = int(content_w * 0.38)
    method_w = content_w - ingredients_w - column_gap
    ingredients_x = content_x
    method_x = ingredients_x + ingredients_w + column_gap
    body_y = header_bottom + 40

    draw.rounded_rectangle(
        [ingredients_x, body_y, ingredients_x + ingredients_w, A5_H - 420],
        radius=24,
        fill="#fff7ef",
        outline=style.soft,
        width=2,
    )
    draw.rounded_rectangle(
        [method_x, body_y, method_x + method_w, A5_H - 420],
        radius=24,
        fill="#ffffff",
        outline=style.soft,
        width=2,
    )

    draw.text((ingredients_x + 28, body_y + 26), "Ingredienser", font=body_bold, fill=style.ink)
    draw.text((method_x + 28, body_y + 26), "Fremgangsmåde", font=body_bold, fill=style.ink)
    draw.line(
        [ingredients_x + 28, body_y + 76, ingredients_x + ingredients_w - 28, body_y + 76],
        fill=style.soft,
        width=2,
    )
    draw.line(
        [method_x + 28, body_y + 76, method_x + method_w - 28, body_y + 76],
        fill=style.soft,
        width=2,
    )

    cursor_left = body_y + 96
    for ingredient in recipe.ingredients:
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

    cursor_right = body_y + 96
    for index, step in enumerate(recipe.method, start=1):
        cursor_right = draw_text_block(
            draw,
            method_x + 28,
            cursor_right,
            method_w - 56,
            f"{index}. {step}",
            body_font,
            "#2d2a26",
            body_line,
        )
        cursor_right += int(body_line * 0.15)

    footer_top = A5_H - 360
    draw.rounded_rectangle(
        [INNER_MARGIN, footer_top, A5_W - INNER_MARGIN, A5_H - 110],
        radius=28,
        fill=style.ink,
    )
    draw.text((INNER_MARGIN + 32, footer_top + 26), "Næringsestimat", font=body_bold, fill="#fffdf9")
    draw.text(
        (INNER_MARGIN + 32, footer_top + 76),
        f"Energi pr. 100 g: {round(per_100['kcal'])} kcal",
        font=small_font,
        fill="#fffdf9",
    )
    draw.text(
        (INNER_MARGIN + 32, footer_top + 112),
        f"Energi pr. portion: {round(kcal_per_portion)} kcal",
        font=small_font,
        fill="#fffdf9",
    )
    draw.text(
        (INNER_MARGIN + 32, footer_top + 160),
        (
            f"Makro pr. 100 g: Protein {per_100['protein']:.1f} g  "
            f"Kulhydrat {per_100['carbs']:.1f} g  "
            f"Fedt {per_100['fat']:.1f} g"
        ),
        font=small_font,
        fill="#fffdf9",
    )
    draw.text(
        (INNER_MARGIN + 32, footer_top + 196),
        (
            f"Makro i energiprocent: Protein {macro_pct['protein']:.0f} %  "
            f"Kulhydrat {macro_pct['carbs']:.0f} %  "
            f"Fedt {macro_pct['fat']:.0f} %"
        ),
        font=small_font,
        fill="#fffdf9",
    )

    page_font = load_font(24, "sans")
    page_text = f"side {page_number}"
    bbox = draw.textbbox((0, 0), page_text, font=page_font)
    draw.text((A5_W - INNER_MARGIN - (bbox[2] - bbox[0]), A5_H - 84), page_text, font=page_font, fill="#857a6c")
    return panel


def draw_cover() -> Image.Image:
    panel = Image.new("RGB", (A5_W, A5_H), "#f6efe5")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A5_W - 28, A5_H - 28], radius=34, outline="#d9c7b4", width=3, fill="#f9f4ec")
    draw.rounded_rectangle([90, 90, A5_W - 90, A5_H - 90], radius=40, outline="#caa587", width=3)

    draw.ellipse([A5_W - 610, 140, A5_W - 120, 620], outline="#d7b99d", width=4)
    draw.ellipse([A5_W - 520, 220, A5_W - 30, 710], outline="#ead7c5", width=2)

    title_font = load_font(104, "display")
    sub_font = load_font(34, "sans")
    draw.text((160, 320), TITLE, font=title_font, fill="#2e241c")
    draw.text((160, 470), "Dansk opskriftshæfte", font=sub_font, fill="#6a5442")
    draw.text((160, 520), "trykklart layout i A4 tværformat med A5-opslag", font=sub_font, fill="#8d7765")

    # Minimalistisk råvaretegning
    draw.line([230, 760, 230, 1300], fill="#3b2a1f", width=5)
    draw.line([230, 860, 150, 800], fill="#3b2a1f", width=4)
    draw.line([230, 920, 135, 860], fill="#3b2a1f", width=4)
    draw.line([230, 980, 150, 930], fill="#3b2a1f", width=4)
    draw.line([230, 1040, 145, 990], fill="#3b2a1f", width=4)
    draw.line([230, 860, 310, 800], fill="#3b2a1f", width=4)
    draw.line([230, 920, 325, 860], fill="#3b2a1f", width=4)
    draw.line([230, 980, 310, 930], fill="#3b2a1f", width=4)
    draw.line([230, 1040, 315, 990], fill="#3b2a1f", width=4)

    draw.ellipse([520, 840, 770, 1080], outline="#3b2a1f", width=5)
    draw.line([650, 835, 700, 760], fill="#3b2a1f", width=4)
    draw.arc([480, 1040, 820, 1320], start=195, end=340, fill="#3b2a1f", width=5)

    draw.line([1000, 760, 1000, 1180], fill="#3b2a1f", width=5)
    draw.line([1000, 840, 930, 790], fill="#3b2a1f", width=4)
    draw.line([1000, 900, 1075, 850], fill="#3b2a1f", width=4)
    draw.line([1000, 960, 930, 910], fill="#3b2a1f", width=4)
    draw.line([1000, 1020, 1075, 970], fill="#3b2a1f", width=4)
    draw.line([1000, 1080, 940, 1030], fill="#3b2a1f", width=4)

    draw.text((160, A5_H - 190), "Samlet, standardiseret og sat op til print", font=load_font(30, "sans"), fill="#6a5442")
    return panel


def draw_contents(ordered: List[Recipe], page_map: Dict[str, int]) -> Image.Image:
    panel = Image.new("RGB", (A5_W, A5_H), "#fcfaf7")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A5_W - 28, A5_H - 28], radius=34, outline="#ddd3c8", width=3, fill="#fffdf9")

    title_font = load_font(78, "display")
    section_font = load_font(30, "sans-bold")
    body_font = load_font(29, "sans")
    small_font = load_font(24, "sans")

    draw.text((INNER_MARGIN, 140), "Indhold", font=title_font, fill="#2b241f")
    draw.text((INNER_MARGIN, 240), "Opskrifterne er grupperet efter type for et mere læsbart hæfte.", font=small_font, fill="#756a5f")

    y = 340
    current_section = None
    for recipe in ordered:
        if recipe.section != current_section:
            current_section = recipe.section
            style = SECTION_STYLES[current_section]
            draw.rounded_rectangle([INNER_MARGIN, y, A5_W - INNER_MARGIN, y + 52], radius=18, fill=style.panel)
            draw.text((INNER_MARGIN + 18, y + 10), current_section, font=section_font, fill=style.ink)
            y += 76

        draw.text((INNER_MARGIN + 10, y), recipe.title, font=body_font, fill="#2d2a26")
        number_text = str(page_map[recipe.title])
        bbox = draw.textbbox((0, 0), number_text, font=body_font)
        number_x = A5_W - INNER_MARGIN - (bbox[2] - bbox[0])
        draw.text((number_x, y), number_text, font=body_font, fill="#7f7266")
        draw.line([INNER_MARGIN + 10, y + 40, A5_W - INNER_MARGIN, y + 40], fill="#ece4da", width=1)
        y += 52

    draw.text((A5_W - 170, A5_H - 84), "side 2", font=small_font, fill="#857a6c")
    return panel


def draw_raw_table_page(keys: List[str], page_number: int, start_index: int) -> Tuple[Image.Image, int]:
    panel = Image.new("RGB", (A5_W, A5_H), "#fbfaf8")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A5_W - 28, A5_H - 28], radius=34, outline="#d6dbe0", width=3, fill="#fffdf9")

    title_font = load_font(68, "display")
    header_font = load_font(28, "sans-bold")
    row_font = load_font(28, "sans")
    small_font = load_font(24, "sans")

    draw.text((INNER_MARGIN, 130), "Råvarer og energi", font=title_font, fill="#24313c")
    draw.text((INNER_MARGIN, 215), "Energiindhold pr. 100 g for de råvarer, der indgår i hæftet.", font=small_font, fill="#66727d")

    col1_x = INNER_MARGIN
    col2_x = 980
    top = 320
    draw.text((col1_x, top), "Råvare", font=header_font, fill="#24313c")
    draw.text((col1_x + 520, top), "kcal", font=header_font, fill="#24313c")
    draw.text((col2_x, top), "Råvare", font=header_font, fill="#24313c")
    draw.text((col2_x + 520, top), "kcal", font=header_font, fill="#24313c")
    top += 50
    draw.line([col1_x, top, A5_W - INNER_MARGIN, top], fill="#cfd6dc", width=2)
    top += 24

    row_h = 44
    left_y = top
    right_y = top
    index = start_index

    while index < len(keys):
        target_x = col1_x if left_y <= right_y else col2_x
        target_y = left_y if left_y <= right_y else right_y
        if target_y + row_h > A5_H - 150:
            if target_x == col1_x and right_y <= left_y:
                target_x = col2_x
                target_y = right_y
            else:
                break

        key = keys[index]
        draw.text((target_x, target_y), DISPLAY_NAMES.get(key, key), font=row_font, fill="#2d2a26")
        draw.text((target_x + 520, target_y), str(round(NDB[key].kcal)), font=row_font, fill="#2d2a26")
        if target_x == col1_x:
            left_y += row_h
        else:
            right_y += row_h
        index += 1

    draw.text((A5_W - 170, A5_H - 84), f"side {page_number}", font=small_font, fill="#857a6c")
    return panel, index


def draw_back_cover() -> Image.Image:
    panel = Image.new("RGB", (A5_W, A5_H), "#f2f5f8")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A5_W - 28, A5_H - 28], radius=34, outline="#cfd7df", width=3, fill="#f7fafc")

    title_font = load_font(72, "display")
    body_font = load_font(32, "sans")
    small_font = load_font(24, "sans")

    draw.text((INNER_MARGIN, 260), "Kogebogen er sat op", font=title_font, fill="#223241")
    draw.text((INNER_MARGIN, 360), "til print, hæftning og køkkenbrug.", font=title_font, fill="#223241")

    draw.rounded_rectangle([INNER_MARGIN, 620, A5_W - INNER_MARGIN, 980], radius=26, fill="#e8eef4")
    draw.text((INNER_MARGIN + 36, 670), "Format", font=body_font, fill="#223241")
    draw.text((INNER_MARGIN + 36, 725), "A4 tværformat med 2 A5-sider pr. ark", font=body_font, fill="#4f6376")
    draw.text((INNER_MARGIN + 36, 815), "Udtryk", font=body_font, fill="#223241")
    draw.text((INNER_MARGIN + 36, 870), "Renskrevet, standardiseret og ernæringsberegnet", font=body_font, fill="#4f6376")

    draw.text(
        (INNER_MARGIN, A5_H - 150),
        "Dannet med hjælp fra AI: OpenAI GPT-5, Codex-agent.",
        font=small_font,
        fill="#6c7a88",
    )
    return panel


def blank_page() -> Image.Image:
    panel = Image.new("RGB", (A5_W, A5_H), "#fffdf9")
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle([28, 28, A5_W - 28, A5_H - 28], radius=34, outline="#ece5dc", width=2, fill="#fffdf9")
    return panel


def compose_spread(left: Image.Image, right: Image.Image) -> Image.Image:
    spread = Image.new("RGB", (A4_W, A4_H), "#f4efe9")
    spread.paste(left, (0, 0))
    spread.paste(right, (A5_W, 0))
    draw = ImageDraw.Draw(spread)
    draw.rectangle([A5_W - 2, 0, A5_W + 2, A4_H], fill="#e8dfd5")
    return spread


def build_markdown_and_page_map(ordered: List[Recipe]):
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)

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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ordered = ordered_recipes()
    page_map, nutrition_map, raw_keys = build_markdown_and_page_map(ordered)
    write_contents_file(ordered, page_map)

    a5_pages: List[Image.Image] = [draw_cover(), draw_contents(ordered, page_map)]

    for recipe in ordered:
        per_100, kcal_per_portion, macro_pct = nutrition_map[recipe.title]
        a5_pages.append(
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
        a5_pages.append(table_page)
        next_page_number += 1

    a5_pages.append(draw_back_cover())

    while len(a5_pages) % 4 != 0:
        a5_pages.append(blank_page())

    spreads = []
    for index in range(0, len(a5_pages), 2):
        spreads.append(compose_spread(a5_pages[index], a5_pages[index + 1]))

    spreads[0].save(PDF_PATH, save_all=True, append_images=spreads[1:], resolution=300.0)

    print(f"Skrev {len(ordered)} opskrifter i {RECIPES_DIR}")
    print(f"A5-sider: {len(a5_pages)}")
    print(f"A4-sider i PDF: {len(spreads)}")
    print(f"PDF: {PDF_PATH}")


if __name__ == "__main__":
    build()
