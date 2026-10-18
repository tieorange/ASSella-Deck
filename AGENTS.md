# ASSella Deck agent instructions

This is `tieorange/ASSella-Deck`, a Steam Deck fork of `niwia/ASSella`. Work on
`deck/beta`; `upstream/beta` is the source for future merges. Read
[`docs/agent-guide.md`](docs/agent-guide.md) before changing code, and read
[`docs/deck-library.md`](docs/deck-library.md) for library work.

## Priorities

- Keep the installed-games library responsive and recoverable on Steam Deck,
  including internal storage and removable microSD libraries.
- Preserve cached games when a configured library is temporarily unavailable.
  Replace stale entries only after that library can be scanned successfully.
- Run filesystem scans and other slow work off the Qt UI thread. Send UI updates
  through Qt signals or the existing main-thread bridge.
- Put new feature code behind clear presentation, domain, and data boundaries
  where practical. Improve the existing Python/PyQt structure incrementally;
  avoid a broad architecture rewrite during a bug fix.

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
