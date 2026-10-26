#!/usr/bin/env python3
"""Screenshot exported files to check them visually (headless Chromium via Playwright).

    python3 preview.py out.drawio out_drawio.png   # official draw.io viewer (fetched once from jgraph/drawio)
    python3 preview.py out.html   out_html.png     # markmap HTML; CDN requests served from `npm pack` if the CDN is blocked
"""
import json, mimetypes, os, re, subprocess, sys, tarfile, tempfile, urllib.request

CACHE = os.path.join(tempfile.gettempdir(), "mindmap-preview-cache")
VIEWER = "https://raw.githubusercontent.com/jgraph/drawio/dev/src/main/webapp/js/viewer-static.min.js"
os.makedirs(CACHE, exist_ok=True)


def _npm_file(url):
    m = re.match(r"https://(?:cdn\.jsdelivr\.net/npm|unpkg\.com)/((?:@[^/]+/)?[^@/]+)(?:@([^/]+))?(/.*)?$", url)
    name, ver, path = m.group(1), m.group(2) or "latest", m.group(3) or ""
    d = os.path.join(CACHE, name.replace("/", "_") + "@" + ver)
    if not os.path.exists(os.path.join(d, "package")):
        os.makedirs(d, exist_ok=True)
        out = subprocess.run(["npm", "pack", f"{name}@{ver}", "-q"], cwd=d, capture_output=True, text=True,
                             check=True).stdout.strip().splitlines()[-1]
        with tarfile.open(os.path.join(d, out)) as t:
            t.extractall(d)
    root = os.path.join(d, "package")
    if path in ("", "/"):
        pj = json.load(open(os.path.join(root, "package.json")))
        path = "/" + (pj.get("jsdelivr") or pj.get("unpkg") or pj.get("main") or "index.js")
    f = os.path.join(root, path.lstrip("/"))
    return open(f, "rb").read(), mimetypes.guess_type(f)[0] or "application/javascript"


def main(src, png):
    from playwright.sync_api import sync_playwright
    src = os.path.abspath(src)
    page_file = src
    if src.endswith(".drawio"):
        vjs = os.path.join(CACHE, "viewer-static.min.js")
        if not os.path.exists(vjs):
            urllib.request.urlretrieve(VIEWER, vjs)
        cfg = json.dumps({"highlight": "#0000ff", "nav": False, "resize": True, "toolbar": "", "edit": None,
                          "xml": open(src, encoding="utf-8").read()})
        page_file = os.path.join(CACHE, "view.html")
        open(page_file, "w").write(
            '<!doctype html><html><body style="margin:0;background:white"><div class="mxgraph" data-mxgraph=\''
            + cfg.replace("'", "&#39;") + "'></div><script>" + open(vjs).read() + "</script></body></html>")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 2400 if src.endswith(".drawio") else 1800, "height": 1200})

        def cdn(route):
            try:
                body, ct = _npm_file(route.request.url)
                route.fulfill(body=body, content_type=ct)
            except Exception as e:
                print("unresolved", route.request.url, e)
                route.abort()
        if os.environ.get("MINDMAP_PREVIEW_ONLINE") != "1":
            pg.route(re.compile(r"https://(cdn\.jsdelivr\.net|unpkg\.com)/.*"), cdn)
        pg.goto("file://" + page_file)
        pg.wait_for_timeout(6000)
        pg.screenshot(path=png, full_page=True)
        b.close()
    print(png)


if __name__ == "__main__":
    main(*sys.argv[1:3])
