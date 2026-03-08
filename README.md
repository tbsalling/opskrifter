# Henriettes opskrifter

Dette repo indeholder kildefilerne til en dansk kogebog samt en generator, der bygger den færdige PDF.

Kogebogen er sat op til:

- dansk sprog
- A4 i tværformat
- 2 opskrifter pr. side, så hver opskrift svarer til en A5-side i hæftet
- ensartet typografi, layout og næringsoplysninger

## Indhold

Repoet er organiseret sådan:

- [recipes](/Users/tbsalling/Documents/src/github/opskrifter/recipes) indeholder de renskrevne opskrifter i Markdown
- [scripts/build_cookbook.py](/Users/tbsalling/Documents/src/github/opskrifter/scripts/build_cookbook.py) genererer både Markdown-filer og den færdige PDF
- [output/kogebog.pdf](/Users/tbsalling/Documents/src/github/opskrifter/output/kogebog.pdf) er den byggede kogebog
- [INDHOLD.md](/Users/tbsalling/Documents/src/github/opskrifter/INDHOLD.md) er en indholdsoversigt med grupperede opskrifter og sidetal
- [AGENTS.md](/Users/tbsalling/Documents/src/github/opskrifter/AGENTS.md) beskriver de projektregler, der bruges til bogproduktionen

## Byg PDF fra kommandolinjen

Krav:

- `python3`
- Python-biblioteket `Pillow`

Kør generatoren fra repo-roden:

```bash
python3 scripts/build_cookbook.py
```

Når kommandoen er kørt:

- opskrifterne i [recipes](/Users/tbsalling/Documents/src/github/opskrifter/recipes) regenereres
- [INDHOLD.md](/Users/tbsalling/Documents/src/github/opskrifter/INDHOLD.md) opdateres
- den færdige PDF skrives til [output/kogebog.pdf](/Users/tbsalling/Documents/src/github/opskrifter/output/kogebog.pdf)

## Installér afhængighed

Hvis `Pillow` ikke allerede er installeret, kan det installeres sådan:

```bash
python3 -m pip install Pillow
```

## Arbejdsgang

Den typiske arbejdsgang er:

1. Opdatér opskriftsdata i [scripts/build_cookbook.py](/Users/tbsalling/Documents/src/github/opskrifter/scripts/build_cookbook.py).
2. Kør `python3 scripts/build_cookbook.py`.
3. Kontroller den genererede PDF i [output/kogebog.pdf](/Users/tbsalling/Documents/src/github/opskrifter/output/kogebog.pdf).

Generatoren sørger også for, at sideantallet i hæftet bliver deleligt med 4 ved at tilføje blanksider efter behov.
