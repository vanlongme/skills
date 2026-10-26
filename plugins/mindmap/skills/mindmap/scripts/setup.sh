#!/usr/bin/env bash
# One-time setup: Python deps + Inter font (for text measurement and rendering).
set -e
pip install -q cairosvg pillow diagrams 2>/dev/null || pip install -q --break-system-packages cairosvg pillow diagrams
if ! fc-list 2>/dev/null | grep -qi "Inter"; then
  echo "Inter font not found: install it (apt install fonts-inter / brew install --cask font-inter) for exact text widths."
fi
# Brand logos ({logo:name}) are shared with the arch-diagram skill when it is installed next to this one;
# otherwise drop PNGs into ./logos or set ARCHDIAG_LOGOS=/path/to/logos.
echo "mindmap ready"
