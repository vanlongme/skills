---
name: arch-diagram
description: Draw Lucidchart/AWS-style architecture diagrams (nested accounts/VPC/subnet tiers, official AWS/K8s/CNCF/vendor logos, edge-attached orthogonal arrows, numbered flows) as SVG+PNG, or recreate one from a reference image.
---

# arch-diagram

Absolute-layout architecture diagrams that look hand-made in Lucidchart: nested accounts, VPCs, subnet
tiers and namespaces; official service/product logos; arrows that attach to **group edges** with explicit
orthogonal routes; numbered steps with a legend. Output: `<name>.png`, `<name>.svg` and the generator
`<name>.py` (the editable source).

Everything lives next to this file:

| Path | Purpose |
|---|---|
| `scripts/archdiag.py` | the library (`Canvas`, helpers, CLI: `grid`, `compare`, `crop`, `find`) |
| `scripts/fetch_logos.py` | downloads 24 brand logos missing from the `diagrams` icon set into `logos/` |
| `scripts/install_fonts.py` | JetBrains Mono for Vietnamese monospace text |
| `scripts/setup.sh` | pip deps + logos + fonts in one go |
| `examples/*.py` | verified diagrams to copy patterns from (previews in `assets/previews/`) |

## Why not Graphviz / `diagrams` / Mermaid
Auto-layout engines end arrows at node centres, pick their own routes and won't place a box "below" in an
LR graph. When connection points matter, every box, icon and arrow point must be explicit.

## Workflow
1. **Setup** (once per session): `bash <skill>/scripts/setup.sh`, then work in a fresh folder with
   `sys.path.insert(0, "<skill>/scripts")` (examples show the exact header). Graphviz is NOT needed.
2. **Measure** (reference image given): `python3 archdiag.py grid ref.png grid.png 50 2590` and read
   coordinates from the grid labels, never from the downscaled preview.
   No reference: sketch columns (stages) × rows first; canvas 2600–4500 wide.
3. **Inventory before coding**
   - containers outer → inner (account → region → VPC → subnet tier → cluster → namespace)
   - icons: `python3 archdiag.py find <keyword>`; brand logos: `logo("<name>")` (see list below)
   - every arrow: source edge → target edge, route (straight / `elbow via_x` / `via_y` / points), colour
4. **Code** one `<name>.py`. Keep one shared row `Y` per flow so horizontal arrows are perfectly straight.
5. **Render & verify** — never ship the first render:
   - read the full PNG, then `python3 archdiag.py crop out.png c.png x1 y1 x2 y2` on every dense area
   - with a reference: `python3 archdiag.py compare ref.png out.png cmp.png`
   - check the **failure list** below, fix, re-render.
6. **Deliver** PNG + SVG + `.py` (zip with `logos/` if the script uses `logo()`).

## Connection rules
- Attach to the edge the flow crosses: `a.right(Y) → b.left(Y)`; vertical: `a.bottom(x) → b.top(x)`.
  A group box is a valid endpoint — prefer it when the arrow "enters a zone".
- Fan-out: one shared trunk — `c.elbow(src.right(Y), tN.left(yN), via_x=X)` with the same `X`.
- Several routes leaving the same port: offset trunks by ±16 px and **order them by where they turn**
  (the route that turns first sits nearest its destination) so no two cross.
- Long paths travel in the **gaps** between containers, never along a border line or through a label.
- Arrow that starts below an icon must start **below its label** (`(icon.cx, icon.y2 + 48)`), not at `icon.bottom()`.
- Bidirectional link = two arrows (`a→b` and `b→a`) or two parallel arrows 16 px apart.
- Colours: `line` pipeline, `ink` cross-account / provisioning / AWS API, `accent` + `dashed` optional/backup,
  custom hex for a flow family (secrets blue dashed, telemetry orange, hybrid teal, KMS red dashed).

## Helpers (in `Canvas`)
`box()` outer/dashed/solid/grey/dotted with `tab="aws"` · `card()` rounded custom box ·
`tier(x1,y1,x2,y2, public, label)` subnet band (green public / blue private) · `pill()` VPC endpoint row
returning its centre y (align target icons to it for straight arrows) · `chip()` ownership badge
(e.g. Terraform vs Argo CD) · `marker(x,y,n)` numbered step **placed on a line** · `tab_label()` label on a
dashed border · `placeholder()` dashed tile when no official logo exists · `icon_c()` icon by centre ·
`mono()` monospace text (CRDs, CIDRs, config keys).

## Logos
`diagrams` ships AWS/Azure/GCP/K8s/on-prem icons. `fetch_logos.py` adds: sonatype (Nexus), coverity,
blackduck, cosign, kyverno, tetragon, keycloak, gateway-api, cilium, karpenter, keda, nvidia, alloy,
agentgateway, modelcontextprotocol, vllm, langgraph, openai, anthropic, claude, langchain, crewai, jira,
confluence. New logo: add one line to `SOURCES` (simple-icons slug, @iconify-json/logos key, or raw URL from
the project's own repo / `cncf/artwork`). Order of search: `diagrams` → simple-icons → iconify logos →
project repo → CNCF artwork.
**Never fake a brand mark** (no look-alike drawing, no other product's logo). If none is obtainable
(known: Seeker IAST, Bottlerocket) use `placeholder()` or plain text and tell the user.
Dark logos on dark backgrounds: put them on a light rounded tile.

## Layout patterns that worked (see examples)
- **Lanes** (`eks_private_dependencies.py`): one row per concern → `component → VPC endpoint → AWS service →
  KMS usage`; arrows are all horizontal.
- **Accounts + VPC tiers** (`eks_platform_blueprint.py`, `hybrid_landing_zone.py`): Network / Platform /
  Observability accounts; public · private-ingress · private-mgmt · private-app · private-data tiers;
  regional-services column aligned with endpoint pills.
- **Cluster internals**: namespace columns on one pipeline row + platform-services row + CNI row +
  compute layer (MNG with Cluster Autoscaler, Karpenter NodePools); ownership chips per namespace.
- **Gateway fan-out** (`ai_gateway_hybrid.py`): policy chain → listeners → backends with ordered trunks;
  separate inference cluster and on-prem branch reached in a lower row.
- **Slide style** (`slide_dark_zones.py`): dark background, grid, zone cards — use when the user wants to
  match a presentation, not an AWS diagram.
- Numbered markers on the flows + a legend row of steps (in the user's language) at the bottom.

## Failure list — check every render
- label crossed by an arrow or a border (move the label, or `tab_label()`; keep text ≥ 8 px from lines)
- arrow ending on a label instead of an icon/box edge
- marker floating off its line
- two routes overlapping/crossing on a shared trunk (offset ±16 px, reorder)
- inner box touching its container border (keep ≥ 20 px)
- text overflowing its box (shrink `size` or wrap to 2 lines)
- missing glyphs (□) in Vietnamese text: install fonts (`install_fonts.py`), use Inter / JetBrains Mono
- placeholder or substituted logo not disclosed to the user

## Styling defaults
Canvas ≥ 2590 wide; icons 56–85 px with ≤ 2-line labels (15–23 px); group labels 18–21 px; AWS tabs 60 px.
Override colours: `Canvas(w, h, theme={"accent": "#...", "badge": "#..."})`, or pass hex to `color=`.
