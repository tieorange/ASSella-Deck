# ASSella Deck

Steam Deck focused fork of [ASSella](https://github.com/niwia/ASSella). The
improvements below are on this fork's `deck/beta` branch, which tracks upstream
`beta` through Git merges.

## Improvements in this fork

- **Recoverable library scans:** Missing Steam libraries, worker errors, and
  cancellation end the scanning state and leave the Scan Libraries button ready
  to retry. A second scan cannot start while one is running.
- **microSD recovery:** Games cached from an unavailable library remain visible.
  The library shows the missing path and rescans when the card is reconnected.
  Successful scans remove games that are no longer present on available drives.
- **Responsive large libraries:** Game rows render in batches, and artwork is
  requested for visible rows first. Scan time is logged per library and overall
  to support measurements on a Deck.
- **Fork-controlled updates:** The installer, in-app updater, and AppImage update
  metadata point to this fork. The installer fails clearly if this fork has no
  release instead of installing an upstream build.
- **Side-by-side installation:** The fork reserves its own AppImage, desktop
  entry, icon, settings, and data paths. Its installer, updater, and uninstaller
  leave ACCELA and upstream ASSella files alone. See the
  [Deck install guide](docs/install.md).
- **Upstream merge path:** The repository retains ASSella's Git history and has
  an [upstream merge guide](docs/deck-fork.md). Nine focused local tests cover
  scan recovery and large-library rendering.

Steam Deck hardware timing, AppImage install and rollback, and binary
redistribution checks are still pending. No modified AppImage has been released.

Original ASSella installation guide: https://yeet.md/s/g6jhSh-M

Contributing with an AI coding agent? Start with [AGENTS.md](AGENTS.md) and the
[agent guide](docs/agent-guide.md).
