#!/usr/bin/env bash
# One-time setup for the arch-diagram skill. Run from anywhere.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pip install -q diagrams cairosvg pillow fonttools brotli 2>/dev/null \
  || pip install --break-system-packages -q diagrams cairosvg pillow fonttools brotli
python3 "$HERE/fetch_logos.py"
python3 "$HERE/install_fonts.py" || echo "font install skipped (Vietnamese monospace may render as boxes)"
