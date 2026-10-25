#!/usr/bin/env python3
"""Install JetBrains Mono (TTF) into ~/.fonts — needed for Vietnamese diacritics in monospace text
(DejaVu Sans Mono lacks ế, ố, ủ ...). Inter (sans) usually ships with the system; install it the same way if not."""
import io
import os
import subprocess
import tarfile
import urllib.request

from fontTools.ttLib import TTFont

URL = "https://registry.npmjs.org/jetbrains-mono/-/jetbrains-mono-1.0.6.tgz"
dst = os.path.expanduser("~/.fonts")
os.makedirs(dst, exist_ok=True)
blob = urllib.request.urlopen(URL, timeout=60).read()
with tarfile.open(fileobj=io.BytesIO(blob)) as t:
    for w in ("Regular", "Medium", "SemiBold", "Bold"):
        m = t.getmember(f"package/fonts/webfonts/JetBrainsMono-{w}.woff2")
        f = TTFont(io.BytesIO(t.extractfile(m).read()))
        f.flavor = None
        f.save(os.path.join(dst, f"JetBrainsMono-{w}.ttf"))
subprocess.run(["fc-cache", "-f"], check=False)
print("JetBrains Mono installed ->", dst)
