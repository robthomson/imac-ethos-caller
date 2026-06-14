#!/usr/bin/env python3
"""
Generate Ethos-compatible WAV files for imac-caller from soundlist CSVs.

Scans src/imac-caller/sounds/ for all soundlist.csv files (one per
locale/variant, written by generate.py), then calls Google Cloud
Text-to-Speech to produce 16 kHz mono A-law WAV files.

Requires:
    pip install google-cloud-texttospeech sox
    GOOGLE_APPLICATION_CREDENTIALS env var pointing to a Google Cloud service-account JSON.

Usage:
    python generate-sounds.py
    python generate-sounds.py --only-missing
    python generate-sounds.py --voice en-US-Wavenet-F --speed 0.9
    python generate-sounds.py --csv sounds/en/gb/soundlist.csv
"""

import argparse
import csv
import glob
import os
import shutil
import sys
import tempfile

try:
    import sox
except ImportError:
    print("ERROR: sox not installed.  Run: pip install sox")
    sys.exit(1)

try:
    from google.cloud import texttospeech
except ImportError:
    print("ERROR: google-cloud-texttospeech not installed.  Run: pip install google-cloud-texttospeech")
    sys.exit(1)

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "src", "imac-caller", "sounds"))

# Voice used per locale/variant when --voice is not given. Derived from the
# soundlist.csv's path, e.g. sounds/en/gb/soundlist.csv -> "en/gb",
# sounds/de/default/soundlist.csv -> "de/default". Variant names
# and voice choices match the official Ethos audio packs as used by rfsuite's
# bin/sound-generator (see generate-all.bat).
# NOTE: double-check these voice names against the current Google Cloud TTS voice
# list before first use of a new locale.
LOCALE_VOICES = {
    "en/gb":     "en-GB-Neural2-A",
    "en/us":     "en-US-Wavenet-F",
    "fr/femme":  "fr-FR-Neural2-F",
    "fr/homme":  "fr-FR-Standard-B",
    "de/default": "de-DE-Neural2-C",
    "nl/default": "nl-NL-Wavenet-A",
    "cz/default": "cs-CZ-Wavenet-A",
}
DEFAULT_VOICE = LOCALE_VOICES["en/gb"]


def voice_for_csv(csv_path):
    """Pick a voice name based on the locale/variant subfolder a soundlist.csv lives in."""
    parent = os.path.basename(os.path.dirname(csv_path))
    grandparent = os.path.basename(os.path.dirname(os.path.dirname(csv_path)))
    combo = f"{grandparent}/{parent}"
    return LOCALE_VOICES.get(combo, DEFAULT_VOICE)


def load_csv(csv_path):
    """Return list of (filename, text) from a soundlist CSV."""
    entries = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get("filename", "").strip().replace("\\", "/").lstrip("/")
            text     = row.get("text", "").strip()
            if filename and text:
                entries.append((filename, text))
    return entries


def find_csvs(sounds_root):
    """Return all soundlist.csv paths under sounds_root."""
    pattern = os.path.join(sounds_root, "**", "soundlist.csv")
    return sorted(glob.glob(pattern, recursive=True))


def to_alaw_wav(tts_bytes, dest_path, speed):
    """Write TTS PCM bytes to dest_path as 16 kHz mono A-law WAV, trimming trailing silence."""
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "tts.wav")
        with open(raw, "wb") as f:
            f.write(tts_bytes)

        tfm = sox.Transformer()
        tfm.set_output_format(channels=1, rate=16000, encoding="a-law")
        extra = ["tempo", str(speed), "reverse", "silence", "1", "0.1", "0.1%", "reverse"]
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        tfm.build(raw, dest_path, extra_args=extra)


def generate(sounds_root, voice_override, speed, only_missing, csv_filter=None):
    client = texttospeech.TextToSpeechClient()
    audio_cfg = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        speaking_rate=speed,
    )

    csvs = [csv_filter] if csv_filter else find_csvs(sounds_root)
    if not csvs:
        print(f"No soundlist.csv files found under {sounds_root}")
        return 1

    generated = skipped = 0

    for csv_path in csvs:
        voice_name = voice_override or voice_for_csv(csv_path)
        voice = texttospeech.VoiceSelectionParams(
            language_code="-".join(voice_name.split("-")[:2]),
            name=voice_name,
        )
        print(f"\n--- {os.path.relpath(csv_path, sounds_root)}  (voice: {voice_name}) ---")
        for filename, text in load_csv(csv_path):
            dest = os.path.join(sounds_root, filename)
            if only_missing and os.path.exists(dest):
                print(f"  skip  {filename}")
                skipped += 1
                continue
            print(f"  gen   {filename}  ->  {repr(text)}")
            response = client.synthesize_speech(
                input=texttospeech.SynthesisInput(text=text),
                voice=voice,
                audio_config=audio_cfg,
            )
            to_alaw_wav(response.audio_content, dest, speed)
            generated += 1

    print(f"\nDone — generated {generated}, skipped {skipped}.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Generate IMAC Ethos Caller sound files via Google TTS")
    parser.add_argument("--sounds-dir",   default=DEFAULT_ROOT,
                        help=f"Root sounds directory (default: {DEFAULT_ROOT})")
    parser.add_argument("--voice",        default=None,
                        help="Google TTS voice name. If omitted, the voice is chosen "
                             f"per CSV from LOCALE_VOICES based on its locale subfolder "
                             f"(default for 'en'/class-level CSVs: {DEFAULT_VOICE})")
    parser.add_argument("--speed",        type=float, default=1.0,
                        help="Speaking rate multiplier (default: 1.0)")
    parser.add_argument("--only-missing", action="store_true",
                        help="Skip files that already exist on disk")
    parser.add_argument("--csv",          default=None,
                        help="Generate from a single specific soundlist.csv instead of scanning")
    args = parser.parse_args()

    sounds_root = os.path.abspath(args.sounds_dir)
    if not os.path.isdir(sounds_root):
        print(f"ERROR: sounds dir not found: {sounds_root}")
        return 1

    return generate(sounds_root, args.voice, args.speed, args.only_missing, args.csv)


if __name__ == "__main__":
    sys.exit(main())
