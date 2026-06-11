# IMAC Ethos Caller

An FrSky Ethos widget that calls IMAC aerobatic competition sequences via audio on the radio. Select a year and class, then use a switch to announce each maneuver in order as you fly.

## Features

- Supports all 8 IMAC classes: Basic, Sportsman, Intermediate, Intermediate ALT, Advanced, Advanced ALT, Unlimited, Unlimited ALT
- Per-year sequence files — adding a new season never touches existing data
- Shared audio catalog — repeated maneuvers (common across classes/years) reuse a single recording instead of duplicating it
- Progress bar shows current maneuver position through the sequence
- Three configurable switches: Trigger (next maneuver), Repeat (replay current), Reset (restart sequence)
- Sequence data for 2026 included with real figure names from official IMAC PDFs

## Radio Requirements

- FrSky Ethos firmware (tested on X20S)
- Sound files must be 16 kHz mono A-law WAV format

## Installation

1. Download the latest release ZIP from the [Releases](../../releases) page
2. Extract to the root of your radio's SD card — the widget lands at `/scripts/imac-caller/`
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

Spoken call-outs are available in English, French, German, and Dutch. Any
maneuver without translated audio falls back to the English recording — see
[Adding Translated Audio](#adding-translated-audio) for how to add more.

Audio is organized into per-locale voice-pack folders matching the official
Ethos audio packs (the same layout used by rfsuite's sound generator):
English ships `gb` (British, the default) and `us` voices, and French ships
`femme` (female, the default) and `homme` (male) voices. The widget picks
whichever variant matches the radio's currently selected audio voice
(`system.getAudioVoice()`), falling back to that locale's default variant if
the radio's voice isn't one of the available options. German and Dutch ship a
single `default` voice each, since Ethos doesn't offer multiple official voice
packs for those locales.

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

This scans the `soundlist.csv` files under `src/imac-caller/sounds/<locale>/<variant>/` (one per locale/variant — see [Voice Variants](#voice-variants)) and generates any missing WAV files. To regenerate everything: delete the WAV files first, then run again.

The voice used is chosen automatically per CSV based on its locale/variant (`LOCALE_VOICES` in `bin/generate-sounds.py`). Pass `--voice <name>` to override the voice for all CSVs in the run.

## Adding a New Year

The repo-root `seasons/` and `i18n/` folders are the editing surface — nothing in them is deployed to the radio. Everything under `src/imac-caller/` is generated.

1. Create `seasons/<year>/sequence.json` listing each class's `key`, `name`, `reset`, and ordered `figures` — each `reset`/figure value is a maneuver ID from [seasons/catalog.json](seasons/catalog.json).
2. For any maneuver not already in the catalog, add it first:
   ```cmd
   python bin\catalog-add.py "Loop" "Loop. Outside entry, three-quarter opposite roll and quarter roll at the top."
   python bin\catalog-add.py --reset basic "Basic sequence reset."
   ```
   Each command prints the maneuver ID to reference from `sequence.json`. New entries are added to `seasons/catalog.json` with English text only — `fr`/`de`/`nl` start as English placeholders flagged `"needs_translation": true` (see [Adding Translated Audio](#adding-translated-audio)).
3. Run `bin\generate.cmd` — writes `sequences.lua` for that year and rebuilds the shared sound catalog (`src/imac-caller/sounds/<locale>/<variant>/soundlist.csv`) from `seasons/catalog.json`.
4. Run `bin\generate-sounds.cmd` to produce any new WAV files.

The widget auto-discovers year folders at runtime — no code changes needed. Maneuvers reused from another class or year (same catalog ID) are not regenerated — no new audio or catalog entry is created for them.

Never edit `sequences.lua`, `soundlist.csv`, or `src/imac-caller/i18n/*.lua` directly — they are generated from the JSON and will be overwritten.

## Adding Translated Audio

Spoken call-out translations live directly in
[seasons/catalog.json](seasons/catalog.json), one entry per maneuver, with a
`fr`/`de`/`nl` block each. New maneuvers (added via `bin\catalog-add.py`)
start with their `fr`/`de`/`nl` text set to the English placeholder and
`"needs_translation": true`.

To translate:

1. Find the maneuver's entry in `seasons/catalog.json` (search for its ID or English `en` text)
2. Edit the `text` field under `fr`/`de`/`nl`
3. Set `"needs_translation": false`
4. Run `bin\generate.cmd` — this adds an entry to
   `src/imac-caller/sounds/<lang>/<variant>/soundlist.csv` (one CSV per
   voice variant — see below), but only for entries with
   `needs_translation: false`
5. Run `bin\generate-sounds.cmd` to generate the translated WAV files

Entries still flagged `needs_translation: true` are skipped — no catalog entry
and no audio is generated for them, so the widget keeps falling back to the
English audio for those maneuvers.

### Sound Catalog

Audio is not stored per year/class. [seasons/catalog.json](seasons/catalog.json)
is the master catalog of every maneuver and reset announcement, keyed by a
"phrase ID" — a slug of its label plus a short hash of its English TTS text,
e.g. `loop-6c260463` (see `bin/catalog-add.py`). `seasons/<year>/sequence.json`
references maneuvers by phrase ID.

Each entry also has a short `audio` id (6 hex characters, e.g. `ceaecb`,
derived from the phrase ID) — `sequences.lua` uses this for `file`/`reset`
(`file = "ceaecb"`, `reset = "2f7cd5"`), and the actual audio lives in a
shared pool at `src/imac-caller/sounds/<locale>/<variant>/<audio id>.wav`.
The on-radio audio path (`SCRIPTS:/imac-caller/sounds/<locale>/<variant>/<audio id>.wav`)
must stay short, so the longer, descriptive phrase ID is only used for
editing/reference in the JSON, never for filenames.

Because a maneuver's ID is derived from its label + English text, the same
maneuver referenced from multiple classes or years collapses to the same
phrase ID (and `audio` id) and is only generated/stored once. The catalog
(`soundlist.csv` per locale/variant) is rebuilt from `seasons/catalog.json` every time
`bin/generate.py` runs, so it stays complete and deduped as years are added.

### Voice Variants

Each locale's catalog is split into one `soundlist.csv` per voice variant the
radio supports (`LOCALE_VARIANTS` in `bin/generate.py`), matching the
layout of rfsuite's sound-generator soundpacks:

| Locale | Variants | Default |
|---|---|---|
| English | `gb`, `us` | `gb` |
| French | `femme`, `homme` | `femme` |
| German | `default` | `default` |
| Dutch | `default` | `default` |

English variants are generated from each catalog entry's `en` text; French,
German, and Dutch variants are generated from the entry's `fr`/`de`/`nl` text
(only when `needs_translation` is `false`). Each variant is written to its own
`src/imac-caller/sounds/<locale>/<variant>/soundlist.csv`, with voices
configured in `LOCALE_VOICES` in `bin/generate-sounds.py`:

| Variant | Voice |
|---|---|
| `en/gb` | `en-GB-Neural2-A` |
| `en/us` | `en-US-Wavenet-F` |
| `fr/femme` | `fr-FR-Neural2-F` |
| `fr/homme` | `fr-FR-Standard-B` |
| `de/default` | `de-DE-Neural2-C` |
| `nl/default` | `nl-NL-Wavenet-A` |

At runtime, the widget picks the variant matching the radio's currently
selected audio voice (`system.getAudioVoice()`), falling back to the locale's
default variant.

## Project Structure

JSON under the repo root is the editing surface; everything under
`src/imac-caller/` is generated by `bin/generate.py` and never hand-edited
(except `widget_impl.lua`, `main.lua`, and `i18n/i18n.lua`, which are widget code).

```
i18n/                                # Editing surface — not deployed
└── strings.json                    # UI chrome strings, all locales (year, routine, switch labels, ...)

seasons/                            # Editing surface — not deployed
├── catalog.json                    # Maneuver catalog: id -> label + en/fr/de/nl text + needs_translation
└── 2026/
    └── sequence.json               # Class/figure structure for this year — references catalog IDs

src/imac-caller/                   # Deployed to radio (generated, except widget code below)
├── main.lua                        # Widget entry point
├── widget_impl.lua                 # Widget logic
├── i18n/
│   ├── i18n.lua                    # Runtime locale loader/translate helper (hand-written)
│   ├── en.lua                      # Generated from i18n/strings.json
│   ├── fr.lua
│   ├── de.lua
│   └── nl.lua
├── seasons/
│   └── 2026/
│       └── sequences.lua           # Generated from seasons/2026/sequence.json + seasons/catalog.json
└── sounds/                          # Shared audio catalog (deduped across classes/years)
    ├── en/
    │   ├── gb/                      # Default — British English voice
    │   │   ├── soundlist.csv
    │   │   └── ceaecb.wav, 2f7cd5.wav, ... (named by each entry's short "audio" id)
    │   └── us/                      # American English voice
    │       ├── soundlist.csv
    │       └── ...
    ├── fr/
    │   ├── femme/                   # Default — translated audio (falls back to English if absent)
    │   │   ├── soundlist.csv
    │   │   └── ...
    │   └── homme/
    │       ├── soundlist.csv
    │       └── ...
    ├── de/
    │   └── default/
    │       ├── soundlist.csv
    │       └── ...
    └── nl/
        └── default/
            ├── soundlist.csv
            └── ...

bin/
├── generate.py                     # JSON sources → i18n/*.lua + sequences.lua + sound catalog (soundlist.csv per locale/variant)
├── generate.cmd                    # Windows wrapper
├── catalog-add.py                  # Adds a new maneuver to seasons/catalog.json, prints its catalog ID
├── generate-sounds.py              # soundlist.csv → WAV files via Google TTS (per-locale/variant voices)
└── generate-sounds.cmd             # Windows wrapper (runs --only-missing)
```

## Development

Deploy directly to a connected radio via the VS Code tasks (requires the radio connected via USB HID or serial).

```
Ctrl+Shift+P → Tasks: Run Task → Deploy
```
