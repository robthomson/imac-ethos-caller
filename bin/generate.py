#!/usr/bin/env python3
"""
Generate everything under src/imac-ethos-caller/ from the JSON sources at the
repo root. JSON is the single editing surface; nothing under src/ is hand-edited.

Reads:   i18n/strings.json                   UI chrome strings, per locale
         seasons/catalog.json                maneuver catalog: id -> label/translations
         seasons/<year>/sequence.json        per-year class/figure structure (catalog refs)

Writes:  src/imac-ethos-caller/i18n/<locale>.lua
         src/imac-ethos-caller/seasons/<year>/sequences.lua
         src/imac-ethos-caller/sounds/<locale>/<variant>/soundlist.csv

Each catalog entry's id is a "phrase ID" - a slug of its label plus a short
hash of its English text, e.g. "loop-6c260463". The same maneuver referenced
from multiple classes/years collapses to the same id, so its audio is only
generated once and shared. Audio files and sequences.lua use each entry's
short "audio" id (sounds/<locale>/<variant>/<audio>.wav) instead of the full
phrase ID, since the on-radio path (SCRIPTS:/imac-ethos-caller/sounds/...)
must stay short.

Usage:
    python generate.py                 # generate everything
    python generate.py --year 2026     # only (re)write that year's sequences.lua
"""

import argparse
import csv
import glob
import json
import os

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
SEASONS_SRC = os.path.join(REPO_ROOT, "seasons")
I18N_SRC    = os.path.join(REPO_ROOT, "i18n", "strings.json")

WIDGET_ROOT = os.path.join(REPO_ROOT, "src", "imac-ethos-caller")
SEASONS_OUT = os.path.join(WIDGET_ROOT, "seasons")
SOUNDS_OUT  = os.path.join(WIDGET_ROOT, "sounds")
I18N_OUT    = os.path.join(WIDGET_ROOT, "i18n")

SUPPORTED_LOCALES = ["en", "fr", "de", "nl"]
TRANSLATABLE_LOCALES = ["fr", "de", "nl"]

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


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def lua_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_i18n(strings):
    """Write src/imac-ethos-caller/i18n/<locale>.lua from i18n/strings.json."""
    keys = list(strings.keys())
    pad = max(len(k) for k in keys) + 1

    for locale in SUPPORTED_LOCALES:
        lines = ["return {"]
        for key in keys:
            value = strings[key].get(locale, strings[key]["en"])
            lines.append(f"    {key.ljust(pad)}= {lua_str(value)},")
        lines.append("}")
        lines.append("")

        os.makedirs(I18N_OUT, exist_ok=True)
        path = os.path.join(I18N_OUT, f"{locale}.lua")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
        print(f"  wrote {os.path.relpath(path, REPO_ROOT)}")


def write_sequences(catalog, sequence, out_dir):
    lines = []
    lines.append("return {")
    lines.append(f'    year    = "{sequence["year"]}",')
    lines.append("    classes = {")
    for cls in sequence["classes"]:
        lines.append("        {")
        lines.append(f'            key   = "{cls["key"]}",')
        lines.append(f'            name  = "{cls["name"]}",')
        lines.append(f'            reset = "{catalog[cls["reset"]]["audio"]}",')
        lines.append("            seq   = {")
        for fid in cls["figures"]:
            entry = catalog[fid]
            lines.append(f'                {{file="{entry["audio"]}", label="{entry["label"]}"}},')
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


def write_soundlists(catalog):
    """Write sounds/<locale>/<variant>/soundlist.csv from the catalog.

    "en" entries are always included. Translated-locale entries are included
    only when not flagged needs_translation, so generate-sounds.py never
    generates audio from untranslated placeholder text.
    """
    pools = {
        f"{locale}/{variant}": {}
        for locale, variants in LOCALE_VARIANTS.items()
        for variant in variants
    }

    for fid, entry in catalog.items():
        for variant in LOCALE_VARIANTS["en"]:
            pools[f"en/{variant}"][fid] = entry["en"]
        for locale in TRANSLATABLE_LOCALES:
            translation = entry.get(locale)
            if translation and not translation.get("needs_translation", True):
                for variant in LOCALE_VARIANTS[locale]:
                    pools[f"{locale}/{variant}"][fid] = translation["text"]

    for locale_variant, entries in sorted(pools.items()):
        if not entries:
            continue
        out_dir = os.path.join(SOUNDS_OUT, locale_variant)
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "soundlist.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "text"])
            for fid in sorted(entries):
                audio = catalog[fid]["audio"]
                writer.writerow([f"{locale_variant}/{audio}.wav", entries[fid]])
        print(f"  wrote {os.path.relpath(path, REPO_ROOT)} ({len(entries)} entries)")


def main():
    parser = argparse.ArgumentParser(description="Generate src/imac-ethos-caller/ from JSON sources")
    parser.add_argument("--year", default=None, help="Only (re)write this year's sequences.lua (e.g. 2026)")
    args = parser.parse_args()

    catalog = load_json(os.path.join(SEASONS_SRC, "catalog.json"))

    print("--- i18n ---")
    write_i18n(load_json(I18N_SRC))

    print("\n--- sequences ---")
    if args.year:
        seq_path = os.path.join(SEASONS_SRC, args.year, "sequence.json")
        if not os.path.exists(seq_path):
            print(f"ERROR: not found: {seq_path}")
            return 1
        seq_paths = [seq_path]
    else:
        seq_paths = sorted(glob.glob(os.path.join(SEASONS_SRC, "*", "sequence.json")))
        if not seq_paths:
            print(f"No */sequence.json files found under {SEASONS_SRC}")
            return 1

    for seq_path in seq_paths:
        year = os.path.basename(os.path.dirname(seq_path))
        sequence = load_json(seq_path)
        write_sequences(catalog, sequence, os.path.join(SEASONS_OUT, year))

    print("\n--- sound catalog ---")
    write_soundlists(catalog)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
