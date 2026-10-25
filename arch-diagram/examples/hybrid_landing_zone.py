"""Hybrid landing zone — AWS architecture style.
Components parsed from the 3-zone slide: on-prem DC · private connectivity (DX x2, S2S VPN, TGW, R53 Resolver)
· Control Tower landing zone (multi-account, SCP, Identity Center, Security Hub, GuardDuty, EKS/RDS/S3).
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from archdiag import Canvas, logo  # noqa: E402

c = Canvas(2900, 1760)
MUTED, SOFT = "#3A4450", "#5A6B86"
DNS_C = "#7B42BC"


def ic(name, cx, cy, label=None, s=80, size=19):
    return c.icon(name, cx - s / 2, cy - s / 2, s, label=label, size=size)


def note(x, y, s, size=16, anchor="middle", color=SOFT, **kw):
    c.text(x, y, s, size, anchor, color=color, **kw)


# ================================================================== on-prem data center
dc = c.box(40, 110, 760, 1600, "solid")
c.icon("generic/place/datacenter", 40, 110, 60)
c.text(116, 147, "Corporate data center (on-prem)", 21, "start", weight=600)

vs = c.box(70, 200, 540, 400, "grey", "VMware vSphere", label_pos="top-left", size=19)
ic("generic/virtualization/vmware", 180, 300, "VM workloads", s=90, size=17)
ic("generic/storage/storage", 420, 300, "vSAN", s=64, size=17)

px = c.box(70, 430, 540, 650, "grey", "Proxmox · bare metal", label_pos="top-left", size=19)
ic("onprem/proxmox/pve", 180, 545, "Proxmox VE", s=76, size=17)
ic("k8s/infra/master", 420, 545, "RKE2\nKubernetes", s=76, size=17)

dbs = c.box(70, 680, 540, 900, "grey", "Databases hiện tại", label_pos="top-left", size=19)
ic("onprem/database/oracle", 180, 795, "Oracle", s=76, size=17)
ic("onprem/database/mssql", 420, 795, "SQL Server", s=76, size=17)

stay = c.box(70, 940, 540, 1170, "dotted", "Giữ lại on-prem (pháp lý · độ trễ)", label_pos="top-left", size=18)
ic("aws/general/traditional-server", 180, 1060, "HSM", s=76, size=17)
ic("aws/general/traditional-server", 420, 1060, "Core banking", s=76, size=17)

dns = ic("aws/general/traditional-server", 305, 1330, "On-prem DNS", s=76, size=17)
rtr = ic("aws/network/vpc-customer-gateway", 655, 460, "Edge router\n(CGW · BGP)", s=80, size=17)

# ================================================================== Direct Connect locations
dxl = c.box(815, 240, 1065, 700, "dashed", "Direct Connect\nlocations", size=18)
dx1 = ic("aws/network/direct-connect", 940, 380, "DX location 1\n10 Gbps", s=76, size=17)
dx2 = ic("aws/network/direct-connect", 940, 570, "DX location 2\n10 Gbps", s=76, size=17)

# ================================================================== AWS
c.box(1100, 40, 2870, 1700, "solid", "AWS Cloud", tab="aws")
c.box(1125, 110, 2850, 1675, "dashed", "Region · ap-southeast-1", label_pos="top-left", size=18)
org = c.box(1150, 160, 2830, 1650, "solid")
c.icon("aws/management/organizations", 1162, 168, 44)
c.text(1216, 198, "AWS Organizations · Control Tower landing zone (dựng bằng Terraform)", 20, "start", weight=600)

# ---- Network account
net = c.box(1170, 240, 1700, 1630, "solid", "Network account", tab="aws", size=19)
dxgw = ic("aws/network/direct-connect", 1300, 470, "Direct Connect\nGateway", s=76, size=17)
vpn = ic("aws/network/site-to-site-vpn", 1300, 760, "S2S VPN\n(dự phòng)", s=76, size=17)
tgw = ic("aws/network/transit-gateway", 1560, 640, "Transit Gateway", s=80, size=18)
note(1560, 738, "route table theo account:\nprod · non-prod · shared", 15, lh=19)
svc = c.box(1190, 1120, 1680, 1610, "dashed", "Shared services VPC", label_pos="top-left", size=18)
r53 = ic("aws/network/route-53", 1435, 1330, "Route 53 Resolver\ninbound · outbound", s=80, size=17)
note(1435, 1480, "forwarding rules (RAM-shared)", 15)

# ---- Management account
mg = c.box(1740, 240, 2250, 610, "solid", "Management account", tab="aws", size=19)
ct = ic("aws/management/control-tower", 1850, 400, "Control Tower", s=76, size=17)
ic("aws/management/organizations", 1995, 400, "Organizations\nSCP", s=76, size=17)
ic("aws/security/single-sign-on", 2140, 400, "IAM Identity\nCenter", s=76, size=17)
note(1995, 585, "một identity cho cả on-prem và AWS", 15)

# ---- Security / Log archive
sa = c.box(2290, 240, 2810, 610, "solid", "Security (Audit) account", tab="aws", size=19)
ic("aws/security/security-hub", 2440, 400, "Security Hub", s=76, size=17)
ic("aws/security/guardduty", 2660, 400, "GuardDuty", s=76, size=17)
note(2550, 585, "delegated admin · bật từ ngày đầu", 15)

la = c.box(2290, 650, 2810, 1000, "solid", "Log Archive account", tab="aws", size=19)
ic("aws/management/cloudtrail", 2400, 810, "CloudTrail\norg trail", s=72, size=17)
ic("aws/management/config", 2550, 810, "AWS Config", s=72, size=17)
logs3 = ic("aws/storage/simple-storage-service-s3", 2700, 810, "S3 log\nbucket", s=72, size=17)

aft = c.box(1740, 650, 2250, 1000, "grey")
c.icon("@terraform", 1762, 668, 40)
c.text(1812, 696, "Terraform · Account Factory (AFT)", 18, "start", weight=600, color=MUTED)
note(1995, 760, "account vending · baseline:", 16, color=MUTED)
note(1995, 788, "VPC + TGW attach · SCP · logging", 16, color=MUTED)
note(1995, 816, "· GuardDuty / Security Hub enrol", 16, color=MUTED)

# ---- Workload accounts
def workload(y1, y2, name):
    b = c.box(1740, y1, 2810, y2, "solid", name, tab="aws", size=19)
    v = c.box(1760, y1 + 72, 2790, y2 - 16, "dashed", "Workload VPC (TGW attach)", label_pos="top-left", size=17)
    cy = y1 + 150
    ic("aws/compute/elastic-kubernetes-service", 2080, cy, "Amazon EKS", s=72, size=17)
    ic("aws/database/rds", 2335, cy, "Amazon RDS", s=72, size=17)
    ic("aws/storage/simple-storage-service-s3", 2590, cy, "Amazon S3", s=72, size=17)
    return b

wp = workload(1060, 1320, "Workload · Prod")
wn = workload(1360, 1630, "Workload · Non-prod")

# ================================================================== arrows
# primary path: DC router -> 2 DX locations -> DX Gateway -> TGW
c.elbow(rtr.right(rtr.cy), dx1.left(dx1.cy), via_x=780, color="ink", width=3)
c.elbow(rtr.right(rtr.cy), dx2.left(dx2.cy), via_x=780, color="ink", width=3)
c.elbow(dx1.right(dx1.cy), dxgw.left(dxgw.cy), via_x=1215, color="ink", width=3)
c.elbow(dx2.right(dx2.cy), dxgw.left(dxgw.cy), via_x=1215, color="ink", width=3)
c.elbow(dxgw.right(dxgw.cy), tgw.left(625), via_x=1440, color="ink", width=3)
c.text(940, 228, "transit VIF · 2 × 10 Gbps", 15, color=MUTED)

# backup: S2S VPN over internet
c.arrow((rtr.cx, 562), (rtr.cx, vpn.cy), vpn.left(vpn.cy), color="accent", dashed=True)
c.text(940, vpn.cy - 12, "IPsec qua internet (backup)", 15, color="#3B8FD9")
c.elbow(vpn.right(vpn.cy), tgw.left(660), via_x=1440, color="accent", dashed=True)

# TGW -> workloads (shared trunk) and -> shared services VPC
TR = 1720
c.elbow(tgw.right(tgw.cy), wp.left(wp.cy), via_x=TR, color="ink")
c.elbow(tgw.right(tgw.cy), wn.left(wn.cy), via_x=TR, color="ink")
c.arrow((tgw.cx, 780), svc.top(tgw.cx), color="ink")

# DNS both ways
c.arrow(dns.right(1310), r53.left(1310), color=DNS_C)
c.arrow(r53.left(1350), dns.right(1350), color=DNS_C)
c.text(940, 1298, "DNS hai chiều (conditional forwarding)", 15, color=DNS_C)

# governance
c.arrow(mg.bottom(1995), aft.top(1995), color="ink", dashed=True)
c.arrow(aft.bottom(1995), wp.top(1995), color="ink", dashed=True)
c.text(2010, 1036, "vend + SCP guardrails", 15, "start", color=MUTED)
c.arrow(wp.top(2550), la.bottom(2550), color="ink", dashed=True)
c.text(2565, 1036, "logs → Log Archive", 15, "start", color=MUTED)

c.save(sys.argv[1] if len(sys.argv) > 1 else "hybrid_aws")
print("ok")
