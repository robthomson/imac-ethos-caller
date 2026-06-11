@echo off
:: Generate all IMAC Ethos Caller sound files via Google Cloud TTS.
:: Only files that don't already exist on disk are generated.
::
:: Prerequisites:
::   pip install google-cloud-texttospeech sox
::   Set GOOGLE_APPLICATION_CREDENTIALS to your Google Cloud service-account JSON path.
::
:: Voice is chosen automatically per soundlist.csv based on its locale
:: (see LOCALE_VOICES in generate-sounds.py). Pass --voice to override
:: for all CSVs, e.g.:
::   en-GB-Neural2-A  (UK female - English default)
::   en-US-Wavenet-F  (US female)
::   en-US-Wavenet-D  (US male)

python "%~dp0generate-sounds.py" --only-missing %*
