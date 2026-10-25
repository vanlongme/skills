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
Animation : c.arrow(..., flow="dash"|"dot") or Canvas(..., flow="dash") for every arrow — marching
            dashes / a dot travelling along the connector (SMIL in SVG, frames in GIF, flowAnimation in draw.io)
Export    : c.save(stem, "svg", "png", "gif", "drawio")  ·  c.save_gif() · c.save_drawio()
Helpers   : c.tier() public/private subnet band · c.card() rounded box · c.marker() numbered step
            c.pill() VPC-endpoint row · c.chip() ownership badge · c.placeholder() "no official logo"
            c.mono() monospace text · c.tab_label() label sitting on a dashed border
"""
import base64
import html
import io
import os
import re
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
    def __init__(self, w, h, theme=None, bg="white", flow=None, cycle=2.0):
        """flow: default animation for every arrow (None | "dash" | "dot");
        cycle: seconds of one animation loop — every flow repeats an integer number of times per cycle,
        so GIFs loop seamlessly."""
        self.w, self.h = w, h
        self.flow, self.cycle = flow, cycle
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

    def _group(self, x, y, w, h, parts, layer=None):
        (layer if layer is not None else self.under).append(
            f'<g data-ad-bbox="{x:.1f},{y:.1f},{w:.1f},{h:.1f}">' + "".join(parts) + '</g>')

    def aws_tab(self, x, y, s=60):
        parts = []
        a = parts.append
        a(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{self.t["ink"]}"/>')
        a(f'<text x="{x + s / 2}" y="{y + s * .52}" font-family="{self.t["font"]}" font-size="{s * .42}" '
          f'font-weight="600" fill="white" text-anchor="middle">aws</text>')
        a(f'<path d="M{x + s * .2},{y + s * .66} Q{x + s * .5},{y + s * .82} {x + s * .8},{y + s * .64}" '
          f'fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round"/>')
        a(f'<path d="M{x + s * .72},{y + s * .6} L{x + s * .81},{y + s * .63} L{x + s * .78},{y + s * .72}" '
          f'fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round"/>')
        self._group(x, y, s, s, parts)

    def badge(self, x, y, s=45):
        parts = []
        a = parts.append
        a(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{self.t["badge"]}"/>')
        a(f'<rect x="{x + 9}" y="{y + 10}" width="{s - 18}" height="{s - 20}" rx="2" fill="none" stroke="white" stroke-width="2"/>')
        a(f'<line x1="{x + 9}" y1="{y + 17}" x2="{x + s - 9}" y2="{y + 17}" stroke="white" stroke-width="2"/>')
        a(f'<text x="{x + s / 2}" y="{y + 32}" font-family="DejaVu Sans Mono" font-size="11" fill="white" text-anchor="middle">&lt;/&gt;</text>')
        self._group(x, y, s, s, parts)

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
        k, parts = s / 64, []
        for col, pts in (
            ("#7B42BC", [(6.6, 4.2), (20.8, 12.4), (20.8, 28.7), (6.6, 20.5)]),
            ("#7B42BC", [(22.4, 13.3), (36.6, 21.5), (36.6, 37.8), (22.4, 29.6)]),
            ("#7B42BC", [(22.4, 31.5), (36.6, 39.7), (36.6, 56.0), (22.4, 47.8)]),
            ("#4040B2", [(38.2, 21.5), (52.4, 13.3), (52.4, 29.6), (38.2, 37.8)]),
        ):
            p = " ".join(f"{x + px * k:.1f},{y + py * k:.1f}" for px, py in pts)
            parts.append(f'<polygon points="{p}" fill="{col}"/>')
        self._group(x, y, s, s, parts)

    # ------------------------------------------------------------ arrows
    def arrow(self, *pts, color="line", dashed=False, width=2.5, radius=10, head=True, flow=None):
        """Orthogonal polyline through pts; rounded corners; arrowhead at the last point.
        flow: None (use Canvas default) | False | "dash" (marching dashes) | "dot" (travelling dot)."""
        col = self.t.get(color, color)
        flow = self.flow if flow is None else flow
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
        meta = f'class="ad-edge" data-head="{int(bool(head))}" data-flow="{flow or ""}"'
        if flow == "dash":
            dash = "10 8" if dashed else "12 9"
            period = sum(float(v) for v in dash.split())
            reps = max(1, round(self.cycle / 0.9))           # ~0.9 s per dash period, integer per cycle

            def _dash(t, d=d, col=col, width=width, dash=dash, period=period, reps=reps, meta=meta):
                if t is None:
                    anim = (f'<animate attributeName="stroke-dashoffset" from="0" to="-{period}" '
                            f'dur="{self.cycle / reps:.3f}s" repeatCount="indefinite"/>')
                    return (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{width}" '
                            f'stroke-dasharray="{dash}" {meta}>{anim}</path>')
                off = -(t * reps % 1) * period
                return (f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{width}" '
                        f'stroke-dasharray="{dash}" stroke-dashoffset="{off:.2f}" {meta}/>')
            self.over.append(_dash)
        else:
            da = ' stroke-dasharray="10 8"' if dashed else ""
            self.over.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{width}"{da} {meta}/>')
        if flow == "dot":
            length = sum(abs(bx - ax) + abs(by - ay) for (ax, ay), (bx, by) in zip(pts, pts[1:])) or 1
            reps = max(1, round(self.cycle * 260 / length))  # ~260 px/s, integer laps per cycle
            r = max(8, width * 3)

            def _dot(t, d=d, col=col, pts=list(pts), length=length, reps=reps, r=r):
                if t is None:
                    return (f'<circle r="{r}" fill="{col}" stroke="white" stroke-width="2" data-ad="flowdot">'
                            f'<animateMotion dur="{self.cycle / reps:.3f}s" repeatCount="indefinite" path="{d}"/>'
                            f'</circle>')
                x, y = _point_at(pts, (t * reps % 1) * length)
                return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}" stroke="white" '
                        f'stroke-width="2" data-ad="flowdot"/>')
            self.over.append(_dot)
        if head:  # explicit triangle (renders identically in every SVG viewer)
            (xa, ya), (xb, yb) = pts[-2], pts[-1]
            n = max(abs(xb - xa), abs(yb - ya)) or 1
            ux, uy = (xb - xa) / n, (yb - ya) / n
            L, Wd = 16, 7
            bx, by = xb - ux * L, yb - uy * L
            self.over.append(
                f'<polygon points="{xb:.1f},{yb:.1f} {bx - uy * Wd:.1f},{by + ux * Wd:.1f} '
                f'{bx + uy * Wd:.1f},{by - ux * Wd:.1f}" fill="{col}" data-ad="head"/>')

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
        self._group(x - 18, y - 18, 36, 36, [
            f'<circle cx="{x}" cy="{y}" r="16" fill="{color}" stroke="white" stroke-width="3"/>',
            f'<text x="{x}" y="{y + 6.5}" font-family="{self.t["font"]}" font-size="18" '
            f'font-weight="700" fill="white" text-anchor="middle">{n}</text>'], layer=self.over)

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
    def svg(self, t=None):
        """t=None: animated SVG (SMIL). t in [0,1): static frame at that phase of the cycle."""
        body = "\n".join(p if isinstance(p, str) else p(t) for p in self.under + self.over)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}">\n{body}\n</svg>')

    @property
    def animated(self):
        return any(not isinstance(p, str) for p in self.over)

    def save(self, stem, *formats, **kw):
        """Write <stem>.<fmt> for each format: svg, png, gif, drawio (default: svg + png).
        kw are passed to save_gif (frames, fps, scale)."""
        formats = formats or ("svg", "png")
        out = []
        if "svg" in formats:
            open(stem + ".svg", "w").write(self.svg(None if self.animated else 0))
            out.append(stem + ".svg")
        if "png" in formats:
            cairosvg.svg2png(bytestring=self.svg(0).encode(), write_to=stem + ".png", output_width=self.w)
            out.append(stem + ".png")
        if "gif" in formats:
            out.append(self.save_gif(stem, **kw))
        if "drawio" in formats:
            out.append(self.save_drawio(stem))
        return out[0] if len(out) == 1 else out

    def save_gif(self, stem, frames=None, fps=15, scale=0.5):
        """Animated GIF of the flows: one seamless loop of `cycle` seconds, rendered at `scale`."""
        from PIL import Image
        frames = frames or max(8, round(self.cycle * fps))
        ims = []
        for k in range(frames):
            png = cairosvg.svg2png(bytestring=self.svg(k / frames).encode(), output_width=int(self.w * scale))
            ims.append(Image.open(io.BytesIO(png)).convert("RGB"))
        pal = ims[0].quantize(colors=255, method=Image.Quantize.MEDIANCUT)
        seq = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in ims]
        seq[0].save(stem + ".gif", save_all=True, append_images=seq[1:], loop=0,
                    duration=round(1000 * self.cycle / frames), optimize=False, disposal=1)
        return stem + ".gif"

    def save_drawio(self, stem, name="Page-1"):
        """Uncompressed draw.io / diagrams.net XML: boxes & text stay editable, connectors become real
        edges with waypoints (flowAnimation on animated ones), icons are embedded images."""
        open(stem + ".drawio", "w").write(svg_to_drawio(self.svg(0), name))
        return stem + ".drawio"


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


def _point_at(pts, dist):
    """Point at arc length `dist` along an orthogonal polyline."""
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = abs(bx - ax) + abs(by - ay)
        if dist <= seg and seg:
            f = dist / seg
            return ax + (bx - ax) * f, ay + (by - ay) * f
        dist -= seg
    return pts[-1]


SVGNS = "http://www.w3.org/2000/svg"


def svg_to_drawio(svg, name="Page-1"):
    """Convert an archdiag SVG into draw.io XML (mxfile, uncompressed)."""
    import xml.etree.ElementTree as ET
    ET.register_namespace("", SVGNS)
    ns = "{%s}" % SVGNS
    root = ET.fromstring(svg)
    W, H = float(root.get("width")), float(root.get("height"))
    grads = {}
    for g in root.iter(ns + "linearGradient"):
        stop = g.find(ns + "stop")
        grads[g.get("id")] = stop.get("stop-color") if stop is not None else "#ffffff"
    cells, bg, counter = [], None, [1]

    def nid():
        counter[0] += 1
        return f"c{counter[0]}"

    def col(v):
        if not v or v == "none":
            return "none"
        m = re.match(r"url\(#(.+)\)", v)
        return grads.get(m.group(1), "#ffffff") if m else v

    def num(v, d=0.0):
        try:
            return float(re.sub(r"[^0-9.\-]", "", v)) if v is not None else d
        except ValueError:
            return d

    def stroke_style(el):
        st = [f"strokeColor={col(el.get('stroke'))}", f"strokeWidth={num(el.get('stroke-width'), 1):g}"]
        da = el.get("stroke-dasharray")
        if da:
            w = max(num(el.get("stroke-width"), 1), 1)
            st += ["dashed=1", "dashPattern=" + " ".join(f"{float(v) / w:g}" for v in da.replace(",", " ").split())]
        if el.get("stroke-opacity"):
            st.append(f"strokeOpacity={round(float(el.get('stroke-opacity')) * 100)}")
        return st

    def vertex(x, y, w, h, style, value=""):
        cells.append(f'<mxCell id="{nid()}" value="{html.escape(value)}" style="{html.escape(style)}" '
                     f'vertex="1" parent="1"><mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
                     f'height="{h:.1f}" as="geometry"/></mxCell>')

    def edge(pts, style):
        way = "".join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in pts[1:-1])
        cells.append(
            f'<mxCell id="{nid()}" value="" style="{html.escape(style)}" edge="1" parent="1">'
            f'<mxGeometry relative="1" as="geometry">'
            f'<mxPoint x="{pts[0][0]:.1f}" y="{pts[0][1]:.1f}" as="sourcePoint"/>'
            f'<mxPoint x="{pts[-1][0]:.1f}" y="{pts[-1][1]:.1f}" as="targetPoint"/>'
            + (f'<Array as="points">{way}</Array>' if way else "") + '</mxGeometry></mxCell>')

    def as_image(el, x, y, w, h, tx, ty):
        frag = ET.tostring(el, encoding="unicode")
        sv = (f'<svg xmlns="{SVGNS}" width="{w:.1f}" height="{h:.1f}" viewBox="{x - tx:.1f} {y - ty:.1f} '
              f'{w:.1f} {h:.1f}">{frag}</svg>')
        b64 = base64.b64encode(sv.encode()).decode()
        vertex(x, y, w, h, f"shape=image;image=data:image/svg+xml,{b64};imageAspect=0;")

    def bbox_of_numbers(vals):
        xs, ys = vals[0::2], vals[1::2]
        return min(xs), min(ys), max(xs) - min(xs) or 1, max(ys) - min(ys) or 1

    def walk(el, tx, ty):
        nonlocal bg
        tag = el.tag.replace(ns, "")
        if tag in ("defs", "linearGradient", "stop", "animate", "animateMotion", "title"):
            return
        if tag in ("svg",):
            for ch in el:
                walk(ch, tx, ty)
            return
        if tag == "g":
            m = re.search(r"translate\(\s*([-\d.]+)[ ,]+([-\d.]+)", el.get("transform", ""))
            dx, dy = (float(m.group(1)), float(m.group(2))) if m else (0, 0)
            if el.get("data-ad-bbox"):
                x, y, w, h = map(float, el.get("data-ad-bbox").split(","))
                as_image(el, x + tx + dx, y + ty + dy, w, h, tx, ty)
                return
            for ch in el:
                walk(ch, tx + dx, ty + dy)
            return
        if tag == "rect":
            x, y = num(el.get("x")) + tx, num(el.get("y")) + ty
            w, h = num(el.get("width"), W), num(el.get("height"), H)
            if bg is None and x == 0 and y == 0 and w >= W and h >= H and not cells:
                bg = col(el.get("fill"))
                return
            st = ["whiteSpace=wrap", "html=1", f"fillColor={col(el.get('fill', '#000000'))}"] + stroke_style(el)
            if el.get("stroke") in (None, "none"):
                st[-len(stroke_style(el)):] = ["strokeColor=none"]
            if el.get("rx"):
                st += ["rounded=1", "absoluteArcSize=1", f"arcSize={2 * num(el.get('rx')):g}"]
            if el.get("fill-opacity"):
                st.append(f"fillOpacity={round(float(el.get('fill-opacity')) * 100)}")
            vertex(x, y, w, h, ";".join(st) + ";")
            return
        if tag == "text":
            val = "".join(el.itertext())
            if not val.strip():
                return
            size = num(el.get("font-size"), 16)
            fam = (el.get("font-family") or "Helvetica").split(",")[0].strip()
            mono_ = "Mono" in fam
            w = max(len(val) * size * (0.62 if mono_ else 0.55), size)
            anchor = el.get("text-anchor", "start")
            x = num(el.get("x")) + tx
            x0 = x if anchor == "start" else (x - w / 2 if anchor == "middle" else x - w)
            y0 = num(el.get("y")) + ty - size * 0.95
            st = ["text", "html=1", "whiteSpace=nowrap", "spacing=0", "verticalAlign=top", "strokeColor=none",
                  "fillColor=none", f"align={ {'start': 'left', 'middle': 'center', 'end': 'right'}[anchor] }",
                  f"fontSize={size:g}", f"fontColor={col(el.get('fill', '#000000'))}", f"fontFamily={fam}"]
            if num(el.get("font-weight"), 400) >= 600:
                st.append("fontStyle=1")
            if el.get("opacity"):
                st.append(f"textOpacity={round(float(el.get('opacity')) * 100)}")
            vertex(x0, y0, w, size * 1.3, ";".join(st) + ";", val)
            return
        if tag == "image":
            href = el.get("href") or el.get("{http://www.w3.org/1999/xlink}href") or ""
            href = href.replace(";base64,", ",")
            vertex(num(el.get("x")) + tx, num(el.get("y")) + ty, num(el.get("width")), num(el.get("height")),
                   f"shape=image;image={href};imageAspect=0;aspect=fixed;")
            return
        if tag == "path" and "ad-edge" in (el.get("class") or ""):
            toks = re.findall(r"([MLQ])([^MLQ]*)", el.get("d"))
            pts = []
            for cmd, args in toks:
                v = [float(a) for a in re.findall(r"-?\d+\.?\d*", args)]
                if cmd in "ML":
                    if cmd == "M" or len(pts) == 0:
                        pts.append((v[0] + tx, v[1] + ty))
                    last = (v[0] + tx, v[1] + ty)
                else:  # Q cx,cy x,y — the control point is the polyline corner
                    pts.append((v[0] + tx, v[1] + ty))
                    last = (v[2] + tx, v[3] + ty)
            pts.append(last)
            st = ["edgeStyle=none", "rounded=1", "html=1", "endFill=1", "endSize=10",
                  "endArrow=" + ("block" if el.get("data-head") == "1" else "none")] + stroke_style(el)
            if el.get("data-flow"):
                st.append("flowAnimation=1")
            edge(pts, ";".join(st) + ";")
            return
        if tag == "polygon" and el.get("data-ad") == "head":
            return
        if tag == "circle" and el.get("data-ad") == "flowdot":
            return
        if tag == "line":
            pts = [(num(el.get("x1")) + tx, num(el.get("y1")) + ty), (num(el.get("x2")) + tx, num(el.get("y2")) + ty)]
            edge(pts, ";".join(["edgeStyle=none", "html=1", "endArrow=none"] + stroke_style(el)) + ";")
            return
        if tag == "circle":
            cx, cy, r = num(el.get("cx")) + tx, num(el.get("cy")) + ty, num(el.get("r"))
            vertex(cx - r, cy - r, 2 * r, 2 * r,
                   ";".join(["ellipse", "html=1", f"fillColor={col(el.get('fill'))}"] + stroke_style(el)) + ";")
            return
        if tag in ("path", "polygon", "polyline"):
            vals = [float(a) for a in re.findall(r"-?\d+\.?\d*", el.get("d") or el.get("points") or "")]
            if len(vals) >= 4:
                x, y, w, h = bbox_of_numbers(vals)
                sw = num(el.get("stroke-width"), 0)
                as_image(el, x + tx - sw, y + ty - sw, w + 2 * sw, h + 2 * sw, tx, ty)
            return

    walk(root, 0, 0)
    return (f'<mxfile host="archdiag" type="device"><diagram id="archdiag" name="{html.escape(name)}">'
            f'<mxGraphModel dx="0" dy="0" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
            f'fold="1" page="1" pageScale="1" pageWidth="{W:g}" pageHeight="{H:g}" '
            f'background="{bg or "#ffffff"}" math="0" shadow="0"><root><mxCell id="0"/>'
            f'<mxCell id="1" parent="0"/>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>')


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
