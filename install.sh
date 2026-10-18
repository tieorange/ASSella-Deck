#!/usr/bin/env bash
set -euo pipefail

# This installer owns only ASSella Deck files. ACCELA, upstream ASSella,
# Steam, and SLSsteam are never installed, migrated, or removed here.
REPOSITORY="tieorange/ASSella-Deck"
BRANCH="deck/beta"
APPIMAGE_NAME="ASSella-Deck.AppImage"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
INSTALL_DIR="$DATA_HOME/ASSella-Deck"
APPIMAGE_PATH="$INSTALL_DIR/$APPIMAGE_NAME"
BACKUP_PATH="$INSTALL_DIR/$APPIMAGE_NAME.previous"
VERSION_PATH="$INSTALL_DIR/version"
DESKTOP_DIR="$DATA_HOME/applications"
DESKTOP_PATH="$DESKTOP_DIR/assella-deck.desktop"
ICON_DIR="$DATA_HOME/icons/hicolor/256x256/apps"
ICON_PATH="$ICON_DIR/assella-deck.png"
ACTION="install"
TEMP_DIR=""

cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf -- "$TEMP_DIR"
    fi
}
trap cleanup EXIT

usage() {
    cat <<'HELP'
ASSella Deck installer (beta releases)
  --install, --update   Install or update this fork
  --rollback            Restore the previous fork AppImage
  --uninstall           Remove only this fork's launcher and AppImages
  --help                Show this help

App data is kept on uninstall. ACCELA and upstream ASSella are untouched.
HELP
}

for option in "$@"; do
    case "$option" in
        --install|--update|--beta|-i|-u|--yes|-y) ;;
        --rollback) ACTION="rollback" ;;
        --uninstall) ACTION="uninstall" ;;
        --help|-h) ACTION="help" ;;
        *) printf 'Unknown option: %s\n' "$option" >&2; usage >&2; exit 2 ;;
    esac
done

sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | cut -d ' ' -f 1
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | cut -d ' ' -f 1
    else
        echo "SHA-256 tool required (sha256sum or shasum)." >&2
        return 1
    fi
}

check_owned_paths() {
    command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required." >&2; return 1; }
    python3 - "$INSTALL_DIR" "$APPIMAGE_PATH" "$BACKUP_PATH" \
        "$VERSION_PATH" "$INSTALL_DIR/version.previous" \
        "$DESKTOP_PATH" "$ICON_PATH" "$DATA_HOME" "$HOME" <<'PY'
import os
import sys

install_dir, *owned, data_home, home = sys.argv[1:]
protected = [
    os.path.realpath(os.path.join(root, name))
    for root in (data_home, os.path.join(home, ".local", "share"))
    for name in ("ACCELA", "ACCELA-Original", "ASSella")
]
if os.path.basename(os.path.realpath(data_home)) in ("ACCELA", "ACCELA-Original", "ASSella"):
    protected.append(os.path.realpath(data_home))
for path in (install_dir, *owned):
    if os.path.islink(path):
        sys.exit(f"Refusing symlinked ASSella Deck path: {path}")
    resolved = os.path.realpath(path)
    if any(os.path.commonpath((resolved, legacy)) == legacy for legacy in protected):
        sys.exit(f"Refusing ASSella Deck path inside another app: {path}")
PY
}

write_desktop_entry() {
    mkdir -p "$DESKTOP_DIR"
    local staged="$TEMP_DIR/assella-deck.desktop"
    {
        echo "[Desktop Entry]"
        echo "Type=Application"
        echo "Name=ASSella Deck"
        echo "Comment=Steam Deck game library and depot manager"
        printf 'Exec="%s" %%U\n' "$APPIMAGE_PATH"
        echo "Icon=assella-deck"
        echo "Terminal=false"
        echo "Categories=Utility;Game;"
        echo "StartupWMClass=ASSella Deck"
    } > "$staged"
    mv -f -- "$staged" "$DESKTOP_PATH"
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
    fi
}

write_icon() {
    mkdir -p "$ICON_DIR"
    local staged="$TEMP_DIR/assella-deck.png"
    local local_icon
    local_icon="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/src/res/logo/icon.png"
    if [ -f "$local_icon" ]; then
        cp -- "$local_icon" "$staged"
    else
        curl -fsSL --max-time 20 \
            "https://raw.githubusercontent.com/$REPOSITORY/$BRANCH/src/res/logo/icon.png" \
            -o "$staged" || return 0
    fi
    mv -f -- "$staged" "$ICON_PATH"
}

release_fields() {
    curl -fsSL --max-time 20 \
        -H "Accept: application/vnd.github+json" \
        -H "User-Agent: ASSella-Deck-Installer" \
        "https://api.github.com/repos/$REPOSITORY/releases" |
        python3 -c '
import json
import sys

name = "ASSella-Deck.AppImage"
base = "https://github.com/tieorange/ASSella-Deck/releases/download/"
for release in json.load(sys.stdin):
    tag = str(release.get("tag_name", ""))
    if not any(mark in tag.lower() for mark in ("beta", "dev", "rc")):
        continue
    assets = {asset.get("name"): asset.get("browser_download_url", "")
              for asset in release.get("assets", [])}
    image = assets.get(name, "")
    checksum = assets.get(name + ".sha256", "")
    if image.startswith(base) and checksum.startswith(base):
        print(tag + "\t" + image + "\t" + checksum)
        break
'
}

install_fork() {
    command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required." >&2; return 1; }
    command -v curl >/dev/null 2>&1 || { echo "curl is required." >&2; return 1; }
    check_owned_paths
    mkdir -p "$INSTALL_DIR"
    TEMP_DIR="$(mktemp -d "$INSTALL_DIR/.install.XXXXXXXX")"

    local fields tag image_url checksum_url expected actual checksum_name
    fields="$(release_fields)"
    if [ -z "$fields" ]; then
        echo "No verified beta AppImage release exists in $REPOSITORY. Existing apps were not changed." >&2
        return 1
    fi
    IFS=$'\t' read -r tag image_url checksum_url <<< "$fields"
    curl -fsSL --max-time 1800 "$image_url" -o "$TEMP_DIR/$APPIMAGE_NAME"
    curl -fsSL --max-time 30 "$checksum_url" -o "$TEMP_DIR/$APPIMAGE_NAME.sha256"
    expected="$(awk 'NR == 1 {print $1}' "$TEMP_DIR/$APPIMAGE_NAME.sha256" | tr 'A-F' 'a-f')"
    checksum_name="$(awk 'NR == 1 {print $2}' "$TEMP_DIR/$APPIMAGE_NAME.sha256")"
    if ! [[ "$expected" =~ ^[a-f0-9]{64}$ ]] || [ "$checksum_name" != "$APPIMAGE_NAME" ]; then
        echo "Invalid release SHA-256 file; installation stopped." >&2
        return 1
    fi
    actual="$(sha256_of "$TEMP_DIR/$APPIMAGE_NAME")"
    if [ "$actual" != "$expected" ]; then
        echo "AppImage SHA-256 mismatch; installation stopped." >&2
        return 1
    fi
    chmod 755 "$TEMP_DIR/$APPIMAGE_NAME"

    # Only the previous fork build is backed up. Never inspect or change
    # ACCELA.AppImage, ASSella.AppImage, or their compatibility symlinks.
    if [ -f "$APPIMAGE_PATH" ]; then
        cp -p -- "$APPIMAGE_PATH" "$TEMP_DIR/$APPIMAGE_NAME.previous"
        mv -f -- "$TEMP_DIR/$APPIMAGE_NAME.previous" "$BACKUP_PATH"
        if [ -f "$VERSION_PATH" ]; then
            cp -p -- "$VERSION_PATH" "$TEMP_DIR/version.previous"
            mv -f -- "$TEMP_DIR/version.previous" "$INSTALL_DIR/version.previous"
        fi
    fi
    mv -f -- "$TEMP_DIR/$APPIMAGE_NAME" "$APPIMAGE_PATH"
    printf '%s\n' "$tag" > "$TEMP_DIR/version"
    mv -f -- "$TEMP_DIR/version" "$VERSION_PATH"
    write_desktop_entry
    write_icon
    printf 'Installed ASSella Deck %s at %s\n' "$tag" "$APPIMAGE_PATH"
}

rollback_fork() {
    check_owned_paths
    if [ ! -f "$BACKUP_PATH" ]; then
        echo "No previous ASSella Deck AppImage is available." >&2
        return 1
    fi
    TEMP_DIR="$(mktemp -d "$INSTALL_DIR/.rollback.XXXXXXXX")"
    if [ -f "$APPIMAGE_PATH" ]; then
        mv -- "$APPIMAGE_PATH" "$TEMP_DIR/current.AppImage"
    fi
    mv -- "$BACKUP_PATH" "$APPIMAGE_PATH"
    if [ -f "$INSTALL_DIR/version.previous" ]; then
        mv -- "$INSTALL_DIR/version.previous" "$VERSION_PATH"
    fi
    printf 'Restored previous ASSella Deck AppImage at %s\n' "$APPIMAGE_PATH"
}

uninstall_fork() {
    check_owned_paths
    rm -f -- "$APPIMAGE_PATH" "$BACKUP_PATH" "$VERSION_PATH" \
        "$INSTALL_DIR/version.previous" "$DESKTOP_PATH" "$ICON_PATH"
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
    fi
    echo "Removed ASSella Deck launcher and AppImages. Fork data was retained."
}

case "$ACTION" in
    help) usage ;;
    install) install_fork ;;
    rollback) rollback_fork ;;
    uninstall) uninstall_fork ;;
esac
