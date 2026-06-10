# IMAC Ethos Caller

An FrSky Ethos widget that calls IMAC aerobatic competition sequences via audio on the radio. Select a year and class, then use a switch to announce each maneuver in order as you fly.

## Features

- Supports all 8 IMAC classes: Basic, Sportsman, Intermediate, Intermediate ALT, Advanced, Advanced ALT, Unlimited, Unlimited ALT
- Per-year sequence files — adding a new season never touches existing data
- Progress bar shows current maneuver position through the sequence
- Three configurable switches: Trigger (next maneuver), Repeat (replay current), Reset (restart sequence)
- Sequence data for 2026 included with real figure names from official IMAC PDFs

## Radio Requirements

- FrSky Ethos firmware (tested on X20S)
- Sound files must be 16 kHz mono A-law WAV format

## Installation

1. Download the latest release ZIP from the [Releases](../../releases) page
2. Extract to the root of your radio's SD card — the widget lands at `/scripts/imac-ethos-caller/`
3. Add the **IMAC Caller** widget to a screen via the Ethos widget menu

## Configuration

Long-press the widget to open settings:

| Field | Description |
|---|---|
| Routine | Year + class combination (e.g. "2026 Advanced") |
| Trigger Switch | Advances to the next maneuver and announces it |
| Repeat Switch | Re-announces the current maneuver |
| Reset Switch | Resets to the start and announces the class reset |
| Language | UI/audio language: Auto (follows the radio's locale), English, Français, Deutsch, Nederlands |

## Languages

The widget UI is available in English, French, German, and Dutch. By default
("Auto") it follows the radio's locale (`system.getLocale()`), falling back to
English for any unsupported locale. You can override this with the
**Language** field in the widget settings.

IMAC class names (Basic, Sportsman, Advanced, …) and figure/maneuver names
(Loop, Hammerhead, Immelmann, …) are always shown in English — these are
standard FAI/IMAC competition terms pilots recognize from official sequence
sheets, regardless of UI language.

Spoken call-outs currently exist in English only. Translated audio for other
languages can be added incrementally (see [Adding a New
Year](#adding-a-new-year) and [Generating Sound Files](#generating-sound-files))
without any further code changes — until then, all languages fall back to the
English audio.

## Generating Sound Files

Sound files are pre-built and included in releases. To regenerate or add new ones:

**Prerequisites**

```
pip install google-cloud-texttospeech sox
```

Google Cloud Application Default Credentials must be configured (run `gcloud auth application-default login` once).

**Run**

```cmd
bin\generate-sounds.cmd
```

This scans all `soundlist.csv` files under `src/imac-ethos-caller/seasons/` and generates any missing WAV files, including any per-locale `<class>/<lang>/soundlist.csv` files (see [Adding Translated Audio](#adding-translated-audio) below). To regenerate everything: delete the WAV files first, then run again.

The voice used is chosen automatically per CSV based on its locale (`LOCALE_VOICES` in `bin/generate-sounds.py`). Pass `--voice <name>` to override the voice for all CSVs in the run.

## Adding a New Year

The `seasons/` folder at the repo root is the editing surface — nothing in it is deployed to the radio.

1. Create `seasons/<year>/en.json` following the structure of [seasons/2026/en.json](seasons/2026/en.json)
2. Run `bin\generate-season.cmd` — this writes `sequences.lua` and all `soundlist.csv` files into `src/`
3. Run `bin\generate-sounds.cmd` to produce the WAV files

The widget auto-discovers year folders at runtime — no code changes needed.

Never edit `sequences.lua` or `soundlist.csv` directly — they are generated from the JSON and will be overwritten.

## Adding Translated Audio

Spoken call-out text for each locale lives in per-locale overlay files
`seasons/<year>/<lang>.json` (e.g. `seasons/2026/fr.json`), one per supported
non-English language (fr, de, nl). These are scaffolded/updated from the
English master via:

```cmd
python bin\generate-i18n-overlay.py --year 2026 --locales fr de nl
```

This adds an English-text placeholder entry with `"needs_translation": true`
for every class `reset_tts` and figure `tts` that doesn't already have an
overlay entry — existing entries (translated or not) are left untouched, so
it's safe to re-run after adding new years or figures.

To translate:

1. Edit the `text` field for a class/figure entry in `seasons/<year>/<lang>.json`
2. Set `"needs_translation": false`
3. Run `bin\generate-season.cmd` — this writes
   `src/imac-ethos-caller/seasons/<year>/<class>/<lang>/soundlist.csv`, but
   only for entries with `needs_translation: false`
4. Run `bin\generate-sounds.cmd` to generate the translated WAV files

Entries still flagged `needs_translation: true` are skipped — no CSV row and
no audio is generated for them, so the widget keeps falling back to the
English audio for those maneuvers.

## Project Structure

```
seasons/                            # Editing surface — not deployed
└── 2026/
    ├── en.json                     # Single source of truth for labels, TTS, and structure
    ├── fr.json                     # Per-locale TTS overlay (placeholders + needs_translation)
    ├── de.json
    └── nl.json

src/imac-ethos-caller/             # Deployed to radio
├── main.lua                        # Widget entry point
├── i18n/
│   ├── i18n.lua                    # Runtime locale loader/translate helper
│   ├── en.lua                      # UI strings per locale
│   ├── fr.lua
│   ├── de.lua
│   └── nl.lua
└── seasons/
    └── 2026/
        ├── sequences.lua           # Generated from JSON
        ├── basic/
        │   ├── en/
        │   │   ├── soundlist.csv   # Generated from en.json
        │   │   └── rst.wav, mnvr01.wav ... mnvr10.wav
        │   └── fr/                 # Optional: translated audio (falls back to English if absent)
        │       ├── soundlist.csv   # Generated from fr.json (translated entries only)
        │       └── rst.wav, mnvr01.wav, ...
        ├── sport/ ...
        └── ...

bin/
├── generate-season.py              # JSON (+ locale overlays) → sequences.lua + soundlist.csv files
├── generate-season.cmd             # Windows wrapper
├── generate-i18n-overlay.py        # Scaffolds/updates per-locale TTS overlay files
├── generate-sounds.py              # soundlist.csv → WAV files via Google TTS (per-locale voices)
└── generate-sounds.cmd             # Windows wrapper (runs --only-missing)
```

## Development

Deploy directly to a connected radio via the VS Code tasks (requires the radio connected via USB HID or serial).

```
Ctrl+Shift+P → Tasks: Run Task → Deploy
```
