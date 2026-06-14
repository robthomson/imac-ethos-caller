#!/usr/bin/env python3
"""
Add (or look up) a maneuver in seasons/catalog.json.

The catalog id ("phrase ID") is derived from the label and English TTS text,
e.g. "loop-6c260463" - so the same label+text always produces the same id,
and reusing an existing maneuver in a new sequence.json just means copying
its id, no catalog changes needed.

If the id doesn't exist yet, a new entry is added with the given English
text and English-text placeholders for fr/de/nl/cz, each flagged
"needs_translation": true. Translators then edit seasons/catalog.json
directly: fill in `text` and set `needs_translation` to false.

Usage:
    python catalog-add.py "Loop" "Loop. Outside entry, three-quarter opposite roll and quarter roll at the top."
    python catalog-add.py --reset basic "Basic sequence reset."
"""

import argparse
import hashlib
import json
import os
import re

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
CATALOG_PATH = os.path.join(REPO_ROOT, "seasons", "catalog.json")
LOCALES      = ["fr", "de", "nl", "cz"]


def slugify(text, max_len=24):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "x"


def phrase_id(label, text):
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"{slugify(label)}-{digest}"


def audio_id(fid, catalog, length=6):
    """Short, stable id used for the actual wav filename / sequences.lua
    (on-radio audio paths must stay short - see seasons/catalog.json)."""
    digest = hashlib.sha1(fid.encode("utf-8")).hexdigest()[:length]
    while any(e.get("audio") == digest for e in catalog.values()):
        length += 1
        digest = hashlib.sha1(fid.encode("utf-8")).hexdigest()[:length]
    return digest


def main():
    parser = argparse.ArgumentParser(description="Add or look up a maneuver in seasons/catalog.json")
    parser.add_argument("label", help="Figure label (e.g. 'Loop'), or class key with --reset")
    parser.add_argument("text", help="English TTS text")
    parser.add_argument("--reset", action="store_true",
                         help="Treat 'label' as a class key and create a reset-announcement entry")
    args = parser.parse_args()

    label = f"reset {args.label}" if args.reset else args.label
    fid = phrase_id(label, args.text)

    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    if fid in catalog:
        print(f"{fid}  (already in catalog)")
        return 0

    entry = {"label": label, "en": args.text, "audio": audio_id(fid, catalog)}
    for locale in LOCALES:
        entry[locale] = {"text": args.text, "needs_translation": True}
    catalog[fid] = entry

    with open(CATALOG_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    print(f"{fid}  (added)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
