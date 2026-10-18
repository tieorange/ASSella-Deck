# ASSella Deck UI redesign

## Scope

The redesign covers Home, Game Library, game discovery and installation, Game
Details, queue and activity, onboarding, and game-operation confirmations.
Settings, Credits, and Easter eggs retain their current UI.

## Navigation model

Home is the operational overview. Its primary actions are **Library** and
**Find a game**. It shows update work and the current task without forcing the
user to open a log view. Game Library remains a separate window and opens Game
Details for a selected game.

Home and top-bar discovery use one guided flow: Find, Build & depots, Storage &
backend, Review. Queueing occurs only on Review. Existing Library and Game
Details actions still open their specialized operation dialogs; those actions
retain their current semantics. Back returns to the preceding step and dialog
closure restores focus to the entry point.

## Input and layout

Target 1280x800 first and allow the layout to contract to 1280x720. Every
interactive control receives `Qt.StrongFocus`, has a clear focused state, and
works through keyboard, touch, mouse, trackpad, and controller routing:

| Control | Meaning |
| --- | --- |
| D-pad / left stick | Move focus or list selection |
| A | Activate the focused control |
| B / Escape | Back or close the current transient surface |
| X | Open contextual actions |
| Y | Move focus to search |
| L1 / R1 | Change the current section or tab |

## Architecture

`src/ui/deck_ui/` contains reusable visual primitives, focus helpers, and the
controller adapter. Each feature owns its screen state and maps domain data to
presentation models. Existing managers remain the source of truth for scans,
downloads, queues, and game operations.

## Mock and verification

`scripts/run_ui_mock.py` launches production UI widgets with deterministic
in-memory state. It never touches Steam or external services. Run with
`--deck` or `--deck-720` and optionally `--state loading|empty|error|missing-sd|large`.
Home, Activity, the guided install shell, Library shell, and Game Details
section rail are production widgets. Library rows and Game Details content are
fixtures because the production screens scan storage and load external data.
Physical controller, actual install, and real Deck Desktop/Gaming Mode checks
remain release gates.
