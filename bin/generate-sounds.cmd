@echo off
:: Generate IMAC Ethos Caller sound files via Google Cloud TTS.
:: Only missing files are generated — safe to re-run at any time.
::
:: Usage:
::   generate-sounds.cmd                     generate all missing files
::   generate-sounds.cmd --voice en-US-Wavenet-F
::   generate-sounds.cmd --csv ..\src\imac-ethos-caller\sounds\2026\basic\soundlist.csv
::   generate-sounds.cmd --speed 0.9
::
python "%~dp0generate-sounds.py" --only-missing %*
