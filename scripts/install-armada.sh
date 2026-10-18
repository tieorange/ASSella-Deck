#!/usr/bin/env bash
set -euo pipefail

echo "The upstream ARM64 installer is disabled in ASSella Deck because it installs into upstream ASSella paths." >&2
echo "Use install.sh for the x86_64 Steam Deck AppImage when a verified fork release is available." >&2
exit 2
