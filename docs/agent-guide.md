# Agent guide

## Start here

This repository is a Python/PyQt application fork. `deck/beta` contains the
Steam Deck changes; `beta` mirrors upstream. Keep changes small so upstream
`beta` can be merged without repeatedly resolving broad refactors.

| Area | Entry points |
| --- | --- |
| Installed-games discovery and cache | `src/managers/game_manager.py`, `src/core/steam_helpers.py`, `src/utils/games_cache.py` |
| Library UI and artwork | `src/ui/dialogs/gamelibrary.py`, `src/ui/dialogs/library/` |
| Fork release routing | `src/utils/release_source.py`, `install.sh`, `.github/workflows/build-appimage.yml` |
| Side-by-side app identity | `src/utils/fork_identity.py`, `src/utils/helpers.py`, `src/utils/settings.py` |
| Focused Deck regressions | `scripts/test_deck_library.py` |

For library behavior and failure cases, read [deck-library.md](deck-library.md).
For upstream merges and Deck acceptance, read [deck-fork.md](deck-fork.md).

## Local validation

Use a Python environment with the project's dependencies. The focused Deck
tests need PyQt6 and psutil. On a headless Linux environment set
`QT_QPA_PLATFORM=offscreen`.

```bash
python scripts/test_deck_library.py
python scripts/test_side_by_side_install.py
python scripts/test_fork_runtime_identity.py
QT_QPA_PLATFORM=offscreen python scripts/test_deck_home_ui.py
python scripts/check_silent_exceptions.py
python -m compileall -q src
bash -n install.sh
git -c core.whitespace=cr-at-eol diff --check
```

Run other relevant `scripts/test_*.py` files for the code you change. GitHub
Actions is disabled on this fork. The upstream pre-release suite is not a
routine development check; run it only when the user explicitly requests it.

## Reporting a change

State which files or behavior changed, the local checks run, and whether it was
tested on a real Steam Deck. Treat cold/warm timings from another machine as
diagnostic, not a Deck result. Do not claim install, update, or rollback success
without testing the candidate AppImage on Deck hardware.
