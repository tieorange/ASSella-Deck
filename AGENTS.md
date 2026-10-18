# ASSella Deck agent instructions

This is `tieorange/ASSella-Deck`, a Steam Deck fork of `niwia/ASSella`. Work on
`deck/beta`; `upstream/beta` is the source for future merges. Read
[`docs/agent-guide.md`](docs/agent-guide.md) before changing code, and read
[`docs/deck-library.md`](docs/deck-library.md) for library work.

The maintainer has nine years of Flutter experience and prefers clean
architecture with three layers divided by feature. Apply that preference to
this Python/PyQt codebase without introducing Flutter or moving unrelated
upstream code. Read `/Users/anduser/.codex/RTK.md` in this workspace: prefix
shell commands with `rtk`; use `rtk proxy <command>` when a raw command needs
to run without RTK filtering.

## Priorities

- Keep the installed-games library responsive and recoverable on Steam Deck,
  including internal storage and removable microSD libraries.
- Preserve cached games when a configured library is temporarily unavailable.
  Replace stale entries only after that library can be scanned successfully.
- Run filesystem scans and other slow work off the Qt UI thread. Send UI updates
  through Qt signals or the existing main-thread bridge.
- Divide new feature code into presentation (Qt widgets and input), domain
  (state, decisions, validation), and data (managers and external services).
  Keep dependencies directed toward domain logic and pass collaborators into
  widgets where feasible. Improve existing PyQt code incrementally so upstream
  merges remain manageable; avoid broad rewrites during a bug fix.

## Code map and data flow

| Area | Where to start | Responsibility |
| --- | --- | --- |
| App startup | `src/main.py`, `src/ui/main_window.py` | Qt application, main window, navigation entry points |
| Deck screens | `src/ui/deck_ui/` | Home, guided install, Activity, shared theme, focus, controller routing |
| Library and details | `src/ui/dialogs/gamelibrary.py`, `src/ui/dialogs/library/`, `src/ui/dialogs/gamelibrary_v2.py` | Library window, rows, filters, scans, Game Details |
| Background work | `src/managers/` | Game discovery, task queue, downloads, updates, app updates |
| Steam and install logic | `src/core/` | Steam paths, manifests, depots, game operations |
| Shared adapters | `src/utils/` | Settings, paths, caches, artwork, logging, fork identity |
| Assets | `src/res/` | Theme resources, icons, version, bundled app resources |
| Checks and mock | `scripts/` | Focused tests, safe in-memory UI mock, local tooling |
| Delivery | `install.sh`, `uninstall.sh`, `docs/` | Fork-only installer, maintenance, developer guides |

Trace a UI action from its widget in `src/ui/` to a manager or domain helper,
then to `src/core/` or `src/utils/` for filesystem, Steam, and network access.
Qt widgets own presentation and input; keep validation and state decisions in a
feature's domain code and external access in its data/manager code. Use signals
or the main-thread bridge to return background results to Qt. For the guided
flow, begin in `src/ui/deck_ui/install/`; for Activity, begin in
`src/ui/deck_ui/activity/`. Older upstream features are not fully layered, so
make local changes without moving unrelated files.

The editable fork icon is `src/res/logo/icon.svg`. Run
`python scripts/render_deck_icon.py` with the app's PyQt6 environment after
changing it to regenerate
`icon.png` and `icon.ico`; keep the desktop installer, AppImage packaging, and
Qt window icon on those fork assets. Do not repurpose upstream `accela.png`.

## UI redesign contract

- Redesign all core game flows: Home, Library, discovery and install, Game
  Details, queue/activity, onboarding, and confirmations. Settings, Credits,
  and Easter eggs are out of scope unless the user explicitly asks otherwise.
- Keep Game Library as a separate window. Preserve existing manager APIs,
  dialog entry points, game operations, and task semantics while improving
  presentation and navigation.
- Build the discover-to-install journey as one guided sequence: find or import,
  choose build and depots, choose storage and backend, then review and queue.
  Existing direct actions must open at their relevant step.
- Support both Steam Deck Desktop Mode and Gaming Mode. At 1280x800 and
  1280x720, controls must remain readable and reachable; avoid fixed screen
  layouts that clip content. Keyboard, touch, mouse, trackpad, and controller
  navigation all remain supported.
- Use a visible focus ring, deterministic initial focus, focus restoration when
  a dialog closes, and Escape/B as Back. Do not use mouse-only cards or actions.
- Keep all slow discovery, artwork, metadata, and network work out of the UI
  thread. Retain visible data while refreshing and present errors with a retry.
- Keep shared UI primitives in `src/ui/deck_ui/`; feature screens compose them
  from `presentation`, `domain`, and `data` modules rather than adding another
  global stylesheet or duplicating style strings.
- The Mac mock must use the production widgets with injected in-memory data. It
  must not open Steam, contact services, modify user settings, install anything,
  or start a local server.
- The Deck install entry from Home and search opens `DeckInstallFlow`; it emits
  queue metadata only at the final Review action. Keep `FetchManifestDialog`
  and depot selection directly callable for existing library and manager paths.
- Library and Game Details currently retain some direct install dialogs. When
  changing those entry points, route into the appropriate guided step while
  preserving the underlying manager operations and explicit Review action.
- Native gamepad input uses `pygame-ce` controller mappings. Retain keyboard
  navigation when no controller is attached. Keep SDL polling on the Qt main
  thread and do not consume directional input from text fields or lists.

## Fork boundaries

- `origin` is this fork; `upstream` is `niwia/ASSella`. Merge upstream changes
  into an integration branch, then into `deck/beta`. Do not rebase or force-push
  the shared Deck branch. See [`docs/deck-fork.md`](docs/deck-fork.md).
- Keep installer, in-app updater, and AppImage update metadata pointed at
  `tieorange/ASSella-Deck`. Never fall back to an upstream binary when a fork
  release is missing. Check all three paths after every upstream merge.
- Keep this fork's AppImage, data, QSettings, desktop entry, icon, service name,
  and uninstaller separate from ACCELA and upstream ASSella. Never create
  compatibility aliases in their directories or claim `accela://`.
- GitHub Actions is disabled for this fork at the repository level. Use local
  checks; do not enable Actions or rely on its workflows for validation.
- Do not publish an AppImage until it has been tested on a Deck and the app and
  bundled dependencies' redistribution rights have been checked. The upstream
  source currently has no root license file.

## Checks

- For library changes, run `python scripts/test_deck_library.py` with PyQt6 and
  psutil available, plus `python scripts/test_deck_navigation.py` and relevant
  existing tests for UI changes.
- For redesigned screens, use `scripts/run_ui_mock.py` with the relevant
  `--state` fixture and inspect both `--deck` (1280x800) and `--deck-720`
  (1280x720). Check keyboard focus, Back, search, section switching, empty and
  error states. Mock checks do not establish real controller or Deck behavior.
- Run `python -m compileall -q src`, `python scripts/check_silent_exceptions.py`,
  and `bash -n install.sh` when those files are touched. Use
  `git -c core.whitespace=cr-at-eol diff --check` for CRLF source files.
- Do not run `scripts/prerelease_check.py` automatically. Run it only when the
  user explicitly asks, as required by upstream `.agents/AGENTS.md`.
- Record real Deck cold and warm scan timings before claiming a performance
  improvement on hardware. Headless Qt timings are diagnostic only.

Follow the applicable behavior invariants in upstream `.agents/AGENTS.md`,
especially path portability, SLSsteam configuration preservation, and library
action dialog independence. Its upstream release URLs, automated Actions
workflow, and branch names do not override this fork's rules.
