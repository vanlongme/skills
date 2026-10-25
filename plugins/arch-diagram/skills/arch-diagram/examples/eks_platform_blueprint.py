"""EKS Platform cluster blueprint v3 — Network / Platform / Observability accounts.

v3: jenkins-agents namespace, Nexus Firewall, GitLab installed by Terraform (others by Argo CD),
agentgateway, Trivy Operator DB mirrored in ECR, EKS control plane + bastion access to the private API.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from archdiag import Canvas, logo  # noqa: E402

LOGO = logo

c = Canvas(4480, 2820)
ORANGE, VAULT, TELE = "#E07B00", "#3B8FD9", "#D9480F"
PUB_FILL, PUB_LINE = "#EEF6EA", "#7AA116"
PRV_FILL, PRV_LINE = "#EAF2FB", "#147EBA"
MUTED, SOFT = "#3A4450", "#5A6B86"
TF_PURPLE, ARGO = "#7B42BC", "#EF7B4D"


# ------------------------------------------------------------------ helpers
def marker(x, y, n):
    c.over.append(f'<circle cx="{x}" cy="{y}" r="16" fill="{ORANGE}" stroke="white" stroke-width="3"/>')
    c.over.append(f'<text x="{x}" y="{y + 6.5}" font-family="{c.t["font"]}" font-size="18" font-weight="700" '
                  f'fill="white" text-anchor="middle">{n}</text>')


def tier(x1, y1, x2, y2, public, label, lx=None):
    fill, line = (PUB_FILL, PUB_LINE) if public else (PRV_FILL, PRV_LINE)
    c.under.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="4" fill="{fill}" '
                   f'stroke="{line}" stroke-width="2"/>')
    lx = lx or x1 + 14
    c.under.append(f'<rect x="{lx}" y="{y1 + 12}" width="16" height="16" rx="2" fill="{line}"/>')
    c.text(lx + 26, y1 + 27, label, 19, "start", weight=600, color=line)
    return c.box(x1, y1, x2, y2, "none")


def tab_label(x, y, txt, w):
    c.under.append(f'<rect x="{x - 8}" y="{y - 19}" width="{w}" height="26" fill="white"/>')
    c.text(x, y, txt, 18, "start", weight=600, color=MUTED)


def ns(x1, x2, name, owner):
    r = c.box(x1, 750, x2, 1220, "dashed", f"ns: {name}", label_pos="top-left", size=18)
    col, txt = (TF_PURPLE, "Terraform") if owner == "tf" else (ARGO, "Argo CD")
    w = 112 if owner == "tf" else 96
    cx = (x1 + x2) / 2
    c.under.append(f'<rect x="{cx - w / 2}" y="1180" width="{w}" height="26" rx="13" fill="{col}"/>')
    c.text(cx, 1199, txt, 15, weight=700, color="white")
    return r


def ic(name, cx, y, label=None, s=85, size=20):
    return c.icon(name, cx - s / 2, y, s, label=label, size=size)


def placeholder(cx, y, s, txt, label, size=20):
    x = cx - s / 2
    c.under.append(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * .18}" fill="white" '
                   f'stroke="#8A94A6" stroke-width="2.5" stroke-dasharray="6 5"/>')
    c.text(cx, y + s / 2 + 7, txt, 20, weight=700, color=SOFT)
    c.text(cx, y + s + 33, label, size, lh=size * 1.26)


def pill(x1, x2, y, name, kind="Interface"):
    col = PUB_LINE if kind == "Gateway" else "#8C4FFF"
    c.under.append(f'<rect x="{x1}" y="{y}" width="{x2 - x1}" height="34" rx="17" fill="white" stroke="{col}" stroke-width="2"/>')
    c.icon("aws/network/endpoint", x1 + 6, y + 4, 26)
    c.under.append(f'<text x="{x1 + 42}" y="{y + 23}" font-family="DejaVu Sans Mono, monospace" font-size="18" '
                   f'fill="{c.t["ink"]}">{name}</text>')
    c.text(x2 - 14, y + 23, kind, 15, "end", color=SOFT)
    return y + 17


R1, R2 = 805, 975
Y, Y2 = R1 + 42, R2 + 42
UY = 432

# ================================================================== frames
users = c.icon("onprem/client/users", 30, UY - 46, 92, label="Corporate\nusers", size=20)
c.box(200, 30, 4450, 2530, "solid", "AWS Cloud", tab="aws")
c.box(230, 100, 4420, 2500, "dashed", "Region · ap-southeast-1", label_pos="top-left", size=19)
net = c.box(260, 150, 860, 2470, "solid", "Network account", tab="aws")
pa = c.box(900, 150, 3740, 2470, "solid", "Platform account · EKS platform cluster", tab="aws")
oa = c.box(3780, 150, 4410, 2470, "solid", "Observability account", tab="aws")

# ================================================================== network account
dx = ic("aws/network/direct-connect", 400, UY - 40, "Direct Connect\n(DXGW)", s=80, size=17)
vpn = ic("aws/network/site-to-site-vpn", 400, 560, "S2S VPN\n(backup)", s=80, size=17)
tgw = ic("aws/network/transit-gateway", 720, UY - 40, s=80)
c.text(720, UY - 52, "Transit Gateway", 18, weight=600)

ev = c.box(290, 900, 830, 1520, "solid")
c.icon("aws/network/vpc", 304, 908, 34)
c.text(346, 932, "Endpoint VPC 10.100.0.0/22", 18, "start", weight=600)
PX = (310, 810)
names = ["secretsmanager", "sts", "ec2", "autoscaling", "ecr.api", "ecr.dkr",
         "elasticloadbalancing", "sqs", "eks", "logs", "ssm", "kms"]
pys = {n: pill(*PX, 950 + i * 44, n) for i, n in enumerate(names)}
c.text(560, 1506, "SG 443 from 10.0.0.0/8 · DNS via PHZ", 15, color=SOFT)

r53 = c.box(290, 1570, 830, 1860, "grey")
c.text(306, 1598, "Route 53 (centralized DNS)", 18, "start", weight=600, color=MUTED)
ic("aws/network/route-53-hosted-zone", 430, 1625, "Private hosted zones\n(endpoint records)", s=75, size=16)
ic("aws/network/route-53", 690, 1625, "Resolver rules\n(RAM-shared)", s=75, size=16)
c.text(560, 1940, "TGW route tables:", 16, color=SOFT, weight=600)
c.text(560, 1966, "on-prem ⇄ platform 10.0.0.0/16", 16, color=SOFT)
c.text(560, 1990, "platform → endpoints 10.100.0.0/22", 16, color=SOFT)
c.text(560, 2014, "platform → observability 10.20.0.0/16", 16, color=SOFT)

# ================================================================== platform account: regional services
rs = c.box(930, 230, 1160, 2440, "dashed")
c.text(1045, 258, "Regional services", 16, weight=600, color=MUTED)
RX = 1045
acm = ic("aws/security/certificate-manager", RX, 272, "ACM", s=80, size=17)

# ================================================================== platform VPC
VR = 3370
vpc = c.box(1190, 220, VR, 2440, "solid")
c.icon("aws/network/vpc", 1206, 226, 36)
c.text(1252, 252, "Platform VPC 10.0.0.0/16 · 3 AZ (a / b / c)", 20, "start", weight=600)

tier(1210, 330, 1900, 540, False, "Private ingress · 10.0.4.0/22", lx=1480)
alb = ic("aws/network/elb-application-load-balancer", 1415, UY - 42)
c.text(1470, UY + 2, "Internal ALB", 19, "start", weight=600)
c.text(1470, UY + 26, "Gateway API · TLS ACM", 16, "start", color=SOFT)

tier(1940, 330, 2700, 540, True, "Public · 10.0.0.0/22 (egress only)")
nat = ic("aws/network/nat-gateway", 2470, 392, "NAT Gateway", s=80, size=17)
igw = ic("aws/network/internet-gateway", 2620, 392, "IGW", s=80, size=17)

mg = tier(2740, 330, 3350, 540, False, "Private mgmt · 10.0.8.0/24")
tf = ic("@terraform", 2880, 388, "Terraform\nhelm_release", s=70, size=16)
bast = ic("aws/compute/ec2-instance", 3170, UY - 40, s=80)
c.text(3170, UY + 62, "Bastion (SSM)", 17, weight=600)
c.text(3170, UY + 84, "kubectl · terraform", 15, color=SOFT)

tier(1210, 580, 3350, 2140, False, "Private app subnets · 10.0.32.0/19 × 3 AZ", lx=1480)
eks = c.box(1230, 620, 3330, 2120, "solid")
c.icon("aws/compute/elastic-kubernetes-service", 1480, 632, 40)
c.text(1530, 660, "Amazon EKS · Platform cluster (DevSecOps tools only, no app workloads)", 20, "start", weight=600)

gw = ns(1330, 1500, "gateway", "argo")
ic(LOGO("gateway-api"), 1415, R1, "Gateway API\nHTTPRoute", size=18)
ic(LOGO("agentgateway"), 1415, R2, "agentgateway\nMCP · A2A", s=72, size=18)

gl = ns(1550, 1770, "gitlab", "tf")
ic("onprem/vcs/gitlab", 1660, R1, "GitLab\n(Helm chart)")
ic("onprem/vcs/gitlab", 1660, R2, "GitOps repo\n(platform)", s=72)

jk = ns(1820, 2020, "jenkins", "argo")
ic("onprem/ci/jenkins", 1920, R1, "Jenkins\ncontroller")
c.text(1920, 1092, "JCasC ·\nK8s plugin", 17, color=MUTED, lh=22)

ag = ns(2070, 2290, "jenkins-agents", "argo")
ic("k8s/compute/pod", 2180, R1, "Agent pods\n(ephemeral)")
ic(LOGO("cosign"), 2180, R2, "cosign · syft\nsign · SBOM", s=80)

sec = ns(2340, 2760, "security-scan", "argo")
ic("saas/security/sonarqube", 2410, R1, "SonarQube\nSAST · gate")
ic(LOGO("coverity"), 2550, R1, "Coverity\nSAST", s=80)
ic(LOGO("blackduck"), 2690, R1, "Black Duck\nSCA", s=80)
ic("onprem/security/trivy", 2480, R2, "Trivy\nimage · IaC")
placeholder(2620, R2, 85, "IAST", "Seeker\nIAST")

nx = ns(2810, 3030, "nexus", "argo")
ic(LOGO("sonatype"), 2920, R1, "Nexus Repo\nartifacts · OCI")
ic(LOGO("sonatype"), 2920, R2, "Nexus Firewall\nquarantine OSS", s=72)

ar = ns(3080, 3280, "argocd", "tf")
ic("onprem/gitops/argocd", 3180, R1, "Argo CD\napp-of-apps")
c.text(3180, R2 + 40, "manages every\nns except gitlab", 17, color=MUTED, lh=22)

# ---------------- platform services
c.box(1330, 1270, 3280, 1505, "dashed")
tab_label(1346, 1277, "Platform services (cluster-wide) · Argo CD-managed", 470)
vt = c.box(1350, 1300, 2020, 1490, "grey")
ic("onprem/security/vault", 1450, 1325, "Vault\nKMS auto-unseal", s=78, size=18)
ic("k8s/compute/deploy", 1645, 1328, "External Secrets\nVault · Secrets Mgr", s=72, size=18)
ic("k8s/compute/deploy", 1870, 1328, "AWS LB\nController", s=72, size=18)
sp = c.box(2070, 1300, 2760, 1490, "grey")
ic(LOGO("kyverno"), 2180, 1325, "Kyverno\nverifyImages", s=75, size=18)
ic(LOGO("tetragon"), 2415, 1328, "Tetragon\neBPF", s=70, size=18)
tro = ic("onprem/security/trivy", 2650, 1328, "Trivy Operator\nDB mirror: ECR", s=70, size=18)
tel = c.box(2810, 1300, 3280, 1490, "grey")
ic(LOGO("alloy"), 2935, 1325, "Grafana Alloy\n(DaemonSet)", s=75, size=18)
ic("k8s/compute/deploy", 3160, 1328, "kube-state-\nmetrics", s=70, size=18)

# ---------------- pod networking
c.box(1330, 1555, 3280, 1765, "dashed")
tab_label(1346, 1562, "Pod networking — CNI chaining (DaemonSets)", 420)
c.box(1350, 1585, 3260, 1750, "grey")
vcni = ic("aws/network/vpc-elastic-network-interface", 1550, 1610, "Amazon VPC CNI\n(aws-node) · IPAM", s=75, size=18)
cil = ic(LOGO("cilium"), 1930, 1610, "Cilium · chaining mode\nNetworkPolicy · Hubble", s=75, size=18)
for i, s in enumerate(["cni.chainingMode: aws-cni · routingMode: native",
                       "enableIPv4Masquerade: false · pod IP = VPC IP",
                       "Hubble flows → Alloy → Loki"]):
    c.under.append(f'<text x="2180" y="{1640 + i * 30}" font-family="DejaVu Sans Mono, monospace" font-size="16" '
                   f'fill="{MUTED}">{s}</text>')

# ---------------- compute layer
c.box(1330, 1815, 3280, 2105, "dashed")
tab_label(1346, 1822, "Compute layer — node groups across 3 AZ · Bottlerocket OS", 560)
mng = c.box(1350, 1845, 2020, 2090, "grey")
c.text(1366, 1874, "System MNG · amiType BOTTLEROCKET_x86_64", 17, "start", weight=600, color=MUTED)
ca = ic("k8s/compute/deploy", 1460, 1900, "Cluster\nAutoscaler", s=72, size=17)
asg = ic("aws/compute/ec2-auto-scaling", 1710, 1900, "ASG m7i.xlarge\nmin 3 · max 6", s=72, size=17)
ic("aws/compute/ec2", 1920, 1900, "Bottlerocket\n1 per AZ", s=72, size=17)
c.text(1685, 2078, "taint CriticalAddonsOnly · Karpenter, CoreDNS, Vault, LBC", 15, color=SOFT)

kp = c.box(2070, 1845, 3260, 2090, "grey")
c.text(2086, 1874, "Karpenter-managed capacity", 17, "start", weight=600, color=MUTED)
kc = ic(LOGO("karpenter"), 2170, 1905, "Karpenter", s=72, size=17)
pools = c.box(2270, 1885, 3245, 2055, "dotted")
c.text(2282, 1907, "NodePools", 16, "start", weight=600, color=MUTED)
ic("aws/compute/ec2", 2440, 1915, "ci-agents · spot c7i", s=62, size=16)
ic("aws/compute/ec2", 2760, 1915, "scanners · r7i", s=62, size=16)
ic("aws/compute/ec2", 3080, 1915, "tools · m7i", s=62, size=16)
c.text(2665, 2078, "EC2NodeClass amiFamily: Bottlerocket · gp3 · IMDSv2", 15, color=SOFT)

# ================================================================== private data tier
dt = tier(1210, 2180, 3350, 2410, False, "Private data subnets · 10.0.64.0/22 × 3 AZ", lx=1480)
s3gw = ic("aws/network/endpoint", 1300, 2258, "S3 Gateway\nendpoint", s=64, size=16)
ic("aws/database/rds-postgresql-instance", 1700, 2240, "RDS PostgreSQL\nprimary", s=72, size=17)
ic("aws/database/rds-postgresql-instance", 1880, 2240, "standby\nMulti-AZ", s=72, size=17)
efs = ic("aws/storage/elastic-file-system-efs", 2400, 2240, "EFS mount targets\nJenkins home (RWX)", s=72, size=17)

# regional services aligned to their arrows
sm = ic("aws/security/secrets-manager", RX, pys["secretsmanager"] - 40, "Secrets\nManager", s=80, size=17)
ecr = ic("aws/compute/ec2-container-registry", RX, pys["ecr.dkr"] - 40, "ECR\ntrivy-db mirror", s=80, size=17)
kms = ic("aws/security/key-management-service", RX, pys["kms"] - 40, "KMS\nVault · EBS · etcd", s=80, size=17)
EBS_Y = 1960
ebs = ic("aws/storage/elastic-block-store-ebs", RX, EBS_Y - 40, "EBS gp3\n(EBS CSI)", s=80, size=17)
S3_Y = s3gw.cy
s3 = ic("aws/storage/simple-storage-service-s3", RX, S3_Y - 40, "S3\nNexus · GitLab", s=80, size=17)

# ================================================================== EKS control plane (AWS-managed)
cp = c.box(3410, 330, 3710, 1240, "solid", "EKS control plane\n(AWS-managed VPC)", tab="aws", size=18)
api = ic("k8s/controlplane/api", 3560, 480, "kube-apiserver\nprivate endpoint", s=80, size=17)
ic("k8s/infra/etcd", 3560, 680, "etcd\n(KMS envelope)", s=80, size=17)
ic("k8s/controlplane/c-m", 3560, 880, "controller-mgr\n· scheduler", s=80, size=17)
c.text(3560, 1110, "endpointPublicAccess: false", 15, color=SOFT)
c.text(3560, 1134, "endpointPrivateAccess: true", 15, color=SOFT)

# ================================================================== observability account (x + 600 vs v2)
OX = 600
ovpc = c.box(3210 + OX, 220, 3780 + OX, 2000, "solid")
c.icon("aws/network/vpc", 3224 + OX, 226, 34)
c.text(3266 + OX, 252, "Observability VPC 10.20.0.0/16", 18, "start", weight=600)
oeks = c.box(3230 + OX, 640, 3760 + OX, 1960, "solid")
c.icon("aws/compute/elastic-kubernetes-service", 3244 + OX, 650, 36)
c.text(3288 + OX, 676, "EKS · LGTM cluster", 18, "start", weight=600)
graf = ic("onprem/monitoring/grafana", 3620 + OX, 700, "Grafana\ndashboards · alerts", s=80, size=17)
TEL_Y = tel.cy
nlb = ic("aws/network/elb-network-load-balancer", 3320 + OX, TEL_Y - 40, "Internal NLB\ningest", s=80, size=17)
c.text(3320 + OX, TEL_Y - 80, "metrics · logs\n· traces", 16, color=TELE, weight=600, lh=20)
be = c.box(3480 + OX, 960, 3750 + OX, 1820, "grey")
c.text(3615 + OX, 988, "LGTM backends", 17, weight=600, color=MUTED)
mim = ic("onprem/monitoring/mimir", 3640 + OX, 1060, "Mimir\nmetrics", s=80, size=17)
lok = ic("onprem/logging/loki", 3640 + OX, TEL_Y - 40, "Loki\nlogs", s=80, size=17)
tmp = ic("onprem/tracing/tempo", 3640 + OX, 1600, "Tempo\ntraces", s=80, size=17)
os3 = ic("aws/storage/simple-storage-service-s3", 3620 + OX, 2090, "S3 · LGTM\nobject storage", s=80, size=17)

# ================================================================== arrows
c.arrow(users.right(UY), dx.left(UY))
c.arrow((users.x2, 470), (320, 470), (320, vpn.cy), vpn.left(vpn.cy), color="accent", dashed=True)
c.arrow(dx.right(UY), tgw.left(UY))
c.arrow(vpn.right(vpn.cy), (690, vpn.cy), (690, tgw.y2 + 2))
c.arrow(tgw.right(UY), alb.left(UY))
c.text(RX, UY - 12, "route 10.0.0.0/16", 15, color=MUTED)
c.arrow((alb.cx, alb.y2 + 2), gw.top(alb.cx))
c.arrow((acm.x2 + 2, acm.cy), (alb.cx, acm.cy), (alb.cx, alb.y1 - 2), color="ink", dashed=True)

c.arrow((tgw.cx, tgw.y2 + 2), ev.top(tgw.cx), color="ink")
EY = 800
c.arrow(eks.left(EY), (750, EY), (750, tgw.y2 + 2), color="ink")
c.text(RX, EY - 10, "AWS APIs via TGW", 15, color=MUTED)
for n, tgt in [("secretsmanager", sm), ("ecr.dkr", ecr), ("kms", kms)]:
    c.arrow(ev.right(pys[n]), tgt.left(pys[n]), color="ink")
c.arrow(r53.right(1720), vpc.left(1720), color="ink", dashed=True)
c.text(RX, 1710, "PHZ association", 15, color=MUTED)

c.arrow(eks.top(nat.cx), (nat.cx, 542), color="ink")
c.arrow(nat.right(nat.cy), igw.left(nat.cy), color="ink")
c.text(nat.cx - 14, 604, "egress: Nexus proxy & Firewall, CVE feeds", 15, "end", color=MUTED)

# bastion -> EKS API (private endpoint) and X-ENI
c.arrow(bast.right(UY), cp.left(UY), color="ink")                              # 9
c.arrow(eks.right(1050), cp.left(1050), color="ink")
c.arrow(cp.left(1050), eks.right(1050), color="ink")
c.text(3425, 1076, "X-ENI :443 ↔ nodes", 15, "start", color=MUTED)

# pipeline
c.arrow(gw.right(Y), gl.left(Y))
c.arrow(gl.right(Y), jk.left(Y))                                               # 2 webhook
c.arrow(jk.right(Y), ag.left(Y))                                               # 3 spawn agent
c.arrow(ag.right(Y), sec.left(Y))                                              # 4 scan
c.arrow(sec.right(Y), nx.left(Y))                                              # 5 push
c.arrow(ag.left(Y2), gl.right(Y2))                                             # 6 bump version
TOPY = 715
c.arrow(gl.top(), (gl.cx, TOPY), (ar.cx, TOPY), ar.top(), color="ink")         # 7
c.text((gl.cx + ar.cx) / 2, TOPY - 10, "Argo CD pulls GitOps repo", 17, color=MUTED)

c.arrow(vt.top(1920), jk.bottom(1920), color=VAULT, dashed=True)
c.arrow(vcni.right(vcni.cy), cil.left(vcni.cy), color="ink")
c.text((vcni.x2 + cil.x1) / 2, vcni.cy - 10, "chain", 15, color=MUTED)
c.arrow(ca.right(ca.cy), asg.left(ca.cy), color="ink")
c.arrow(kc.right(kc.cy), pools.left(kc.cy), color="ink")

c.arrow(eks.left(EBS_Y), ebs.right(EBS_Y), color="ink")
c.arrow(eks.bottom(1700), dt.top(1700), color="ink")
c.text(1715, 2165, "PostgreSQL :5432", 15, "start", color=MUTED)
c.arrow(eks.bottom(2400), efs.top(), color="ink")
c.text(2415, 2165, "NFS :2049", 15, "start", color=MUTED)
c.arrow(s3gw.left(S3_Y), s3.right(S3_Y), color="ink")

# telemetry
c.arrow(tel.right(TEL_Y), nlb.left(TEL_Y), color=TELE, width=3)                 # 8
TR = 3440 + OX
for b in (mim, lok, tmp):
    c.elbow(nlb.right(TEL_Y), b.left(b.cy), via_x=TR, color=TELE)
c.arrow((graf.cx, 838), be.top(graf.cx), color="ink", dashed=True)
c.text(graf.cx + 12, 925, "query", 15, "start", color=MUTED)
c.arrow(be.bottom(3560 + OX), (3560 + OX, os3.cy), os3.left(os3.cy), color="ink")

for x, y, n in [(160, UY, 1), (1795, Y, 2), (2045, Y, 3), (2315, Y, 4), (2785, Y, 5),
                (1795, Y2, 6), (2900, TOPY, 7), (3755, TEL_Y, 8), (3290, UY, 9)]:
    marker(x, y, n)

# ================================================================== legend
steps = [
    "Corporate → Direct Connect (VPN dự phòng) → TGW → internal ALB → Gateway API → GitLab",
    "Webhook từ GitLab kích hoạt Jenkins controller",
    "Jenkins tạo agent pod ở ns jenkins-agents (NodePool ci-agents, spot)",
    "SAST · SCA · IAST · image/IaC scan — gate fail thì dừng",
    "Đẩy image + SBOM lên Nexus, Nexus Firewall chặn OSS độc hại; ký bằng cosign",
    "Agent cập nhật version trong GitOps repo",
    "Argo CD reconcile mọi namespace (trừ gitlab — do Terraform cài)",
    "Grafana Alloy đẩy metric · log · trace sang Observability account",
    "Bastion (SSM) → EKS API private endpoint: kubectl, Terraform cài GitLab + bootstrap Argo CD",
]
for i, s in enumerate(steps):
    x = 40 + (i // 3) * 1250
    y = 2590 + (i % 3) * 50
    marker(x + 16, y - 6, i + 1)
    c.text(x + 46, y, s, 19, "start")
lx = 3800
for k, (col, dash, txt) in enumerate([("line", False, "Luồng pipeline"), ("ink", False, "AWS API · GitOps · storage"),
                                     (VAULT, True, "Secrets"), (TELE, False, "Telemetry")]):
    y = 2584 + k * 50
    c.arrow((lx, y), (lx + 80, y), color=col, dashed=dash)
    c.text(lx + 96, y + 6, txt, 18, "start")
lx2 = 3800 - 330
for k, (col, txt) in enumerate([(TF_PURPLE, "Terraform"), (ARGO, "Argo CD")]):
    y = 2584 + k * 50
    c.under.append(f'<rect x="{lx2}" y="{y - 13}" width="96" height="26" rx="13" fill="{col}"/>')
    c.text(lx2 + 48, y + 6, txt, 15, weight=700, color="white")
    c.text(lx2 + 110, y + 6, "cài đặt namespace", 18, "start")
c.under.append(f'<rect x="{lx2}" y="{2684 - 12}" width="24" height="24" rx="4" fill="white" stroke="#8A94A6" '
               f'stroke-width="2" stroke-dasharray="4 3"/>')
c.text(lx2 + 36, 2690, "Chưa có logo (Seeker)", 18, "start")

c.save(sys.argv[1] if len(sys.argv) > 1 else "platform_blueprint_v3")
print("ok")
