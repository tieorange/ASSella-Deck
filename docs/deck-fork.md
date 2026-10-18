# ASSella Deck fork

This fork tracks `niwia/ASSella` **beta**. Its `deck/beta` branch contains the
Steam Deck changes and is the branch used for candidate builds. The upstream
project remains available through the `upstream` Git remote; `origin` points to
`tieorange/ASSella-Deck`.

## Bring in upstream changes

```bash
git fetch upstream beta
git switch deck/beta
git switch -c integrate/upstream-YYYYMMDD
git merge --no-ff upstream/beta
```

Resolve conflicts on the integration branch. Run the normal CI checks and test
the library on a Deck before merging into `deck/beta` through a pull request.
Keep the merge commit so the common ancestry is available next time. Do not
force-push `deck/beta`.

The fork release source is defined in `src/utils/release_source.py` and mirrored
in `install.sh` and `.github/workflows/build-appimage.yml`. After every upstream
merge, verify that all three still point to `tieorange/ASSella-Deck`; upstream
release URLs would silently replace this build during an update. The installer
intentionally fails when this fork has no release instead of falling back to
upstream binaries.

## Deck acceptance checklist

- Record cold and warm library scan durations in Desktop Mode, with games on
  internal storage and an inserted microSD card.
- Remove the card during a scan. The library must exit scanning, retain cached
  entries for that card, explain the missing path, and allow a retry.
- With the card mounted, add and remove a game, rescan, and verify the cache.
- Test a large library for UI responsiveness, focus, and artwork loading.
- Test candidate AppImage install, upgrade, and rollback before publishing.

There is no verified Steam Deck performance baseline yet. The upstream source
repository has no root license file; confirm redistribution rights for the app
and bundled dependencies before publishing a modified AppImage.
