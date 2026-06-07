#!/usr/bin/env python3
"""
Generate sequences.lua and soundlist.csv files from a seasons/<year>.json source.

Reads:   seasons/<year>.json                  (repo root, not deployed)
Writes:  src/imac-ethos-caller/seasons/<year>/sequences.lua
         src/imac-ethos-caller/seasons/<year>/<class>/soundlist.csv

Usage:
    python generate-season.py                 # process all seasons/*.json
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
        cls_dir = os.path.join(out_dir, cls["key"])
        os.makedirs(cls_dir, exist_ok=True)
        path = os.path.join(cls_dir, "soundlist.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "text"])
            writer.writerow([f"{year}/{cls['key']}/rst.wav", cls["reset_tts"]])
            for fig in cls["figures"]:
                writer.writerow([f"{year}/{cls['key']}/{fig['file']}.wav", fig["tts"]])
        print(f"  wrote {os.path.relpath(path, REPO_ROOT)}")


def process_year(json_path):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    year = data["year"]
    print(f"\n--- {year} ---")
    out_dir = os.path.join(SEASONS_OUT, year)
    write_lua(data, out_dir)
    write_csv(data, out_dir)


def main():
    parser = argparse.ArgumentParser(description="Generate Lua + CSV files from sequences.json")
    parser.add_argument("--year", default=None, help="Process a single year (e.g. 2026)")
    args = parser.parse_args()

    if args.year:
        json_path = os.path.join(SEASONS_SRC, f"{args.year}.json")
        if not os.path.exists(json_path):
            print(f"ERROR: not found: {json_path}")
            return 1
        process_year(json_path)
    else:
        paths = sorted(glob.glob(os.path.join(SEASONS_SRC, "*.json")))
        if not paths:
            print(f"No .json files found under {SEASONS_SRC}")
            return 1
        for p in paths:
            process_year(p)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
