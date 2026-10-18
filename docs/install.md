# Install ASSella Deck alongside ACCELA and ASSella

The fork uses a separate install directory, application data, settings, desktop
entry, icon, and AppImage name. The installer never backs up, replaces, symlinks,
or uninstalls ACCELA or upstream ASSella. It does not install or reset Headcrab.

| Application | Default AppImage | Desktop entry |
| --- | --- | --- |
| ACCELA | `~/.local/share/ACCELA/ACCELA.AppImage` | `accela.desktop` |
| Upstream ASSella | `~/.local/share/ACCELA/ASSella.AppImage` | `assella.desktop` |
| This fork | `~/.local/share/ASSella-Deck/ASSella-Deck.AppImage` | `assella-deck.desktop` |

The fork also uses its own `ASSella-Deck` data directory and Qt settings name.
If `XDG_DATA_HOME` is set, its install and data paths use that root instead of
`~/.local/share`. The fork does not claim the `accela://` URL handler or change
existing desktop entries.

## Install and maintain

From the `deck/beta` checkout on Steam Deck, after a verified beta AppImage has
been published to this fork's GitHub releases:

```bash
./install.sh --install
./install.sh --update
./install.sh --rollback
./install.sh --uninstall
```

Installation requires a release containing both `ASSella-Deck.AppImage` and
`ASSella-Deck.AppImage.sha256`. It refuses missing or mismatched checksums and
leaves existing installs untouched if no qualifying release exists. The previous
fork AppImage is retained for `--rollback`. Uninstall removes only this fork's
AppImages and launcher; it keeps fork data for a later reinstall.

**No modified AppImage is published yet.** Source changes alone cannot make the
Deck installer succeed. A candidate binary needs a real Deck test and a
redistribution-rights review before publishing, as described in
[deck-fork.md](deck-fork.md).

## Shared Steam integration

All three applications can discover the same Steam libraries and may operate
on the same games or SLSsteam configuration. The fork skips automatic SLSsteam
repairs and migrations at startup by default. Explicit game-management and
Settings actions can still change shared Steam/SLSsteam files. Avoid running
updates or installs for the same game simultaneously in multiple applications.
