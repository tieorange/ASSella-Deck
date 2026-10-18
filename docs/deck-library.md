# Installed-games library: agent notes

## Current flow

`GameManager.scan_steam_libraries_async()` starts one `TaskRunner`. The worker
discovers Steam libraries, indexes ACF manifests once, scans game directories,
and updates the disk-backed games cache. Success and error callbacks clear the
scan state on the UI thread. The library dialog retains its current rows while
refreshing and offers a retry after failure.

`get_unavailable_steam_libraries()` reports configured paths without a mounted
`steamapps` directory. Games previously cached on those paths remain visible
with `library_unavailable=True`; a later successful scan can replace them.
Other available libraries still refresh, so removed games on mounted drives
disappear from the cache.

The library view inserts at most 30 game rows per event-loop turn. Artwork is
queued for visible rows and a small scroll margin, with a bounded fetch queue.
Update-status checks are separate from scan completion. Scan duration is logged
per library and for the full scan.

## Cases to protect

- No Steam installation or worker failure: leave cached rows visible, clear
  scanning state, and show a retryable error. Skip individual unreadable
  manifests without blocking the rest of the scan.
- Card removed before or during a scan: keep its cached rows and name the
  unavailable path; do not treat temporary absence as game deletion.
- Card reinserted: rescan its contents, add new games, and remove games no
  longer present there.
- Repeated Scan Libraries clicks: keep one active worker and avoid duplicate
  scans or callbacks.
- Large libraries: keep the event loop responsive while rows and artwork load.
  A new refresh must invalidate work scheduled for the previous list.

`scripts/test_deck_library.py` covers the core scan-state, path, batching, and
artwork cases with filesystem fixtures and headless Qt list tests. Real Deck
testing remains necessary for internal drive and microSD timing, focus
behavior, and install/upgrade/rollback.
