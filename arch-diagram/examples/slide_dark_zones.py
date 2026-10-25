"""Hybrid migration — 3 zones (On-prem · Private connectivity · AWS landing zone), dark theme.
Layout measured from the reference image (canvas 2590 wide); icons added on each card.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from archdiag import Canvas, logo  # noqa: E402

W, H = 2590, 1072
c = Canvas(W, H, bg="#141A3A")
A = c.under.append
FONT = "Inter, DejaVu Sans, sans-serif"
MONO = "JetBrains Mono, DejaVu Sans Mono, monospace"

WHITE, BODY, MUTE = "#F2F4F8", "#A7B1C7", "#8C95AB"
TEAL, TEAL_D = "#6FD0E0", "#3E9FB3"


def t(x, y, s, size, color, font=FONT, weight=400, ls=0, anchor="start", opacity=1):
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    A(f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" fill="{color}" '
      f'letter-spacing="{ls}" text-anchor="{anchor}" opacity="{opacity}">{s}</text>')


# ------------------------------------------------------------------ background + grid
A('<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
  '<stop offset="0" stop-color="#18224A"/><stop offset=".55" stop-color="#141638"/>'
  '<stop offset="1" stop-color="#1A1440"/></linearGradient></defs>')
A(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
for x in range(0, W, 65):
    A(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#5A78C8" stroke-opacity=".10" stroke-width="1"/>')
for y in range(0, H, 65):
    A(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#5A78C8" stroke-opacity=".10" stroke-width="1"/>')

# ------------------------------------------------------------------ content
ZONES = [
    dict(x1=28, x2=803, num="01", tag="ON-PREM", accent=MUTE, border="#8C95AB", dash=True, solid=False,
         title="Data center hiện tại",
         desc=["Những gì đang chạy hôm nay, cùng những",
               "workload sẽ ở lại vì lý do pháp lý hoặc độ trễ."],
         items=[("VMware vSphere", "VM · vSAN", [("generic/virtualization/vmware", True)]),
                ("Proxmox · bare metal", "RKE2 Kubernetes", [("onprem/proxmox/pve", True), ("k8s/infra/master", False)]),
                ("Oracle · SQL Server", "database hiện tại", [("onprem/database/oracle", True), ("onprem/database/mssql", True)]),
                ("HSM · core banking", "giữ lại on-prem", [("onprem/compute/server", True)])]),
    dict(x1=878, x2=1651, num="02", tag="KẾT NỐI", accent=TEAL, border=TEAL_D, dash=True, solid=False,
         title="Kết nối riêng, có dự phòng",
         desc=["Không đi qua internet công cộng. DNS",
               "phân giải hai chiều, route rõ ràng cho từng",
               "môi trường."],
         items=[("Direct Connect", "10 Gbps · 2 locations", [("aws/network/direct-connect", False)]),
                ("Site-to-site VPN", "đường dự phòng", [("aws/network/site-to-site-vpn", False)]),
                ("Transit Gateway", "route theo account", [("aws/network/transit-gateway", False)]),
                ("Route 53 Resolver", "DNS hai chiều", [("aws/network/route-53", False)])]),
    dict(x1=1726, x2=2499, num="03", tag="AWS", accent=TEAL, border=TEAL_D, dash=False, solid=True,
         title="Landing zone",
         desc=["Multi-account dựng bằng Terraform, guardrail",
               "và logging bật sẵn trước khi workload đầu tiên",
               "chuyển sang."],
         items=[("Control Tower", "multi-account · SCP", [("aws/management/control-tower", False)]),
                ("EKS · RDS · S3", "đích của workload", [("aws/compute/elastic-kubernetes-service", False),
                                                          ("aws/database/rds", False),
                                                          ("aws/storage/simple-storage-service-s3", False)]),
                ("IAM Identity Center", "một identity cho hai phía", [("aws/security/single-sign-on", False)]),
                ("Security Hub · GuardDuty", "giám sát từ ngày đầu", [("aws/security/security-hub", False),
                                                                       ("aws/security/guardduty", False)])]),
]
ZY1, ZY2 = 32, 1036
CARD_TOPS, CARD_H = [461, 597, 733, 869], 117

zrects = []
for z in ZONES:
    x1, x2 = z["x1"], z["x2"]
    dash = ' stroke-dasharray="7 7"' if z["dash"] else ""
    sw = 2.5 if z["solid"] else 2
    op = ".85" if z["solid"] else ".6"
    A(f'<rect x="{x1}" y="{ZY1}" width="{x2 - x1}" height="{ZY2 - ZY1}" rx="46" fill="#FFFFFF" fill-opacity=".025" '
      f'stroke="{z["border"]}" stroke-opacity="{op}" stroke-width="{sw}"{dash}/>')
    zrects.append(c.box(x1, ZY1, x2, ZY2, "none"))
    cx1, cx2 = x1 + 52, x2 - 52

    t(cx1, 112, f"ZONE {z['num']}", 24, z["accent"], MONO, 600, ls=6)
    pw = 30 + len(z["tag"]) * 15.5
    A(f'<rect x="{cx2 - pw}" y="83" width="{pw}" height="41" rx="20.5" fill="none" stroke="#FFFFFF" '
      f'stroke-opacity=".28" stroke-width="1.6"/>')
    t(cx2 - pw / 2 + 2, 110, z["tag"], 18, z["accent"] if z["accent"] == TEAL else "#C9D2E3", MONO, 600, ls=3,
      anchor="middle")
    t(cx1, 205, z["title"], 46, WHITE, weight=400, ls=-0.8)
    for i, ln in enumerate(z["desc"]):
        t(cx1, 282 + i * 51, ln, 29.5, BODY, weight=400, ls=-0.4)
    A(f'<line x1="{cx1}" y1="427" x2="{cx2}" y2="427" stroke="#FFFFFF" stroke-opacity=".22" stroke-width="1.5" '
      f'stroke-dasharray="6 6"/>')

    for k, (title, sub, icons) in enumerate(z["items"]):
        y = CARD_TOPS[k]
        A(f'<rect x="{cx1}" y="{y}" width="{cx2 - cx1}" height="{CARD_H}" rx="16" fill="#FFFFFF" fill-opacity=".045" '
          f'stroke="#FFFFFF" stroke-opacity=".10" stroke-width="1.5"/>')
        t(cx1 + 27, y + 65, f"{k + 1:02d}", 22, z["accent"], MONO, 500)
        t(cx1 + 88, y + 54, title, 30, WHITE, weight=400, ls=-0.5)
        t(cx1 + 88, y + 88, sub, 21, MUTE, MONO, 500, ls=1.5)
        # icons, right-aligned, vertically centred
        s = 60 if len(icons) == 1 else 50
        gap = 12
        x = cx2 - 26 - s
        for name, tile in reversed(icons):
            iy = y + (CARD_H - s) / 2
            if tile:   # light tile so dark-coloured logos stay legible on the navy background
                A(f'<rect x="{x}" y="{iy}" width="{s}" height="{s}" rx="{s * .22}" fill="#F2F4F8" fill-opacity=".95"/>')
                c.icon(name, x + s * .12, iy + s * .12, s * .76)
            else:
                c.icon(name, x, iy, s)
            x -= s + gap

# ------------------------------------------------------------------ zone connectors (⇄ at row-1 height)
YC = CARD_TOPS[0] + CARD_H / 2 + 16
for a, b in [(zrects[0], zrects[1]), (zrects[1], zrects[2])]:
    c.arrow(a.right(YC - 8, gap=6), b.left(YC - 8, gap=6), color=TEAL, width=2.5)
    c.arrow(b.left(YC + 8, gap=6), a.right(YC + 8, gap=6), color=TEAL, width=2.5)

c.save(sys.argv[1] if len(sys.argv) > 1 else "hybrid_zones")
print("ok")
