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
  psutil available, plus relevant existing tests.
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
