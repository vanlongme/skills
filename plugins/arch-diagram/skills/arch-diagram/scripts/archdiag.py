"""archdiag — absolute-layout architecture diagrams (Lucidchart/AWS style) -> SVG + PNG.

Usage:
    from archdiag import Canvas
    c = Canvas(2590, 1250)
    acct = c.box(308, 148, 2457, 980, "solid", label="AFT Management Account", tab="aws")
    src  = c.box(415, 530, 592, 787, "grey", label="Source", label_pos="top-center")
    cc   = c.icon("aws/devtools/codecommit", 461, 598, label="AWS\\nCodeCommit")
    c.arrow(cc.right(), src2.left(y=cc.cy))          # attach to edges, not centers
    c.save("out")                                    # out.svg + out.png

Box kinds : outer | dashed | solid | grey | dotted | none
Tabs      : "aws" (navy AWS account tab) | "code" (blue group badge, top-right) | None
Icons     : any PNG under diagrams/resources (e.g. "aws/compute/ec2", "k8s/compute/pod",
            "onprem/client/users"), plus built-ins "@terraform".
Arrows    : c.arrow(p1, p2, ...) orthogonal polyline, rounded corners, head at the last point.
            c.elbow(a, b, via_x=..)  / c.elbow(a, b, via_y=..) build 3-segment routes.
Logos     : logo("karpenter") -> path of a PNG fetched by scripts/fetch_logos.py (ARCHDIAG_LOGOS dir).
Helpers   : c.tier() public/private subnet band · c.card() rounded box · c.marker() numbered step
            c.pill() VPC-endpoint row · c.chip() ownership badge · c.placeholder() "no official logo"
            c.mono() monospace text · c.tab_label() label sitting on a dashed border
"""
import base64
import os
from dataclasses import dataclass

import cairosvg
import diagrams

RES = os.path.join(os.path.dirname(diagrams.__file__), "..", "resources")
HERE = os.path.dirname(os.path.abspath(__file__))


def logo(name):
    """Absolute path of a brand logo PNG (run scripts/fetch_logos.py once to populate).
    Search order: $ARCHDIAG_LOGOS, ./logos, <skill>/logos."""
    for d in (os.environ.get("ARCHDIAG_LOGOS"), os.path.join(os.getcwd(), "logos"),
              os.path.join(HERE, "..", "logos")):
        if d and os.path.exists(os.path.join(d, name + ".png")):
            return os.path.abspath(os.path.join(d, name + ".png"))
    raise FileNotFoundError(f"logo '{name}' missing — run: python3 scripts/fetch_logos.py")

THEME = dict(
    font="Inter, DejaVu Sans, sans-serif",
    ink="#232F3E",       # account borders, labels, strong arrows
    line="#545B64",      # normal arrows
    dash="#5A6B86",      # dashed/dotted group borders
    grey="#EEF0F2",      # filled groups
    accent="#3B8FD9",    # optional / async path
    badge="#4D5ED6",     # group badge
)


@dataclass
class Rect:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def cx(self): return (self.x1 + self.x2) / 2
    @property
    def cy(self): return (self.y1 + self.y2) / 2

    # connection ports — offset by `gap` px outside the edge so heads don't overlap strokes
    def left(self, y=None, gap=2):   return (self.x1 - gap, self.cy if y is None else y)
    def right(self, y=None, gap=2):  return (self.x2 + gap, self.cy if y is None else y)
    def top(self, x=None, gap=2):    return (self.cx if x is None else x, self.y1 - gap)
    def bottom(self, x=None, gap=2): return (self.cx if x is None else x, self.y2 + gap)


class Canvas:
    def __init__(self, w, h, theme=None, bg="white"):
        self.w, self.h = w, h
        self.t = {**THEME, **(theme or {})}
        self.under, self.over = [], []   # arrows drawn last (over boxes)
        self.under.append(f'<rect width="{w}" height="{h}" fill="{bg}"/>')

    # ------------------------------------------------------------ text
    def text(self, x, y, s, size=23, anchor="middle", weight=400, color=None, lh=None):
        lines = s.split("\n")
        lh = lh or size * 1.22
        for i, ln in enumerate(lines):
            ln = ln.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            self.under.append(
                f'<text x="{x}" y="{y + i * lh:.1f}" font-family="{self.t["font"]}" font-size="{size}" '
                f'font-weight="{weight}" fill="{color or self.t["ink"]}" text-anchor="{anchor}">{ln}</text>')

    # ------------------------------------------------------------ containers
    def box(self, x1, y1, x2, y2, kind="solid", label=None, label_pos=None, tab=None, size=21):
        t, w, h = self.t, x2 - x1, y2 - y1
        style = {
            "outer":  f'fill="none" stroke="{t["dash"]}" stroke-width="3" stroke-dasharray="14 10"',
            "dashed": f'fill="none" stroke="{t["dash"]}" stroke-width="3" stroke-dasharray="14 10"',
            "solid":  f'fill="white" stroke="{t["ink"]}" stroke-width="3"',
            "grey":   f'fill="{t["grey"]}" stroke="none" rx="6"',
            "dotted": f'fill="none" stroke="{t["dash"]}" stroke-width="2.5" stroke-dasharray="3 5"',
            "none":   'fill="none" stroke="none"',
        }[kind]
        self.under.append(f'<rect x="{x1}" y="{y1}" width="{w}" height="{h}" {style}/>')
        if tab == "aws":
            self.aws_tab(x1, y1)
        elif tab == "code":
            self.badge(x2 - 64, y1 + 10)
        if label:
            pos = label_pos or ("tab" if tab == "aws" else "top-center")
            if pos == "tab":
                self.text(x1 + 76, y1 + 37 - (11 if "\n" in label else 0), label, size - 1, "start", lh=23)
            elif pos == "top-left":
                self.text(x1 + 14, y1 + 32, label, size, "start")
            else:
                self.text((x1 + x2) / 2, y1 + 38, label, size, lh=25)
        return Rect(x1, y1, x2, y2)

    def aws_tab(self, x, y, s=60):
        a = self.under.append
        a(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{self.t["ink"]}"/>')
        a(f'<text x="{x + s / 2}" y="{y + s * .52}" font-family="{self.t["font"]}" font-size="{s * .42}" '
          f'font-weight="600" fill="white" text-anchor="middle">aws</text>')
        a(f'<path d="M{x + s * .2},{y + s * .66} Q{x + s * .5},{y + s * .82} {x + s * .8},{y + s * .64}" '
          f'fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round"/>')
        a(f'<path d="M{x + s * .72},{y + s * .6} L{x + s * .81},{y + s * .63} L{x + s * .78},{y + s * .72}" '
          f'fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round"/>')

    def badge(self, x, y, s=45):
        a = self.under.append
        a(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{self.t["badge"]}"/>')
        a(f'<rect x="{x + 9}" y="{y + 10}" width="{s - 18}" height="{s - 20}" rx="2" fill="none" stroke="white" stroke-width="2"/>')
        a(f'<line x1="{x + 9}" y1="{y + 17}" x2="{x + s - 9}" y2="{y + 17}" stroke="white" stroke-width="2"/>')
        a(f'<text x="{x + s / 2}" y="{y + 32}" font-family="DejaVu Sans Mono" font-size="11" fill="white" text-anchor="middle">&lt;/&gt;</text>')

    # ------------------------------------------------------------ icons
    def icon(self, name, x, y, s=85, label=None, size=23):
        """Place icon with top-left at (x,y). Returns its Rect (ports for arrows)."""
        if name == "@terraform":
            self._terraform(x, y, s)
        else:
            path = os.path.join(RES, name + ("" if name.endswith(".png") else ".png"))
            if not os.path.exists(path):
                raise FileNotFoundError(f"icon '{name}' not found — run: python3 archdiag.py find <keyword>")
            b64 = base64.b64encode(open(path, "rb").read()).decode()
            self.under.append(f'<image x="{x}" y="{y}" width="{s}" height="{s}" href="data:image/png;base64,{b64}"/>')
        if label:
            self.text(x + s / 2, y + s + 33, label, size, lh=size * 1.26)
        return Rect(x, y, x + s, y + s)

    def _terraform(self, x, y, s):
        k = s / 64
        for col, pts in (
            ("#7B42BC", [(6.6, 4.2), (20.8, 12.4), (20.8, 28.7), (6.6, 20.5)]),
            ("#7B42BC", [(22.4, 13.3), (36.6, 21.5), (36.6, 37.8), (22.4, 29.6)]),
            ("#7B42BC", [(22.4, 31.5), (36.6, 39.7), (36.6, 56.0), (22.4, 47.8)]),
            ("#4040B2", [(38.2, 21.5), (52.4, 13.3), (52.4, 29.6), (38.2, 37.8)]),
        ):
            p = " ".join(f"{x + px * k:.1f},{y + py * k:.1f}" for px, py in pts)
            self.under.append(f'<polygon points="{p}" fill="{col}"/>')

    # ------------------------------------------------------------ arrows
    def arrow(self, *pts, color="line", dashed=False, width=2.5, radius=10, head=True):
        """Orthogonal polyline through pts; rounded corners; arrowhead at the last point."""
        col = self.t.get(color, color)
        d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for i in range(1, len(pts) - 1):
            (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
            def toward(ax, ay, bx, by, r):
                n = max(abs(bx - ax), abs(by - ay)) or 1
                r = min(r, n / 2)
                return ax + (bx - ax) / n * r, ay + (by - ay) / n * r
            a, b = toward(x1, y1, x0, y0, radius), toward(x1, y1, x2, y2, radius)
            d += f" L{a[0]:.1f},{a[1]:.1f} Q{x1},{y1} {b[0]:.1f},{b[1]:.1f}"
        d += f" L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"
        da = ' stroke-dasharray="10 8"' if dashed else ""
        self.over.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{width}"{da}/>')
        if head:  # explicit triangle (renders identically in every SVG viewer)
            (xa, ya), (xb, yb) = pts[-2], pts[-1]
            n = max(abs(xb - xa), abs(yb - ya)) or 1
            ux, uy = (xb - xa) / n, (yb - ya) / n
            L, Wd = 16, 7
            bx, by = xb - ux * L, yb - uy * L
            self.over.append(
                f'<polygon points="{xb:.1f},{yb:.1f} {bx - uy * Wd:.1f},{by + ux * Wd:.1f} '
                f'{bx + uy * Wd:.1f},{by - ux * Wd:.1f}" fill="{col}"/>')

    def elbow(self, a, b, via_x=None, via_y=None, **kw):
        """3-segment orthogonal route: H-V-H through via_x, or V-H-V through via_y."""
        if via_x is not None:
            return self.arrow(a, (via_x, a[1]), (via_x, b[1]), b, **kw)
        if via_y is not None:
            return self.arrow(a, (a[0], via_y), (b[0], via_y), b, **kw)
        return self.arrow(a, b, **kw)

    # ------------------------------------------------------------ higher-level helpers
    def card(self, x1, y1, x2, y2, stroke="#D0D5DD", fill="#F7F8FA", rx=10, dash=None, sw=2.5):
        """Rounded box with custom stroke/fill (e.g. a namespace, a tool group, a highlighted lane)."""
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.under.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="{rx}" fill="{fill}" '
                          f'stroke="{stroke}" stroke-width="{sw}"{da}/>')
        return Rect(x1, y1, x2, y2)

    def tier(self, x1, y1, x2, y2, public, label, lx=None):
        """AWS subnet tier band: public = green, private = blue; small colour square + label."""
        fill, line = ("#EEF6EA", "#7AA116") if public else ("#EAF2FB", "#147EBA")
        self.under.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="4" fill="{fill}" '
                          f'stroke="{line}" stroke-width="2"/>')
        lx = lx or x1 + 14
        self.under.append(f'<rect x="{lx}" y="{y1 + 12}" width="16" height="16" rx="2" fill="{line}"/>')
        self.text(lx + 26, y1 + 27, label, 19, "start", weight=600, color=line)
        return Rect(x1, y1, x2, y2)

    def marker(self, x, y, n, color="#E07B00"):
        """Numbered step marker — put it ON an arrow segment, never floating."""
        self.over.append(f'<circle cx="{x}" cy="{y}" r="16" fill="{color}" stroke="white" stroke-width="3"/>')
        self.over.append(f'<text x="{x}" y="{y + 6.5}" font-family="{self.t["font"]}" font-size="18" '
                         f'font-weight="700" fill="white" text-anchor="middle">{n}</text>')

    def mono(self, x, y, s, size=16, anchor="middle", color="#3A4450", weight=400):
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.under.append(f'<text x="{x}" y="{y}" font-family="JetBrains Mono, DejaVu Sans Mono, monospace" '
                          f'font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{s}</text>')

    def tab_label(self, x, y, txt, w, size=18, color="#3A4450"):
        """Label on top of a dashed border: white knock-out rect behind the text."""
        self.under.append(f'<rect x="{x - 8}" y="{y - 19}" width="{w}" height="26" fill="white"/>')
        self.text(x, y, txt, size, "start", weight=600, color=color)

    def pill(self, x1, x2, y, name, kind="Interface"):
        """VPC endpoint row (Interface = purple, Gateway = green). Returns centre y for straight arrows."""
        col = "#7AA116" if kind == "Gateway" else "#8C4FFF"
        self.under.append(f'<rect x="{x1}" y="{y}" width="{x2 - x1}" height="34" rx="17" fill="white" '
                          f'stroke="{col}" stroke-width="2"/>')
        self.icon("aws/network/endpoint", x1 + 6, y + 4, 26)
        self.mono(x1 + 42, y + 23, name, 18, "start", self.t["ink"])
        self.text(x2 - 14, y + 23, kind, 15, "end", color="#5A6B86")
        return y + 17

    def chip(self, cx, y, txt, color, w=None):
        """Small filled badge, e.g. who installs a namespace (Terraform / Argo CD)."""
        w = w or 20 + len(txt) * 9
        self.under.append(f'<rect x="{cx - w / 2}" y="{y}" width="{w}" height="26" rx="13" fill="{color}"/>')
        self.text(cx, y + 19, txt, 15, weight=700, color="white")

    def placeholder(self, cx, y, s, txt, label, size=20):
        """Dashed tile for a product with no obtainable official logo. Never fake a brand mark."""
        x = cx - s / 2
        self.under.append(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * .18}" fill="white" '
                          f'stroke="#8A94A6" stroke-width="2.5" stroke-dasharray="6 5"/>')
        self.text(cx, y + s / 2 + 7, txt, 20, weight=700, color="#5A6B86")
        self.text(cx, y + s + 33, label, size, lh=size * 1.26)

    def icon_c(self, name, cx, cy, label=None, s=72, size=17):
        """icon() positioned by centre instead of top-left."""
        return self.icon(name, cx - s / 2, cy - s / 2, s, label=label, size=size)

    # ------------------------------------------------------------ output
    def svg(self):
        body = "\n".join(self.under + self.over)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">\n{body}\n</svg>')

    def save(self, stem):
        s = self.svg()
        open(stem + ".svg", "w").write(s)
        cairosvg.svg2png(bytestring=s.encode(), write_to=stem + ".png", output_width=self.w)
        return stem + ".png"


# ---------------------------------------------------------------- CLI helpers
def grid(src, out, step=100, width=2590):
    """Resize reference to `width` (= your Canvas width) and overlay a labelled grid,
    so the numbers you read off it are directly usable as Canvas coordinates."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(src).convert("RGB")
    if width and im.width != width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    dr = ImageDraw.Draw(im, "RGBA")
    try:
        f = ImageFont.truetype("DejaVuSans.ttf", 18)
    except OSError:
        f = ImageFont.load_default()
    for x in range(0, im.width, step):
        dr.line([(x, 0), (x, im.height)], fill=(255, 0, 0, 90 if x % (step * 5) else 170), width=1)
        dr.text((x + 3, 3), str(x), fill=(220, 0, 0), font=f)
    for y in range(0, im.height, step):
        dr.line([(0, y), (im.width, y)], fill=(0, 0, 255, 90 if y % (step * 5) else 170), width=1)
        dr.text((3, y + 3), str(y), fill=(0, 0, 220), font=f)
    im.save(out)
    print(f"{out}  ({im.width}x{im.height})")


def compare(a, b, out):
    """Stack reference (top) and render (bottom) at the same width for visual diff."""
    from PIL import Image
    A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    B = B.resize((A.width, int(B.height * A.width / B.width)))
    C = Image.new("RGB", (A.width, A.height + B.height + 20), "white")
    C.paste(A, (0, 0)); C.paste(B, (0, A.height + 20))
    C.save(out)
    print(out)


def crop(src, out, x1, y1, x2, y2):
    """Cut a region of a render at full resolution — use it to inspect dense areas."""
    from PIL import Image
    Image.open(src).crop((int(x1), int(y1), int(x2), int(y2))).save(out)
    print(out)


def find(keyword):
    kw = keyword.lower()
    for root, _, files in os.walk(RES):
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), RES)[:-4]
            if kw in rel.lower():
                print(rel)


if __name__ == "__main__":
    import signal, sys
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    cmd, *args = sys.argv[1:] or ["help"]
    if cmd == "grid":
        grid(args[0], args[1] if len(args) > 1 else "grid.png",
             int(args[2]) if len(args) > 2 else 100, int(args[3]) if len(args) > 3 else 2590)
    elif cmd == "compare":
        compare(args[0], args[1], args[2] if len(args) > 2 else "compare.png")
    elif cmd == "find":
        find(args[0])
    elif cmd == "crop":
        crop(args[0], args[1], *map(float, args[2:6]))
    else:
        print("usage: archdiag.py grid <img> [out] [step] [canvas_width] | compare <ref> <render> [out] | find <keyword> | crop <img> <out> x1 y1 x2 y2")
