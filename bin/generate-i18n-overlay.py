#!/usr/bin/env python3
"""
Scaffold/update per-locale TTS overlay files from a seasons/<year>/en.json source.

Reads:   seasons/<year>/en.json                (English master)
Writes:  seasons/<year>/<locale>.json          (per-locale TTS overlay)

For each class/figure in the master file, ensures a corresponding entry exists
in each locale overlay. New entries are added as English-text placeholders with
"needs_translation": true. Existing overlay entries (translated or not) are left
untouched, so this is safe to re-run after adding new years/figures.

Usage:
    python generate-i18n-overlay.py --year 2026 --locales fr de nl
    python generate-i18n-overlay.py --locales fr de nl     # all seasons/*/en.json
"""

import argparse
import glob
import json
import os

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT   = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
SEASONS_SRC = os.path.join(REPO_ROOT, "seasons")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def update_overlay(master, overlay_path):
    if os.path.exists(overlay_path):
        overlay = load_json(overlay_path)
    else:
        overlay = {"year": master["year"], "classes": {}}

    classes = overlay.setdefault("classes", {})
    for cls in master["classes"]:
        entry = classes.setdefault(cls["key"], {})
        if "reset_tts" not in entry:
            entry["reset_tts"] = {"text": cls["reset_tts"], "needs_translation": True}
        figures = entry.setdefault("figures", {})
        for fig in cls["figures"]:
            if fig["file"] not in figures:
                figures[fig["file"]] = {"text": fig["tts"], "needs_translation": True}

    write_json(overlay_path, overlay)
    print(f"  wrote {os.path.relpath(overlay_path, REPO_ROOT)}")


def process_year(json_path, locales):
    master = load_json(json_path)
    year = master["year"]
    year_dir = os.path.dirname(json_path)
    print(f"\n--- {year} ---")
    for locale in locales:
        overlay_path = os.path.join(year_dir, f"{locale}.json")
        update_overlay(master, overlay_path)


def main():
    parser = argparse.ArgumentParser(description="Scaffold per-locale TTS overlay files")
    parser.add_argument("--year", default=None, help="Process a single year (e.g. 2026)")
    parser.add_argument("--locales", nargs="+", required=True, help="Locale codes (e.g. fr de nl)")
    args = parser.parse_args()

    if args.year:
        json_path = os.path.join(SEASONS_SRC, args.year, "en.json")
        if not os.path.exists(json_path):
            print(f"ERROR: not found: {json_path}")
            return 1
        process_year(json_path, args.locales)
    else:
        paths = sorted(glob.glob(os.path.join(SEASONS_SRC, "*", "en.json")))
        if not paths:
            print(f"No */en.json files found under {SEASONS_SRC}")
            return 1
        for p in paths:
            process_year(p, args.locales)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
