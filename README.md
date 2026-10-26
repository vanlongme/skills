# vanlongme/skills

Plugin marketplace of reusable agent skills. Works with Claude Code (plugin marketplace) and with the
cross-agent [`skills`](https://skills.sh) CLI (Codex, Cursor, Gemini CLI, Copilot, OpenCode, …).

| Plugin | Skill | What it does |
|---|---|---|
| `arch-diagram` | [`arch-diagram`](plugins/arch-diagram/skills/arch-diagram/SKILL.md) | Lucidchart/AWS-style architecture diagrams (accounts, VPC tiers, K8s namespaces, official logos, edge-attached arrows, animated connectors) from a short Python script → SVG · PNG · GIF · draw.io XML |
| `mindmap` | [`mindmap`](plugins/mindmap/skills/mindmap/SKILL.md) | XMind-style mind maps from a Markdown outline (two-sided / right / tree, branch colours, icons, Vietnamese text) → SVG · PNG · draw.io XML · FreeMind `.mm` · interactive markmap HTML |

## Install

**Claude Code**

```bash
/plugin marketplace add vanlongme/skills
/plugin install arch-diagram@vanlongme
/plugin install mindmap@vanlongme
```

Skills are invoked as `/arch-diagram:arch-diagram` and `/mindmap:mindmap`, or picked up automatically when you ask
for a diagram / mind map.
Update later with `/plugin marketplace update vanlongme`.

**Other agents** (Codex, Cursor, Gemini CLI, Copilot, OpenCode, …)

```bash
npx skills add vanlongme/skills               # pick agents interactively
npx skills add vanlongme/skills -a codex -g   # e.g. global install for Codex
```

**claude.ai**: zip `plugins/<plugin>/skills/<skill>` and upload it as a custom skill.

> Private repo: the machine needs git access to `github.com/vanlongme/skills` (SSH key or `gh auth login`).

## First run

```bash
bash <arch-diagram skill>/scripts/setup.sh   # pip deps + 24 brand logos + JetBrains Mono (Vietnamese mono text)
bash <mindmap skill>/scripts/setup.sh        # pip deps; reuses arch-diagram logos for {logo:name}
```

## Layout

```
.claude-plugin/marketplace.json            # marketplace catalog
plugins/<plugin>/.claude-plugin/plugin.json
plugins/<plugin>/skills/<skill>/SKILL.md   # + scripts/, examples/, assets/
```

Add a plugin: create `plugins/<name>/` with the same structure, append an entry to `marketplace.json`, bump
`version` in its `plugin.json`, then run `claude plugin validate .`.

## arch-diagram previews

Animated connectors (`flow="dash"` / `flow="dot"`), exported as GIF — the same script also writes an animated
SVG and an editable [`.drawio`](plugins/arch-diagram/skills/arch-diagram/examples/aws_aft_animated.drawio):

![Animated AFT](plugins/arch-diagram/skills/arch-diagram/assets/previews/aws_aft_animated.gif)

| | |
|---|---|
| ![AFT](plugins/arch-diagram/skills/arch-diagram/assets/previews/aws_aft_reference.png) | ![EKS deps](plugins/arch-diagram/skills/arch-diagram/assets/previews/eks_private_dependencies.png) |
| ![Platform blueprint](plugins/arch-diagram/skills/arch-diagram/assets/previews/eks_platform_blueprint.png) | ![AI gateway](plugins/arch-diagram/skills/arch-diagram/assets/previews/ai_gateway_hybrid.png) |
| ![Hybrid landing zone](plugins/arch-diagram/skills/arch-diagram/assets/previews/hybrid_landing_zone.png) | ![Slide style](plugins/arch-diagram/skills/arch-diagram/assets/previews/slide_dark_zones.png) |

## mindmap previews

```bash
python3 scripts/mindmap.py examples/devsecops_toolchain.md out --formats svg,png,drawio,mm,html
```

![DevSecOps mind map](plugins/mindmap/skills/mindmap/assets/previews/devsecops_toolchain.png)

| `--layout right` | `--layout tree --theme dark` |
|---|---|
| ![Migration plan](plugins/mindmap/skills/mindmap/assets/previews/aws_migration_plan.png) | ![Tree dark](plugins/mindmap/skills/mindmap/assets/previews/aws_migration_tree_dark.png) |

Interactive export (markmap, collapsible): ![markmap](plugins/mindmap/skills/mindmap/assets/previews/markmap_html.png)

Brand logos are trademarks of their owners; `fetch_logos.py` downloads them from public sources at setup
time instead of storing them in this repo.
