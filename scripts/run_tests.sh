#!/usr/bin/env bash
set -euo pipefail

# The upstream pre-release suite still references ACCELA's data directory.
# Running it from a side-by-side fork could inspect or modify the other app.
echo "The upstream pre-release suite is disabled until its paths are isolated." >&2
echo "Run scripts/test_deck_library.py, scripts/test_side_by_side_install.py," >&2
echo "and scripts/test_fork_runtime_identity.py with the required dependencies." >&2
exit 2
