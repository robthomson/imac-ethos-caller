#!/usr/bin/env python3
"""
Generate sequences.lua and soundlist.csv files from a seasons/<year>/en.json source.

Reads:   seasons/<year>/en.json                (repo root, not deployed)
         seasons/<year>/<locale>.json          (per-locale TTS overlay, optional)
Writes:  src/imac-ethos-caller/seasons/<year>/sequences.lua
         src/imac-ethos-caller/seasons/<year>/<class>/<locale>/<variant>/soundlist.csv

For each locale overlay file that exists, only entries with
"needs_translation": false are written to the locale soundlist, so
generate-sounds.py never generates audio from untranslated placeholder text.

Every locale is written under <class>/<locale>/<variant>/, one soundlist.csv
per variant, matching the folder layout of rfsuite's sound-generator soundpacks
(see LOCALE_VARIANTS). Locales with only one radio voice pack still get a
"default" variant subfolder for consistency (e.g. "de/default").

Usage:
    python generate-season.py                 # process all seasons/*/en.json
    python generate-season.py --year 2026     # process one year only
"""

import argparse
import csv
import glob
import json
import os

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
SEASONS_SRC = os.path.join(REPO_ROOT, "seasons")
SEASONS_OUT = os.path.join(REPO_ROOT, "src", "imac-ethos-caller", "seasons")
LOCALES     = ["fr", "de", "nl"]

# Voice variant folders per locale, matching the official Ethos audio pack
# names used by rfsuite's sound-generator soundpacks (see
# rotorflight-lua-ethos-suite/bin/sound-generator/generate-all.bat). Locales
# with only one radio voice pack still get a "default" variant folder.
LOCALE_VARIANTS = {
    "en": ["us", "gb"],
    "fr": ["femme", "homme"],
    "de": ["default"],
    "nl": ["default"],
}


def write_lua(data, out_dir):
    year = data["year"]
    lines = []
    lines.append("return {")
    lines.append(f'    year    = "{year}",')
    lines.append("    classes = {")
    for cls in data["classes"]:
        lines.append("        {")
        lines.append(f'            key  = "{cls["key"]}",')
        lines.append(f'            name = "{cls["name"]}",')
        lines.append("            seq  = {")
        for fig in cls["figures"]:
            lines.append(f'                {{file="{fig["file"]}", label="{fig["label"]}"}},')
        lines.append("            },")
        lines.append("        },")
    lines.append("    },")
    lines.append("}")
    lines.append("")

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "sequences.lua")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"  wrote {os.path.relpath(path, REPO_ROOT)}")


def write_csv(data, out_dir):
    year = data["year"]
    for cls in data["classes"]:
        for variant in LOCALE_VARIANTS["en"]:
            cls_dir = os.path.join(out_dir, cls["key"], "en", variant)
            os.makedirs(cls_dir, exist_ok=True)
            path = os.path.join(cls_dir, "soundlist.csv")
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "text"])
                writer.writerow([f"{year}/{cls['key']}/en/{variant}/rst.wav", cls["reset_tts"]])
                for fig in cls["figures"]:
                    writer.writerow([f"{year}/{cls['key']}/en/{variant}/{fig['file']}.wav", fig["tts"]])
            print(f"  wrote {os.path.relpath(path, REPO_ROOT)}")


def write_locale_csv(year, locale, overlay, out_dir):
    variants = LOCALE_VARIANTS.get(locale, ["default"])
    for cls_key, cls_data in overlay.get("classes", {}).items():
        reset_tts = cls_data.get("reset_tts")
        figures = cls_data.get("figures", {})

        for variant in variants:
            rows = []
            if reset_tts and not reset_tts.get("needs_translation", True):
                rows.append([f"{year}/{cls_key}/{locale}/{variant}/rst.wav", reset_tts["text"]])
            for file, fig in figures.items():
                if not fig.get("needs_translation", True):
                    rows.append([f"{year}/{cls_key}/{locale}/{variant}/{file}.wav", fig["text"]])

            if not rows:
                continue

            cls_dir = os.path.join(out_dir, cls_key, locale, variant)
            os.makedirs(cls_dir, exist_ok=True)
            path = os.path.join(cls_dir, "soundlist.csv")
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["filename", "text"])
                writer.writerows(rows)
            print(f"  wrote {os.path.relpath(path, REPO_ROOT)}")


def process_locales(year, year_src_dir, out_dir):
    for locale in LOCALES:
        overlay_path = os.path.join(year_src_dir, f"{locale}.json")
        if not os.path.exists(overlay_path):
            continue
        with open(overlay_path, encoding="utf-8") as f:
            overlay = json.load(f)
        write_locale_csv(year, locale, overlay, out_dir)


def process_year(json_path):
    year_src_dir = os.path.dirname(json_path)
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    year = data["year"]
    print(f"\n--- {year} ---")
    out_dir = os.path.join(SEASONS_OUT, year)
    write_lua(data, out_dir)
    write_csv(data, out_dir)
    process_locales(year, year_src_dir, out_dir)


def main():
    parser = argparse.ArgumentParser(description="Generate Lua + CSV files from sequences.json")
    parser.add_argument("--year", default=None, help="Process a single year (e.g. 2026)")
    args = parser.parse_args()

    if args.year:
        json_path = os.path.join(SEASONS_SRC, args.year, "en.json")
        if not os.path.exists(json_path):
            print(f"ERROR: not found: {json_path}")
            return 1
        process_year(json_path)
    else:
        paths = sorted(glob.glob(os.path.join(SEASONS_SRC, "*", "en.json")))
        if not paths:
            print(f"No */en.json files found under {SEASONS_SRC}")
            return 1
        for p in paths:
            process_year(p)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
