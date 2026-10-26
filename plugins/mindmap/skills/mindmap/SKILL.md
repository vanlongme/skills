---
name: mindmap
description: Draw XMind/MindNode-style mind maps from a Markdown outline: balanced two-sided map, right-only or top-down tree, coloured branches, tapered curved connectors, AWS/K8s icons and brand logos, Vietnamese text. Exports SVG, PNG, editable draw.io XML, FreeMind .mm (opens in Freeplane/XMind) and interactive collapsible HTML (markmap). Use for "vẽ mindmap", "mind map", brainstorm/topic maps, study notes, plan breakdowns, toolchain overviews.
---

# mindmap

Turn an outline into a mind map with one command. The outline is the source of truth: write it first, render,
look at the PNG, adjust the outline (not the pixels), re-render.

| File | Purpose |
|---|---|
| `scripts/mindmap.py` | parser + layout + exporters (CLI and `MindMap` class) |
| `scripts/preview.py` | screenshot a `.drawio` (official viewer) or markmap `.html` to verify it |
| `scripts/setup.sh` | pip deps (cairosvg, pillow, diagrams for icons) |
| `examples/*.md` | DevSecOps toolchain (logos/icons), AWS migration plan (Vietnamese, collapsed node) |

## Why this approach (research summary)

- **markmap** (Markdown → interactive SVG, d3) is the best *viewer*: zoom, pan, fold. Its static output is
  plain (text on lines, one side only) and needs a browser, so it is used for the `.html` export only.
- **Mermaid `mindmap`** renders inside Markdown hosts but has little layout control and no two-sided balance.
- **XMind / FreeMind / Freeplane** are where people *edit* maps → FreeMind `.mm` is the interchange format
  (Freeplane opens it, XMind and MindManager import it).
- **draw.io** is where architecture diagrams already live → native vertices + connected edges so moving a node
  drags its branches.
- Own layout (Python) gives the XMind look for slides/docs: balanced sides, pill branches, tapered curves.

## Workflow

1. `bash scripts/setup.sh` once.
2. Write the outline (`.md`). Keep labels short (≤ 6 words); 4–8 level-1 branches; ≤ 4 levels deep. Long labels
   wrap at `--max-width` (default 300 px).
3. Render: `python3 scripts/mindmap.py map.md out --formats svg,png,drawio,mm,html`
4. **Look at `out.png`** (Read it). Check: no overlapping boxes, sides balanced, wrapped text OK, icons resolved.
   Crop zoomed areas with PIL if the map is large.
5. If you exported draw.io or HTML, verify them too: `python3 scripts/preview.py out.drawio out_drawio.png`.
6. Deliver the PNG (or SVG) plus the editable format the user needs (`.drawio`, `.mm` or `.html`).

## Outline syntax

```markdown
# Root topic {icon:aws/compute/elastic-kubernetes-service}
## Branch A {color:#E07B00}          <- heading level n => depth n-1
- child {icon:onprem/vcs/gitlab}    <- bullets nest under the last heading (2- or 4-space indent)
  - grandchild {logo:kyverno}
## Branch B
- big subtree {collapsed}           <- children hidden, label gets "(+N)"; folded in .mm/.html too
  - hidden child
```

- Root = first `#` heading (or first bullet). `##` = level 1, `###` = level 2, then bullets continue deeper.
  Pure bullet outlines work too (first bullet is the root).
- `{icon:<path>}` = any icon of the `diagrams` package without `.png`
  (`aws/compute/ec2`, `k8s/compute/pod`, `onprem/gitops/argocd`, `onprem/monitoring/grafana`, …).
  Find names: `ls $(python3 -c "import diagrams,os;print(os.path.dirname(diagrams.__file__))")/../resources/onprem/*`.
- `{logo:<name>}` = PNG from `./logos`, `$ARCHDIAG_LOGOS`, or the sibling **arch-diagram** skill's `logos/`
  (run its `setup.sh` to fetch 24 brand logos). Never draw a fake brand mark; leave the icon out instead.
- `{color:#hex}` on a branch overrides its palette colour (children inherit).
- `**bold**`, `` `code` `` and `[links](…)` are stripped to plain text.

## Options

| CLI | Python | Notes |
|---|---|---|
| `--layout map` | `layout="map"` | default; level-1 branches split into two balanced sides, read clockwise |
| `--layout right` | `layout="right"` | all branches to the right (timelines, plans, few branches) |
| `--layout tree` | `layout="tree"` | top-down org chart (shallow hierarchies; gets wide fast) |
| `--theme light/dark` | `theme=` | dark = navy background, light root |
| `--max-width 300` | `max_width=` | wrap width for level ≥ 2 labels |
| `--formats svg,png,drawio,mm,html,md` | `m.save(stem, *formats)` | `md` = normalised outline |

```python
import sys; sys.path.insert(0, "<skill>/scripts")
from mindmap import MindMap
m = MindMap.from_markdown(open("map.md").read(), layout="map", theme="light")
m.save("out", "svg", "png", "drawio", "mm", "html")
```

## Visual grammar (keep it)

- Root: dark pill, 34 px bold. Level 1: pill filled with the branch colour, white 23 px. Level 2: white rounded box
  with branch-colour border. Level 3+: text on a coloured underline (XMind style) — connectors attach to the
  underline end, not the text centre.
- One colour per level-1 branch, inherited by its whole subtree. Palette is AWS-ish and colour-blind safe enough
  to tell neighbours apart; override with `{color:}` when a branch has a meaning (red = risk, green = done).
- Connectors are cubic Béziers whose width tapers by depth (7 → 4.5 → 2.8 → 2).

## Exports

- **SVG/PNG**: icons embedded (downscaled to 96 px) — the file is self-contained.
- **draw.io**: every topic is a vertex, every connector an edge with `source`/`target`, curved, no arrowheads;
  level 3+ use `shape=partialRectangle` (bottom border = underline) with a separate image cell for icons.
  Edit in draw.io / diagrams.net; drag a node and its edges follow.
- **FreeMind `.mm`**: topics, side (`POSITION`), colours, folded state. Opens in Freeplane, imports into XMind,
  MindManager, MindMeister. Icons are not carried.
- **HTML (markmap)**: one self-contained page loading `markmap-autoloader@0.18.12` from jsDelivr; branch colours
  match the PNG; collapsed nodes fold (`<!-- markmap: fold -->`); toolbar with zoom/fit. Needs internet to view.

## Failure list

- Branch too tall on one side → split it into two level-1 branches or use `{collapsed}` for detail.
- Labels that are sentences → shorten; mind maps are keywords.
- Icon silently missing → wrong `{icon:}` path or logo not fetched; check with `ls` before rendering.
- Text measurement uses Inter via PIL; without Inter installed widths are estimated and boxes may be loose.
