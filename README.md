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

This scans all `soundlist.csv` files under `src/imac-ethos-caller/sounds/` and generates any missing WAV files. To regenerate everything: delete the WAV files first, then run again.

Each class has a `soundlist.csv` with rows in the form `filename,text`. Edit these files to change what is spoken, then regenerate.

## Adding a New Year

1. Create `src/imac-ethos-caller/seasons/<year>/` with a `sequences.lua` and one subfolder per class, following the structure of [seasons/2026/](src/imac-ethos-caller/seasons/2026/)
2. Add a `soundlist.csv` to each class subfolder
3. Add `loadYear("<year>")` to the `YEARS` table in [main.lua](src/imac-ethos-caller/main.lua)
4. Run `bin\generate-sounds.cmd` to produce the WAV files

## Project Structure

```
src/imac-ethos-caller/
├── main.lua                        # Widget entry point
└── seasons/
    └── 2026/
        ├── sequences.lua           # Sequence data for all 8 classes
        ├── basic/
        │   ├── soundlist.csv       # Text-to-speech source list
        │   ├── rst.wav             # Reset announcement
        │   └── mnvr01.wav ... mnvr10.wav
        ├── sport/ ...
        ├── inter/ ...
        └── ...

bin/
├── generate-sounds.py              # Sound generation script
└── generate-sounds.cmd             # Windows wrapper (runs --only-missing)
```

## Development

Deploy directly to a connected radio via the VS Code tasks (requires the radio connected via USB HID or serial).

```
Ctrl+Shift+P → Tasks: Run Task → Deploy
```
