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

This scans all `soundlist.csv` files under `src/imac-ethos-caller/seasons/` and generates any missing WAV files. To regenerate everything: delete the WAV files first, then run again.

## Adding a New Year

The `seasons/` folder at the repo root is the editing surface — nothing in it is deployed to the radio.

1. Create `seasons/<year>.json` following the structure of [seasons/2026.json](seasons/2026.json)
2. Run `bin\generate-season.cmd` — this writes `sequences.lua` and all `soundlist.csv` files into `src/`
3. Run `bin\generate-sounds.cmd` to produce the WAV files

The widget auto-discovers year folders at runtime — no code changes needed.

Never edit `sequences.lua` or `soundlist.csv` directly — they are generated from the JSON and will be overwritten.

## Project Structure

```
seasons/                            # Editing surface — not deployed
└── 2026.json                       # Single source of truth for labels, TTS, and structure

src/imac-ethos-caller/             # Deployed to radio
├── main.lua                        # Widget entry point
└── seasons/
    └── 2026/
        ├── sequences.lua           # Generated from JSON
        ├── basic/
        │   ├── soundlist.csv       # Generated from JSON
        │   ├── rst.wav
        │   └── mnvr01.wav ... mnvr10.wav
        ├── sport/ ...
        └── ...

bin/
├── generate-season.py              # JSON → sequences.lua + soundlist.csv files
├── generate-season.cmd             # Windows wrapper
├── generate-sounds.py              # soundlist.csv → WAV files via Google TTS
└── generate-sounds.cmd             # Windows wrapper (runs --only-missing)
```

## Development

Deploy directly to a connected radio via the VS Code tasks (requires the radio connected via USB HID or serial).

```
Ctrl+Shift+P → Tasks: Run Task → Deploy
```
