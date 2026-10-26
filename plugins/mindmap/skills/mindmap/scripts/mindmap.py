#!/usr/bin/env python3
"""mindmap — Markdown outline -> XMind/MindNode-style mind map.

Exports: SVG · PNG · draw.io XML (native, editable, connected edges) · FreeMind .mm (opens in
Freeplane / XMind / MindManager) · interactive HTML (markmap, collapsible) · normalised Markdown.

Input (Markdown):
    # Root topic
    ## Branch                         heading level n  -> depth n-1
    - child                           bullets nest under the last heading (2- or 4-space indent)
      - grandchild {icon:aws/compute/elastic-kubernetes-service}
    ## Another branch {color:#7B42BC}
    - item {logo:karpenter}

Inline tags (stripped from the label): {icon:<diagrams path>} {logo:<name>} {color:#hex} {collapsed}
**bold** / `code` markers are stripped.

CLI:
    python3 mindmap.py in.md out [--layout map|right|tree] [--theme light|dark]
                       [--formats svg,png,drawio,mm,html,md] [--max-width 300]
Python:
    from mindmap import MindMap
    m = MindMap.from_markdown(text, layout="map"); m.save("out", "svg", "png", "drawio")
"""
import base64
import html
import os
import re
import sys
from dataclasses import dataclass, field

import cairosvg
from PIL import ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_FAMILY = "Inter, DejaVu Sans, sans-serif"
MARKMAP_AUTOLOADER = "https://cdn.jsdelivr.net/npm/markmap-autoloader@0.18.12"

PALETTE = ["#E07B00", "#147EBA", "#7AA116", "#D13212", "#8C4FFF", "#00A4A6",
           "#DD344C", "#4D5ED6", "#B8860B", "#E7157B"]
THEMES = {
    "light": dict(bg="#FFFFFF", root_fill="#232F3E", root_text="#FFFFFF", text="#1F2937",
                  l2_fill="#FFFFFF", muted="#5A6B86"),
    "dark": dict(bg="#141A3A", root_fill="#F2F4F8", root_text="#141A3A", text="#E8ECF4",
                 l2_fill="#1D2550", muted="#A7B1C7"),
}
# per depth: font size, weight, pad x/y, horizontal gap to children, vertical gap between siblings, edge width
LEVELS = {
    0: dict(size=34, weight=700, px=30, py=20, hgap=110, vgap=34, ew=7.0),
    1: dict(size=23, weight=600, px=20, py=12, hgap=70, vgap=26, ew=4.5),
    2: dict(size=19, weight=500, px=14, py=8, hgap=52, vgap=14, ew=2.8),
    3: dict(size=17, weight=400, px=6, py=6, hgap=44, vgap=8, ew=2.0),
}


_ICON_CACHE = {}


def icon_b64(path, px=96):
    """PNG -> base64, downscaled so embedded logos stay small in SVG/draw.io."""
    if path not in _ICON_CACHE:
        import io
        from PIL import Image
        im = Image.open(path).convert("RGBA")
        im.thumbnail((px, px), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        _ICON_CACHE[path] = base64.b64encode(buf.getvalue()).decode()
    return _ICON_CACHE[path]


def lvl(d):
    return LEVELS[min(d, 3)]


def _font_file(weight):
    name = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold"}[weight]
    for base in ("/usr/share/fonts/opentype/inter", "/usr/share/fonts/truetype/inter",
                 os.path.expanduser("~/.fonts"), "/System/Library/Fonts", "/Library/Fonts"):
        for ext in ("otf", "ttf"):
            p = os.path.join(base, f"Inter-{name}.{ext}")
            if os.path.exists(p):
                return p
    return None


_FONTS = {}


def text_width(s, size, weight):
    key = (size, weight)
    if key not in _FONTS:
        f = _font_file(weight)
        _FONTS[key] = ImageFont.truetype(f, size) if f else None
    f = _FONTS[key]
    return f.getlength(s) if f else len(s) * size * 0.56


def wrap(s, size, weight, max_w):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if cur and text_width(t, size, weight) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else []) or [""]


# ---------------------------------------------------------------- model
@dataclass
class Node:
    text: str
    depth: int
    children: list = field(default_factory=list)
    icon: str = None          # path to a PNG
    color: str = None
    collapsed: bool = False
    # layout results
    lines: list = None
    w: float = 0
    h: float = 0
    x: float = 0              # top-left
    y: float = 0
    side: int = 1             # +1 right, -1 left
    sub_h: float = 0
    id: str = ""


TAG = re.compile(r"\{(icon|logo|color|collapsed)(?::([^}]*))?\}")


def _resolve_icon(kind, ref):
    if kind == "logo":
        for d in (os.environ.get("ARCHDIAG_LOGOS"), os.path.join(os.getcwd(), "logos"),
                  os.path.join(HERE, "..", "logos"),
                  os.path.join(HERE, "..", "..", "..", "..", "arch-diagram", "skills", "arch-diagram", "logos")):
            if d and os.path.exists(os.path.join(d, ref + ".png")):
                return os.path.abspath(os.path.join(d, ref + ".png"))
        return None
    try:
        import diagrams
        p = os.path.join(os.path.dirname(diagrams.__file__), "..", "resources", ref + ".png")
        return p if os.path.exists(p) else None
    except ImportError:
        return None


def _parse_label(raw):
    icon = color = None
    collapsed = False
    for kind, ref in TAG.findall(raw):
        if kind in ("icon", "logo"):
            icon = _resolve_icon(kind, ref.strip()) or icon
        elif kind == "color":
            color = ref.strip()
        elif kind == "collapsed":
            collapsed = True
    text = TAG.sub("", raw)
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2), text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return " ".join(text.split()), icon, color, collapsed


def parse_markdown(md):
    """Headings and bullets -> Node tree. Nesting is decided on the *raw* depth (heading level / indent),
    so skipped levels (## then ####) or an indented first bullet still attach to the nearest parent."""
    root, stack, head_depth, bullet_root = None, [], 0, False
    lines = [l.rstrip().replace("\t", "    ") for l in md.splitlines()
             if l.strip() and not l.strip().startswith(("<!--", "---", "```"))]
    indents = sorted({len(l) - len(l.lstrip()) for l in lines if re.match(r"^\s*([-*+]|\d+[.)])\s", l)} - {0})
    unit = indents[0] if indents else 2
    for line in lines:
        s = line.lstrip()
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            raw = head_depth = len(m.group(1)) - 1
            label = m.group(2)
        elif re.match(r"^([-*+]|\d+[.)])\s+", s):
            ind = (len(line) - len(s)) // unit
            label = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)
            raw = ind if (bullet_root or root is None) else head_depth + 1 + ind
            if root is None:
                bullet_root = True
        else:
            continue
        text, icon, color, collapsed = _parse_label(label)
        node = Node(text, 0, icon=icon, color=color, collapsed=collapsed)
        node.raw = raw
        if root is None:
            node.raw = -1
            root, stack = node, [node]
            continue
        while len(stack) > 1 and stack[-1].raw >= raw:
            stack.pop()
        parent = stack[-1]
        node.depth = parent.depth + 1
        parent.children.append(node)
        stack.append(node)
    if root is None:
        raise ValueError("empty outline")
    return root


def walk(n):
    yield n
    for c in n.children:
        yield from walk(c)


# ---------------------------------------------------------------- layout
class MindMap:
    def __init__(self, root, layout="map", theme="light", max_width=300, palette=None):
        self.root, self.layout = root, layout
        self.t = THEMES[theme]
        self.max_width = max_width
        self.palette = palette or PALETTE
        self._colorize()
        self._measure()
        self._place()

    @classmethod
    def from_markdown(cls, md, **kw):
        return cls(parse_markdown(md), **kw)

    @classmethod
    def from_file(cls, path, **kw):
        return cls.from_markdown(open(path, encoding="utf-8").read(), **kw)

    # colours: one per level-1 branch, inherited downward unless overridden
    def _colorize(self):
        self.root.color = self.root.color or self.t["root_fill"]
        for i, b in enumerate(self.root.children):
            b.color = b.color or self.palette[i % len(self.palette)]
            for n in walk(b):
                for c in n.children:
                    c.color = c.color or n.color
        for i, n in enumerate(walk(self.root)):
            n.id = f"n{i}"

    def _measure(self):
        for n in walk(self.root):
            L = lvl(n.depth)
            maxw = 520 if n.depth == 0 else (self.max_width if n.depth >= 2 else self.max_width + 60)
            label = n.text + (f"  (+{len(n.children)})" if n.collapsed and n.children else "")
            n.lines = wrap(label, L["size"], L["weight"], maxw)
            tw = max(text_width(l, L["size"], L["weight"]) for l in n.lines)
            lh = L["size"] * 1.28
            ic = (L["size"] * 1.5 + 8) if n.icon else 0
            n.w = tw + 2 * L["px"] + ic
            n.h = max(len(n.lines) * lh, L["size"] * 1.5 if n.icon else 0) + 2 * L["py"]

    def _visible(self, n):
        return [] if n.collapsed else n.children

    def _subtree_h(self, n):
        kids = self._visible(n)
        if not kids:
            n.sub_h = n.h
        else:
            gap = lvl(n.depth + 1)["vgap"]
            n.sub_h = max(n.h, sum(self._subtree_h(c) for c in kids) + gap * (len(kids) - 1))
        return n.sub_h

    def _place_side(self, kids, x_edge, cy, side, depth):
        gap = lvl(depth)["vgap"]
        total = sum(c.sub_h for c in kids) + gap * (len(kids) - 1)
        y = cy - total / 2
        for c in kids:
            ccy = y + c.sub_h / 2
            c.side = side
            c.x = x_edge if side > 0 else x_edge - c.w
            c.y = ccy - c.h / 2
            nxt = self._visible(c)
            if nxt:
                hg = lvl(c.depth)["hgap"]
                self._place_side(nxt, (c.x + c.w + hg) if side > 0 else (c.x - hg), ccy, side, c.depth + 1)
            y += c.sub_h + gap

    def _place_tree(self, n, x, y):
        """Top-down org-chart: returns subtree width."""
        kids = self._visible(n)
        gap = 28
        if not kids:
            n.sub_w = n.w
        else:
            n.sub_w = max(n.w, sum(self._tree_w(c) for c in kids) + gap * (len(kids) - 1))
        n.x, n.y = x + (n.sub_w - n.w) / 2, y
        cx = x + (n.sub_w - (sum(c.sub_w for c in kids) + gap * (len(kids) - 1))) / 2 if kids else x
        for c in kids:
            self._place_tree(c, cx, y + n.h + 70)
            cx += c.sub_w + gap
        return n.sub_w

    def _tree_w(self, n):
        kids = self._visible(n)
        n.sub_w = n.w if not kids else max(n.w, sum(self._tree_w(c) for c in kids) + 28 * (len(kids) - 1))
        return n.sub_w

    def _place(self):
        r = self.root
        if self.layout == "tree":
            self._tree_w(r)
            self._place_tree(r, 0, 0)
        else:
            for c in self._visible(r):
                self._subtree_h(c)
            kids = self._visible(r)
            if self.layout == "right" or len(kids) < 3:
                right, left = kids, []
            else:  # ordered split minimising height difference; left side reads bottom->top (clockwise)
                hs = [c.sub_h for c in kids]
                k = min(range(1, len(kids)), key=lambda k: abs(sum(hs[:k]) - sum(hs[k:])))
                right, left = kids[:k], kids[k:][::-1]
            r.x, r.y = -r.w / 2, -r.h / 2
            hg = lvl(0)["hgap"]
            if right:
                self._place_side(right, r.w / 2 + hg, 0, 1, 1)
            if left:
                self._place_side(left, -r.w / 2 - hg, 0, -1, 1)
        nodes = [n for n in walk(r) if self._is_shown(n)]
        m = 60
        x0, y0 = min(n.x for n in nodes) - m, min(n.y for n in nodes) - m
        for n in nodes:
            n.x -= x0
            n.y -= y0
        self.W = max(n.x + n.w for n in nodes) + m
        self.H = max(n.y + n.h for n in nodes) + m

    def _is_shown(self, n, _cache=None):
        if _cache is None:
            _cache = self._shown = getattr(self, "_shown", None) or self._compute_shown()
        return n.id in _cache

    def _compute_shown(self):
        out = set()

        def rec(n):
            out.add(n.id)
            for c in self._visible(n):
                rec(c)
        rec(self.root)
        return out

    # ------------------------------------------------------------ geometry helpers
    def _out_anchor(self, n, side):
        if self.layout == "tree":
            return n.x + n.w / 2, n.y + n.h
        if self._underline(n):
            return (n.x + n.w, n.y + n.h) if side > 0 else (n.x, n.y + n.h)
        return (n.x + n.w, n.y + n.h / 2) if side > 0 else (n.x, n.y + n.h / 2)

    def _in_anchor(self, n):
        if self.layout == "tree":
            return n.x + n.w / 2, n.y
        if self._underline(n):
            return (n.x, n.y + n.h) if n.side > 0 else (n.x + n.w, n.y + n.h)
        return (n.x, n.y + n.h / 2) if n.side > 0 else (n.x + n.w, n.y + n.h / 2)

    def _underline(self, n):
        return n.depth >= 3

    # ------------------------------------------------------------ SVG
    def svg(self):
        t, out = self.t, []
        a = out.append
        a(f'<rect width="{self.W:.0f}" height="{self.H:.0f}" fill="{t["bg"]}"/>')
        # edges first
        for n in walk(self.root):
            if not self._is_shown(n):
                continue
            for c in self._visible(n):
                x1, y1 = self._out_anchor(n, c.side)
                x2, y2 = self._in_anchor(c)
                ew = lvl(n.depth)["ew"]
                if self.layout == "tree":
                    my = (y1 + y2) / 2
                    d = f"M{x1:.1f},{y1:.1f} C{x1:.1f},{my:.1f} {x2:.1f},{my:.1f} {x2:.1f},{y2:.1f}"
                else:
                    dx = (x2 - x1) * 0.55
                    d = f"M{x1:.1f},{y1:.1f} C{x1 + dx:.1f},{y1:.1f} {x2 - dx:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"
                if n.depth == 0 and self.layout != "tree":   # tapered root branch
                    a(f'<path d="{d}" fill="none" stroke="{c.color}" stroke-width="{ew + 3}" '
                      f'stroke-linecap="round" opacity=".35" class="mm-edge"/>')
                a(f'<path d="{d}" fill="none" stroke="{c.color}" stroke-width="{ew}" stroke-linecap="round" '
                  f'class="mm-edge"/>')
        for n in walk(self.root):
            if self._is_shown(n):
                self._node_svg(n, a)
        body = "\n".join(out)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.W:.0f}" height="{self.H:.0f}" '
                f'viewBox="0 0 {self.W:.0f} {self.H:.0f}">\n{body}\n</svg>')

    def _node_svg(self, n, a):
        t, L = self.t, lvl(n.depth)
        size, weight = L["size"], L["weight"]
        if n.depth == 0:
            fill, stroke, tc = n.color, "none", t["root_text"]
        elif n.depth == 1:
            fill, stroke, tc = n.color, "none", "#FFFFFF"
        elif n.depth == 2:
            fill, stroke, tc = t["l2_fill"], n.color, t["text"]
        else:
            fill, stroke, tc = "none", "none", t["text"]
        rx = n.h / 2 if n.depth <= 1 else 10
        if self._underline(n):
            a(f'<line x1="{n.x:.1f}" y1="{n.y + n.h:.1f}" x2="{n.x + n.w:.1f}" y2="{n.y + n.h:.1f}" '
              f'stroke="{n.color}" stroke-width="{lvl(n.depth - 1)["ew"]}" stroke-linecap="round"/>')
        else:
            a(f'<rect x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" height="{n.h:.1f}" rx="{rx:.1f}" '
              f'fill="{fill}" stroke="{stroke}" stroke-width="2.5"/>')
        tx = n.x + L["px"]
        if n.icon:
            s = size * 1.5
            b64 = icon_b64(n.icon)
            a(f'<image x="{tx:.1f}" y="{n.y + (n.h - s) / 2:.1f}" width="{s:.1f}" height="{s:.1f}" '
              f'href="data:image/png;base64,{b64}"/>')
            tx += s + 8
        lh = size * 1.28
        y0 = n.y + (n.h - len(n.lines) * lh) / 2 + size * 0.98
        for i, ln in enumerate(n.lines):
            a(f'<text x="{tx:.1f}" y="{y0 + i * lh:.1f}" font-family="{FONT_FAMILY}" font-size="{size}" '
              f'font-weight="{weight}" fill="{tc}">{html.escape(ln)}</text>')

    # ------------------------------------------------------------ draw.io (native: connected, editable)
    def drawio(self, name="Mind map"):
        t, cells = self.t, []
        for n in walk(self.root):
            if not self._is_shown(n):
                continue
            L = lvl(n.depth)
            base = [f"fontSize={L['size']}", f"fontFamily=Inter", "html=1", "whiteSpace=wrap", "spacing=4"]
            if L["weight"] >= 600:
                base.append("fontStyle=1")
            if n.depth == 0:
                st = ["rounded=1", "arcSize=50", f"fillColor={n.color}", "strokeColor=none", f"fontColor={t['root_text']}"]
            elif n.depth == 1:
                st = ["rounded=1", "arcSize=50", f"fillColor={n.color}", "strokeColor=none", "fontColor=#FFFFFF"]
            elif n.depth == 2:
                st = ["rounded=1", "absoluteArcSize=1", "arcSize=20", f"fillColor={t['l2_fill']}",
                      f"strokeColor={n.color}", "strokeWidth=2.5", f"fontColor={t['text']}"]
            else:
                st = ["shape=partialRectangle", "top=0", "left=0", "right=0", "bottom=1", "fillColor=none",
                      f"strokeColor={n.color}", f"strokeWidth={lvl(n.depth - 1)['ew']}", f"fontColor={t['text']}",
                      "align=left"]
            if n.icon:
                b64 = icon_b64(n.icon)
                s = int(L["size"] * 1.5)
                if n.depth < 3:   # shape=label carries the icon inside the box
                    st = ["shape=label", f"image=data:image/png,{b64}", f"imageWidth={s}", f"imageHeight={s}",
                          "imageAlign=left", f"spacingLeft={s + 8}"] + st
                else:             # partialRectangle cannot draw images -> separate image cell on top
                    st = st + [f"spacingLeft={s + 8}"]
                    cells.append(f'<mxCell id="{n.id}i" value="" style="shape=image;image=data:image/png,{b64};'
                                 f'imageAspect=1;aspect=fixed;" vertex="1" parent="1"><mxGeometry '
                                 f'x="{n.x + L["px"]:.1f}" y="{n.y + (n.h - s) / 2:.1f}" width="{s}" height="{s}" '
                                 f'as="geometry"/></mxCell>')
            style = ";".join(base + st) + ";"
            cells.append(f'<mxCell id="{n.id}" value="{html.escape(" ".join(n.lines))}" style="{html.escape(style)}" '
                         f'vertex="1" parent="1"><mxGeometry x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" '
                         f'height="{n.h:.1f}" as="geometry"/></mxCell>')
        for n in walk(self.root):
            if not self._is_shown(n):
                continue
            for c in self._visible(n):
                ew = lvl(n.depth)["ew"]
                if self.layout == "tree":
                    ex, ey, nx_, ny_ = 0.5, 1, 0.5, 0
                else:
                    r = c.side > 0
                    ex = 1 if r else 0
                    ey = 1 if self._underline(n) else 0.5
                    nx_ = 0 if r else 1
                    ny_ = 1 if self._underline(c) else 0.5
                style = (f"edgeStyle=none;curved=1;rounded=1;html=1;endArrow=none;startArrow=none;"
                         f"strokeColor={c.color};strokeWidth={ew};exitX={ex};exitY={ey};exitDx=0;exitDy=0;"
                         f"entryX={nx_};entryY={ny_};entryDx=0;entryDy=0;")
                x1, y1 = self._out_anchor(n, c.side)
                x2, y2 = self._in_anchor(c)
                if self.layout == "tree":
                    my = (y1 + y2) / 2
                    pts = f'<Array as="points"><mxPoint x="{x1:.1f}" y="{my:.1f}"/><mxPoint x="{x2:.1f}" y="{my:.1f}"/></Array>'
                else:
                    mx = (x1 + x2) / 2
                    pts = f'<Array as="points"><mxPoint x="{mx:.1f}" y="{y1:.1f}"/><mxPoint x="{mx:.1f}" y="{y2:.1f}"/></Array>'
                cells.append(f'<mxCell id="e{c.id}" style="{html.escape(style)}" edge="1" parent="1" '
                             f'source="{n.id}" target="{c.id}"><mxGeometry relative="1" as="geometry">{pts}'
                             f'</mxGeometry></mxCell>')
        # edges before vertices so nodes sit on top
        edges = [c for c in cells if 'edge="1"' in c]
        verts = [c for c in cells if 'edge="1"' not in c and 'i" value=""' not in c]
        verts += [c for c in cells if 'i" value=""' in c]
        return (f'<mxfile host="mindmap" type="device"><diagram id="mindmap" name="{html.escape(name)}">'
                f'<mxGraphModel dx="0" dy="0" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" '
                f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.W:.0f}" pageHeight="{self.H:.0f}" '
                f'background="{t["bg"]}" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
                + "".join(edges + verts) + '</root></mxGraphModel></diagram></mxfile>')

    # ------------------------------------------------------------ FreeMind / markdown / markmap
    def freemind(self):
        def rec(n, side=None):
            attrs = f'TEXT="{html.escape(n.text, quote=True)}" ID="ID_{n.id}"'
            if n.depth == 1:
                attrs += f' POSITION="{"right" if n.side > 0 else "left"}"'
            if n.depth >= 1:
                attrs += f' COLOR="{n.color}"'
            if n.collapsed:
                attrs += ' FOLDED="true"'
            inner = "".join(rec(c) for c in n.children)
            edge = f'<edge COLOR="{n.color}"/>' if n.depth >= 1 else ""
            return f"<node {attrs}>{edge}{inner}</node>"
        return f'<map version="1.0.1">{rec(self.root)}</map>\n'

    def markdown(self):
        out = [f"# {self.root.text}"]

        def rec(n, ind):
            for c in n.children:
                fold = " <!-- markmap: fold -->" if c.collapsed else ""
                if c.depth == 1:
                    out.append(f"\n## {c.text}{fold}")
                    rec(c, 0)
                else:
                    out.append("  " * ind + f"- {c.text}{fold}")
                    rec(c, ind + 1)
        rec(self.root, 0)
        return "\n".join(out) + "\n"

    def markmap_html(self, title=None):
        md = self.markdown()
        # markmap assigns colours in visit order: root first, then each level-1 branch
        colors = ",".join(f'"{n.color}"' for n in [self.root] + self.root.children)
        return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title or self.root.text)}</title>
<style>html,body{{margin:0;height:100%;background:{self.t['bg']};font-family:{FONT_FAMILY}}}
.markmap{{position:relative;height:100vh;--markmap-text-color:{self.t['text']}}}.markmap>svg{{width:100%;height:100%;--markmap-text-color:{self.t['text']}}}
.markmap-foreign,.markmap-foreign *{{color:{self.t['text']} !important}}</style>
<script>window.markmap={{autoLoader:{{toolbar:true}}}};</script></head><body>
<div class="markmap"><script type="text/template">
---
markmap:
  colorFreezeLevel: 2
  initialExpandLevel: -1
  maxWidth: {self.max_width}
  color: [{colors}]
---
{md.replace("</script", "<\\/script")}
</script></div>
<script src="{MARKMAP_AUTOLOADER}"></script></body></html>
"""

    # ------------------------------------------------------------ save
    def save(self, stem, *formats):
        formats = formats or ("svg", "png")
        out = []
        svg = None
        if {"svg", "png"} & set(formats):
            svg = self.svg()
        if "svg" in formats:
            open(stem + ".svg", "w", encoding="utf-8").write(svg)
            out.append(stem + ".svg")
        if "png" in formats:
            cairosvg.svg2png(bytestring=svg.encode(), write_to=stem + ".png", output_width=int(self.W))
            out.append(stem + ".png")
        if "drawio" in formats:
            open(stem + ".drawio", "w", encoding="utf-8").write(self.drawio(self.root.text))
            out.append(stem + ".drawio")
        if "mm" in formats:
            open(stem + ".mm", "w", encoding="utf-8").write(self.freemind())
            out.append(stem + ".mm")
        if "html" in formats:
            open(stem + ".html", "w", encoding="utf-8").write(self.markmap_html())
            out.append(stem + ".html")
        if "md" in formats:
            open(stem + ".md", "w", encoding="utf-8").write(self.markdown())
            out.append(stem + ".md")
        return out


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Markdown outline -> mind map")
    ap.add_argument("input")
    ap.add_argument("out", help="output stem (no extension)")
    ap.add_argument("--layout", default="map", choices=["map", "right", "tree"])
    ap.add_argument("--theme", default="light", choices=list(THEMES))
    ap.add_argument("--formats", default="svg,png")
    ap.add_argument("--max-width", type=int, default=300)
    a = ap.parse_args(argv)
    m = MindMap.from_file(a.input, layout=a.layout, theme=a.theme, max_width=a.max_width)
    for p in m.save(a.out, *a.formats.split(",")):
        print(p)


if __name__ == "__main__":
    main(sys.argv[1:])
