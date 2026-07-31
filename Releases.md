# 1.0.5

- Internal fix: the lazy-loading helper's proxy no longer stays a permanent indirection layer after the widget implementation loads -- it now resolves to the real functions on first use, removing an ongoing per-tick overhead on wakeup()/paint(). No user-facing behavior change.

# 1.0.4

- Extend system to support more languages.

# 1.0.3

- Refactor system to work with muliple languages.   Currently supported are
   - english
   - german
   - dutch
   - french

 Audio files have been created in each language for each class. (Basic, Sportsman, Intermediate, Intermediate ALT, Advanced, Advanced ALT, Unlimited, Unlimited ALT)


# 1.0.2

- Improve some audio files

# 1.0.1

- Improved memory usage
- Misc cleanups

# 1.0.0

- Initial release: IMAC Ethos Caller widget
- Supports all 8 IMAC 2026 competition classes (Basic, Sportsman, Intermediate, Intermediate ALT, Advanced, Advanced ALT, Unlimited, Unlimited ALT)
- Configurable trigger, repeat, and reset switches
- Progress bar showing sequence completion

***
