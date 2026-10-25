"""Centralized AI platform v2 — agentgateway + dedicated hosted-LLM GPU cluster + hybrid on-prem GPU.

Row A : consumers -> AI Platform cluster (agentgateway: policy chain -> A2A / MCP / LLM) -> SaaS backends
Row B : shared platform services (IdP, Vault, rate limit, observability, audit)
Row C : AI Inference account (EKS GPU, vLLM + Inference Extension) · Network account (TGW, DX) · On-prem GPU DC
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from archdiag import Canvas, logo  # noqa: E402

LOGO = logo

c = Canvas(2920, 2720)
MUTED, SOFT = "#3A4450", "#5A6B86"
AGW, BLUE, GPU = "#7B2FBE", "#147EBA", "#4E8A00"
OTEL, SEC, HYB = "#D9480F", "#3B8FD9", "#0B7A75"


def ic(name, cx, cy, label=None, s=72, size=17):
    return c.icon(name, cx - s / 2, cy - s / 2, s, label=label, size=size)


def marker(x, y, n):
    c.over.append(f'<circle cx="{x}" cy="{y}" r="16" fill="#E07B00" stroke="white" stroke-width="3"/>')
    c.over.append(f'<text x="{x}" y="{y + 6.5}" font-family="{c.t["font"]}" font-size="18" font-weight="700" '
                  f'fill="white" text-anchor="middle">{n}</text>')


def card(x1, y1, x2, y2, stroke, fill="white", rx=10, dash=None, sw=2.5):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    c.under.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="{rx}" fill="{fill}" '
                   f'stroke="{stroke}" stroke-width="{sw}"{da}/>')
    return c.box(x1, y1, x2, y2, "none")


def mono(x, y, s, size=16, anchor="middle", color=MUTED):
    c.under.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans Mono, monospace" font-size="{size}" '
                   f'fill="{color}" text-anchor="{anchor}">{s}</text>')


# ================================================================== title
c.text(40, 64, "Centralized AI platform · agentgateway · hosted LLM · hybrid on-prem", 34, "start", weight=700)
c.text(40, 100, "agentgateway: Linux Foundation · Agentic AI Foundation (AAIF) — LLM · MCP · A2A gateway trên Kubernetes Gateway API "
       "+ Gateway API Inference Extension", 18, "start", color=SOFT)

# ================================================================== ROW A · consumers
cons = c.box(40, 450, 440, 1300, "grey", "Consumers", size=20)
ic("k8s/compute/pod", 140, 560, "AI agents\n(LangGraph · CrewAI)")
ic("k8s/compute/deploy", 340, 560, "Apps /\nmicroservices")
ic(LOGO("claude"), 140, 780, "Coding assistants\n(Claude Code, IDE)", s=64)
ic("onprem/client/users", 340, 780, "Chat UI\n(Open WebUI)")
ic("aws/general/traditional-server", 240, 990, "On-prem apps\n(qua DX · TGW)", s=64)
c.text(240, 1138, "Cùng 1 endpoint:", 17, color=MUTED, weight=600)
for i, s in enumerate(["/v1/chat/completions · /mcp · /a2a"]):
    mono(240, 1172, s, 15)
c.text(240, 1210, "auth: OIDC JWT · API key", 16, color=SOFT)

# ================================================================== ROW A · AI platform (gateway) cluster
pcl = c.box(500, 120, 2170, 1320, "solid", "AI Platform account · EKS gateway cluster", tab="aws")
alb = ic("aws/network/elb-application-load-balancer", 615, 885, "Internal ALB\n(Gateway API)", s=80)

cp = card(840, 200, 1490, 410, "#B7BFCC", fill="#F7F8FA", dash="8 6")
c.text(856, 228, "Control plane · ns agentgateway-system", 18, "start", weight=600, color=MUTED)
argo = ic("onprem/gitops/argocd", 920, 310, "Argo CD", s=64, size=16)
c.under.append('<rect x="1010" y="262" width="300" height="104" rx="8" fill="white" stroke="#D0D5DD" stroke-width="1.5"/>')
for i, s in enumerate(["Gateway · HTTPRoute", "AgentgatewayBackend", "AgentgatewayPolicy"]):
    mono(1160, 290 + i * 30, s)
ctl = ic(LOGO("agentgateway"), 1410, 305, "controller", s=60, size=16)

dp = card(840, 450, 1490, 1285, AGW, fill="#FBF7FF")
c.icon(LOGO("agentgateway"), 856, 462, 36)
c.text(900, 488, "agentgateway proxy · data plane (Rust)", 19, "start", weight=700, color=AGW)
pc = card(862, 520, 1072, 1262, "#E0A458", fill="#FFFBF5", rx=8)
c.text(967, 548, "Policy chain", 17, weight=700, color="#9A5B00")
pills = [("AuthN", "JWT · API key"), ("AuthZ", "CEL RBAC"), ("Rate limit", "token quota / team"),
         ("Guardrails", "PII · data-class"), ("Telemetry", "OTel spans")]
for i, (a, b) in enumerate(pills):
    y = 568 + i * 136
    c.under.append(f'<rect x="878" y="{y}" width="178" height="112" rx="10" fill="#FFF4E5" stroke="#F0C27B" stroke-width="1.5"/>')
    c.text(967, y + 46, a, 18, weight=700, color="#7A4A00")
    c.text(967, y + 76, b, 15, color="#7A4A00")
    if i < len(pills) - 1:
        c.arrow((967, y + 112), (967, y + 134), color="#C98A2B", width=2)

YA, YM, YL = 605, 905, 1165
lst = {}
for key, y1, title, logo, l1, l2 in [
    ("a2a", 520, "A2A gateway", "agentgateway", "agent card · /a2a", "task routing · authz per agent"),
    ("mcp", 820, "MCP gateway", "modelcontextprotocol", "tool federation · /mcp", "stdio · SSE · Streamable HTTP"),
    ("llm", 1080, "LLM gateway", "openai", "OpenAI-compatible · /v1/*", "route by model · data-class · cost")]:
    b = card(1112, y1, 1472, y1 + 170, AGW, fill="white")
    c.icon(LOGO(logo), 1128, y1 + 18, 44)
    c.text(1184, y1 + 50, title, 20, "start", weight=700, color=AGW)
    c.text(1130, y1 + 100, l1, 16, "start", color=MUTED)
    c.text(1130, y1 + 128, l2, 16, "start", color=MUTED)
    lst[key] = b

agents = card(1600, 450, 2140, 655, BLUE, fill="#F2F8FD")
c.text(1616, 478, "ns agents (A2A servers)", 17, "start", weight=600, color=BLUE)
ic(LOGO("langgraph"), 1720, 560, "Credit-review\nagent", s=56, size=15)
ic(LOGO("crewai"), 1880, 560, "Ops / SRE\nagent", s=64, size=15)
ic("k8s/compute/pod", 2040, 560, "Team agents\n(any framework)", s=56, size=15)

mcps = card(1600, 760, 2140, 965, BLUE, fill="#F2F8FD")
c.text(1616, 788, "ns mcp-servers (internal tools)", 17, "start", weight=600, color=BLUE)
ic("onprem/vcs/gitlab", 1700, 860, "GitLab MCP", s=56, size=15)
ic(LOGO("jira"), 1870, 860, "Jira /\nConfluence MCP", s=52, size=15)
ic("k8s/network/svc", 2040, 860, "OpenAPI → MCP\n(internal APIs)", s=56, size=15)

rmcp = c.box(2210, 760, 2880, 1060, "dashed", "Remote MCP (SaaS)", label_pos="top-left", size=19)
ic("onprem/vcs/github", 2350, 900, "GitHub MCP", s=64)
ic("saas/chat/slack", 2545, 900, "Slack MCP", s=64)
ic(LOGO("confluence"), 2740, 900, "Atlassian MCP", s=56)

prov = c.box(2210, 1120, 2880, 1420, "dashed", "External LLM providers (fallback)", label_pos="top-left", size=19)
ic("aws/ml/bedrock", 2330, 1250, "Amazon Bedrock\n(PrivateLink)", s=72)
ic("azure/aimachinelearning/azure-openai", 2545, 1250, "Azure OpenAI", s=72)
ic(LOGO("anthropic"), 2760, 1230, None, s=56)
ic(LOGO("openai"), 2760, 1295, None, s=46)
c.text(2760, 1370, "Anthropic · OpenAI", 17)
c.text(2760, 1392, "(egress proxy)", 15, color=SOFT)

# ================================================================== ROW B · shared services
sh = c.box(840, 1470, 2880, 1750, "dashed")
c.text(2426, 1502, "Shared platform services", 19, "start")
idp = card(860, 1520, 1060, 1730, "#D0D5DD", fill="#F7F8FA")
ic(LOGO("keycloak"), 960, 1595, "IdP · OIDC\nKeycloak / Entra", s=56, size=15)
vlt = card(1080, 1520, 1280, 1730, "#D0D5DD", fill="#F7F8FA")
ic("onprem/security/vault", 1180, 1595, "Vault · ESO\nprovider keys", s=56, size=15)
rl = card(1300, 1520, 1490, 1730, "#D0D5DD", fill="#F7F8FA")
ic("onprem/inmemory/redis", 1395, 1595, "Global rate\nlimit (Redis)", s=56, size=15)
obs = card(1600, 1520, 2380, 1730, "#D0D5DD", fill="#F7F8FA")
c.text(1616, 1548, "Observability · FinOps", 17, "start", weight=600, color=MUTED)
ic(LOGO("alloy"), 1700, 1610, "Alloy (OTel)", s=52, size=15)
ic("onprem/monitoring/grafana", 1860, 1610, "Grafana", s=52, size=15)
ic("onprem/monitoring/mimir", 2020, 1610, "Mimir", s=52, size=15)
ic("onprem/tracing/tempo", 2180, 1610, "Tempo", s=52, size=15)
c.text(1990, 1714, "tokens · TTFT · GPU util (DCGM) · cost per team / model", 14, color=SOFT)
aud = card(2410, 1520, 2860, 1730, "#D0D5DD", fill="#F7F8FA")
c.text(2426, 1548, "Audit & compliance", 17, "start", weight=600, color=MUTED)
ic("onprem/logging/loki", 2530, 1610, "Loki\nprompt / tool log", s=52, size=15)
ic("aws/storage/simple-storage-service-s3", 2730, 1610, "S3 (WORM)\nretention", s=52, size=15)

# ================================================================== ROW C · AI Inference account (hosted LLM)
inf = c.box(500, 1810, 1960, 2450, "solid", "AI Inference account · dedicated EKS GPU cluster (hosted LLM)", tab="aws")

igw = card(1460, 1880, 1940, 2110, GPU, fill="#F5FAEE")
c.text(1476, 1908, "Inference gateway", 17, "start", weight=700, color=GPU)
nlb = ic("aws/network/elb-network-load-balancer", 1545, 1980, "Internal NLB", s=56, size=15)
ic(LOGO("agentgateway"), 1700, 1980, "agentgateway\n(inference mode)", s=52, size=15)
ic("k8s/compute/deploy", 1855, 1980, "EPP\nendpoint picker", s=56, size=15)

pools = card(860, 1880, 1420, 2240, GPU, fill="white")
c.text(876, 1908, "InferencePools · vLLM model servers", 17, "start", weight=700, color=GPU)
for (y1, name, d1, d2, n) in [(1925, "llama-3.3-70b", "vLLM · TP=4 · prefix cache", "p5.48xlarge · 8×H100", 3),
                              (2085, "qwen2.5-coder-32b", "vLLM · LoRA adapters / team", "g6e.12xlarge · 4×L40S", 2)]:
    c.under.append(f'<rect x="876" y="{y1}" width="528" height="140" rx="8" fill="#F5FAEE" stroke="#B9D58C" stroke-width="1.5"/>')
    mono(892, y1 + 28, f"pool: {name}", 16, "start", GPU)
    for k in range(n):
        c.icon(LOGO("vllm"), 892 + k * 62, y1 + 48, 50)
    c.text(1100, y1 + 74, d1, 15, "start", color=MUTED)
    c.text(1100, y1 + 100, d2, 15, "start", color=MUTED)
PA, PB = 1995, 2155

store = card(530, 1880, 820, 2240, "#D0D5DD", fill="#F7F8FA")
c.text(546, 1908, "Model store", 17, "start", weight=700, color=MUTED)
s3m = ic("aws/storage/simple-storage-service-s3", 675, 1985, "Model registry\nS3 (versioned)", s=60, size=15)
fsx = ic("aws/storage/fsx-for-lustre", 675, 2135, "FSx for Lustre\nweights cache", s=60, size=15)

gl = card(530, 2275, 1940, 2430, "#D0D5DD", fill="#F7F8FA")
c.text(546, 2303, "GPU compute layer", 17, "start", weight=700, color=MUTED)
ic(LOGO("karpenter"), 640, 2355, "Karpenter\nGPU NodePools", s=50, size=14)
ic("aws/compute/ec2", 830, 2355, "p5 · H100\n(on-demand / CB)", s=50, size=14)
ic("aws/compute/ec2", 1010, 2355, "g6e · L40S\n(spot ok)", s=50, size=14)
ic(LOGO("nvidia"), 1200, 2355, "GPU Operator\ndriver · device plugin", s=50, size=14)
ic(LOGO("nvidia"), 1400, 2355, "DCGM exporter\nGPU metrics", s=50, size=14)
ic(LOGO("keda"), 1590, 2355, "KEDA\nqueue-depth scale", s=50, size=14)
ic("aws/network/elb-network-load-balancer", 1780, 2355, "EFA · NVMe\ninstance store", s=46, size=14)

# ================================================================== ROW C · Network account
net = c.box(2000, 1810, 2300, 2450, "solid", "Network account", tab="aws", size=18)
tgw = ic("aws/network/transit-gateway", 2235, 1960, "Transit Gateway", s=72, size=15)
dx = ic("aws/network/direct-connect", 2235, 2200, "Direct Connect\n2 × 10 Gbps", s=72, size=15)

# ================================================================== ROW C · On-prem
op = c.box(2340, 1810, 2880, 2450, "solid")
c.icon("generic/place/datacenter", 2340, 1810, 52)
c.text(2402, 1844, "On-prem DC · data residency", 19, "start", weight=600)
rke = card(2360, 1880, 2860, 2240, HYB, fill="#EEF8F7", dash="8 6")
c.text(2376, 1908, "RKE2 GPU cluster", 17, "start", weight=700, color=HYB)
ic(LOGO("agentgateway"), 2445, 1990, "agentgateway\n+ EPP", s=52, size=15)
ic(LOGO("vllm"), 2610, 1990, "vLLM pool\nllama-70b", s=52, size=15)
ic("aws/general/traditional-server", 2775, 1990, "H100 servers\n(DGX)", s=56, size=15)
c.text(2610, 2150, "dữ liệu restricted (PII, core banking)", 15, color=MUTED)
c.text(2610, 2176, "không rời DC · model weights mirror nội bộ", 15, color=MUTED)
apps = card(2360, 2275, 2860, 2430, "#D0D5DD", fill="#F7F8FA")
oapp = ic("aws/general/traditional-server", 2470, 2345, "Core banking apps\n(consumer)", s=50, size=14)
ic("k8s/network/svc", 2700, 2345, "On-prem MCP\n(core APIs)", s=50, size=14)

# ================================================================== arrows
c.arrow(cons.right(885), alb.left(885), width=3)                                    # 1
c.arrow(alb.right(885), pc.left(885), width=3)
TR1 = 1092
for key, y in (("a2a", YA), ("mcp", YM), ("llm", YL)):
    c.elbow(pc.right(885), lst[key].left(y), via_x=TR1, color=AGW)                  # 2

c.arrow(lst["a2a"].right(YA), agents.left(YA), color=AGW)                          # 5
TM = 1560
c.elbow(lst["mcp"].right(YM), mcps.left(862), via_x=TM, color=AGW)                  # 4
c.elbow(lst["mcp"].right(YM), rmcp.left(1010), via_x=TM, color=AGW)

TL = 1540                                                                           # 3 LLM routing
c.arrow(lst["llm"].right(YL), (TL + 16, YL), (TL + 16, 1300), prov.left(1300), color=AGW, dashed=True)
c.text(1880, 1290, "fallback · burst", 15, color=MUTED)
c.arrow(lst["llm"].right(YL), (TL - 16, YL), (TL - 16, igw.y1 - 2), color=GPU, width=3.5)
c.text(TL - 2, 1800, "default: hosted LLM", 15, "start", color=GPU, weight=600)
HY = 1775
c.arrow(lst["llm"].right(YL), (TL, YL), (TL, HY), (tgw.cx, HY), tgw.top(), color=HYB, width=3)
c.text(1870, HY - 10, "data-class=restricted → on-prem", 15, color=HYB, weight=600)

c.arrow(argo.right(argo.cy), (1008, argo.cy), color="ink")
c.arrow((1312, 310), ctl.left(310), color="ink")
c.arrow((1410, 372), dp.top(1410), color="ink", dashed=True)
c.text(1424, 436, "xDS", 15, "start", color=MUTED)

c.arrow(idp.top(960), pc.bottom(960), color=SEC, dashed=True)
c.text(972, 1400, "JWKS", 15, "start", color=SEC)
c.arrow(vlt.top(1180), dp.bottom(1180), color=SEC, dashed=True)
c.text(1192, 1400, "secretRef", 15, "start", color=SEC)
c.arrow(rl.top(1395), dp.bottom(1395), color=SEC, dashed=True)
c.arrow(pcl.bottom(1800), obs.top(1800), color=OTEL, width=3)                       # 6
c.text(1815, 1400, "OTel (Alloy)", 15, "start", color=OTEL)
c.arrow(obs.right(1625), aud.left(1625), color=OTEL)

# inside inference cluster
c.elbow(igw.left(1995), (pools.x2 + 2, PA), via_x=1440, color=GPU)                  # 7
c.elbow(igw.left(1995), (pools.x2 + 2, PB), via_x=1440, color=GPU)
c.arrow(store.right(2060), pools.left(2060), color="ink", dashed=True)
c.text(840, 2046, "load", 14, color=MUTED)
c.arrow((s3m.cx, 2072), (s3m.cx, fsx.y1 - 2), color="ink", dashed=True)

# hybrid path
c.arrow((tgw.cx, tgw.y2 + 48), (dx.cx, dx.y1 - 2), color=HYB, width=3)                       # 8
c.arrow(dx.right(2190), rke.left(2190), color=HYB, width=3)
c.arrow(oapp.left(oapp.cy), (2320, oapp.cy), (2320, 2215), dx.right(2215), color=HYB, dashed=True)

for x, y, n in [(470, 885, 1), (1092, 885, 2), (TL - 16, 1240, 3), (TM, 960, 4), (1536, YA, 5), (1800, 1350, 6),
                (1440, 2075, 7), (2235, 1775, 8)]:
    marker(x, y, n)

# ================================================================== legend
steps = ["Consumer AWS + on-prem gọi một endpoint duy nhất qua internal ALB",
         "Policy chain: AuthN, CEL RBAC, quota token, guardrail + gắn data-class",
         "LLM: mặc định hosted LLM; restricted → on-prem; Bedrock/SaaS làm fallback",
         "MCP: gộp tool nội bộ + SaaS sau /mcp, phân quyền theo tool",
         "A2A: agent gọi agent qua gateway, có authz và audit",
         "OTel → LGTM: token, TTFT, GPU util, cost theo team/model; audit lưu S3 WORM",
         "Inference gateway + EPP chọn replica vLLM theo KV-cache/queue; KEDA scale pod, Karpenter thêm GPU node",
         "Hybrid: TGW → Direct Connect → cụm GPU on-prem; core banking apps gọi ngược lên AI gateway"]
for i, s in enumerate(steps):
    x = 40 + (i // 4) * 1440
    y = 2522 + (i % 4) * 44
    marker(x + 16, y - 6, i + 1)
    c.text(x + 46, y, s, 18, "start")

c.save(sys.argv[1] if len(sys.argv) > 1 else "ai_gateway_v2")
print("ok")
