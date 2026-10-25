"""EKS fully private — internal components and their dependencies on VPC endpoints, AWS services and KMS.

Layout: one horizontal lane per concern.
  [in-cluster component] -> [VPC endpoint(s)] -> [AWS service] -> [KMS key usage]
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from archdiag import Canvas, logo  # noqa: E402

c = Canvas(2700, 2340)
KMS_RED = "#DD344C"
MONO = "DejaVu Sans Mono, monospace"

# ------------------------------------------------------------------ column x-ranges
A1, A2 = 120, 1240      # in-cluster lanes
B1, B2 = 1320, 1770     # endpoint lanes
C1, C2 = 1885, 2285     # service lanes
K1, K2 = 2380, 2640     # KMS column

LANES = [
    dict(title="Image pull",
         comps=[("aws/compute/ec2", "Worker node\n(containerd)"), ("k8s/controlplane/kubelet", "kubelet")],
         eps=[("ecr.api", "Interface"), ("ecr.dkr", "Interface"), ("s3", "Gateway")],
         svcs=[("aws/compute/ec2-container-registry", "Amazon ECR"), ("aws/storage/simple-storage-service-s3", "Amazon S3\n(image layers)")],
         kms="ECR repos ·\nS3 SSE-KMS"),
    dict(title="Workload identity",
         comps=[("k8s/compute/ds", "Pod Identity\nAgent"), ("k8s/rbac/sa", "ServiceAccount\n(IRSA)"), ("k8s/compute/pod", "App pod\n(AWS SDK)")],
         eps=[("sts", "Interface"), ("eks-auth", "Interface")],
         svcs=[("aws/security/identity-and-access-management-iam-aws-sts", "IAM · STS\n(role creds)")],
         kms=None),
    dict(title="Node lifecycle & storage",
         comps=[("k8s/compute/ds", "VPC CNI\n(aws-node)"), ("k8s/compute/deploy", "Karpenter"),
                ("aws/storage/elastic-block-store-ebs", "EBS CSI\ndriver")],
         eps=[("ec2", "Interface"), ("sqs", "Interface"), ("eks", "Interface")],
         svcs=[("aws/compute/ec2", "EC2 · EBS"), ("aws/integration/simple-queue-service-sqs", "SQS\n(interrupt)")],
         kms="EBS volume\nencryption"),
    dict(title="Load balancing — AWS Load Balancer Controller", h=330,
         comps=[("k8s/network/ing", "Ingress\n(alb)"), ("k8s/network/svc", "Service\n(type: LB)"),
                ("k8s/compute/deploy", "LB Controller\n(+ webhook)"), ("k8s/others/crd", "TargetGroup\nBinding")],
         notes=["→ creates internal ALB/NLB in subnets tagged kubernetes.io/role/internal-elb=1 · target-type: ip → pod IPs",
                "Private flags: --enable-shield=false · --enable-waf=false · --enable-wafv2=false (if no wafv2 endpoint)",
                "Calls: ELB API (LB / TG / listeners) · EC2 (SG rules, subnet & ENI lookup) · ACM (cert discovery) · STS (IRSA)"],
         eps=[("elasticloadbalancing", "Interface"), ("ec2", "Interface"), ("sts", "Interface"),
              ("acm", "Interface"), ("wafv2", "Interface · opt")],
         svcs=[("aws/network/elb-application-load-balancer", "Internal\nALB / NLB"),
               ("aws/security/certificate-manager", "ACM\n(TLS certs)"), ("aws/security/waf", "WAFv2\n(optional)")],
         kms=None),
    dict(title="Observability",
         comps=[("k8s/compute/ds", "Fluent Bit"), ("k8s/compute/ds", "CloudWatch\nAgent / ADOT")],
         eps=[("logs", "Interface"), ("monitoring", "Interface")],
         svcs=[("aws/management/cloudwatch-logs", "CloudWatch\nLogs"), ("aws/management/cloudwatch", "CloudWatch\nMetrics")],
         kms="Log group\nencryption"),
    dict(title="Secrets & operations",
         comps=[("aws/management/systems-manager", "SSM Agent\n(on node)"), ("k8s/compute/deploy", "External Secrets\n/ Secrets CSI")],
         eps=[("ssm", "Interface"), ("ssmmessages", "Interface"), ("ec2messages", "Interface"),
              ("secretsmanager", "Interface"), ("kms", "Interface")],
         svcs=[("aws/management/systems-manager", "Systems\nManager"), ("aws/security/secrets-manager", "Secrets\nManager")],
         kms="Secrets Manager\nsecrets"),
]
TOP0, GAP = 550, 20


def pill(x1, x2, y, name, kind):
    """Endpoint row: icon + service suffix + Interface/Gateway tag. Returns center y."""
    c.under.append(f'<rect x="{x1}" y="{y}" width="{x2 - x1}" height="32" rx="16" fill="white" '
                   f'stroke="{"#7AA116" if kind == "Gateway" else "#8C4FFF"}" stroke-width="2"/>')
    c.icon("aws/network/endpoint", x1 + 6, y + 3, 26)
    c.under.append(f'<text x="{x1 + 42}" y="{y + 22}" font-family="{MONO}" font-size="18" fill="{c.t["ink"]}">{name}</text>')
    c.text(x2 - 14, y + 22, kind, 15, "end", color="#5A6B86")
    return y + 16


def row_icons(x1, x2, top, items, s=80, size=20):
    n = len(items)
    for i, (ic, lb) in enumerate(items):
        cx = x1 + (x2 - x1) * (i + .5) / n
        c.icon(ic, cx - s / 2, top, s, label=lb, size=size)


# ------------------------------------------------------------------ frames
c.box(30, 30, 2670, 2310, "solid", "AWS Cloud · ap-southeast-1", tab="aws")

cp = c.box(A1, 110, A2, 370, "solid", "Amazon EKS control plane (AWS-managed VPC)", tab="aws")
row_icons(A1, A2, 165, [
    ("aws/compute/elastic-kubernetes-service", "Amazon EKS"),
    ("k8s/controlplane/api", "kube-apiserver\n(private only)"),
    ("k8s/infra/etcd", "etcd\n(Secrets)"),
    ("k8s/controlplane/c-m", "controller-\nmanager"),
    ("k8s/controlplane/sched", "scheduler"),
])

vpc = c.box(80, 420, 1810, 2210, "solid")
c.icon("aws/network/vpc", 96, 428, 40)
c.text(146, 457, "VPC 10.0.0.0/16 · private subnets only · no IGW · no NAT", 21, "start", weight=600)

dp = c.box(100, 490, 1260, 2185, "dashed", "EKS data plane — nodes in private subnets (3 AZ)", label_pos="top-left")
epg = c.box(1300, 490, 1790, 2185, "dashed", "VPC endpoints (PrivateLink · private DNS)", label_pos="top-left", size=20)
svg_ = c.box(1860, 420, 2310, 2210, "dashed", "AWS regional services", label_pos="top-left", size=20)
kms = c.box(K1, 110, K2, 2150, "solid")
c.icon("aws/security/key-management-service", (K1 + K2) / 2 - 45, 135, 90, label="AWS KMS\ncustomer-managed keys", size=20)

# ------------------------------------------------------------------ lanes
kms_pill_y = None
top = TOP0
for i, L in enumerate(LANES):
    if i:
        top += LANES[i - 1].get("h", 236) + GAP
    LANE_H = L.get("h", 236)
    cy = top + (236 if "notes" in L else LANE_H) / 2 + (0 if "notes" not in L else 0)
    a = c.box(A1, top, A2, top + LANE_H, "grey")
    c.text(A1 + 16, top + 30, f"{i + 1}. {L['title']}", 20, "start", weight=700)
    row_icons(A1 + 180, A2, top + 45, L["comps"])
    for j, ln in enumerate(L.get("notes", [])):
        c.text(A1 + 16, top + 240 + j * 30, ln, 17, "start", color="#3A4450")

    b = c.box(B1, top, B2, top + LANE_H, "grey")
    n = len(L["eps"])
    y0 = cy - (n * 40 - 8) / 2
    for j, (nm, kind) in enumerate(L["eps"]):
        py = pill(B1 + 15, B2 - 15, y0 + j * 40, nm, kind)
        if nm == "kms":
            kms_pill_y = py

    s = c.box(C1, top, C2, top + LANE_H, "grey")
    row_icons(C1, C2, top + 45, L["svcs"], s=75, size=19)

    c.arrow(a.right(cy), b.left(cy), color="ink")
    c.arrow(b.right(cy), s.left(cy), color="ink")
    if L["kms"]:
        c.arrow(s.right(cy), kms.left(cy), color=KMS_RED, dashed=True)
        c.text((K1 + K2) / 2, cy - 4, L["kms"], 18, color=KMS_RED, lh=23)

# control plane <-> data plane (cross-account ENIs) and control plane -> KMS
XENI = 960
c.arrow(cp.bottom(XENI), dp.top(XENI), color="ink")
c.arrow(dp.top(XENI), cp.bottom(XENI), color="ink")
c.text(XENI + 18, 404, "X-ENI · private API endpoint (443)", 18, "start", color="#3A4450")

CPY = 320
c.arrow(cp.right(CPY), kms.left(CPY), color=KMS_RED, dashed=True)
c.text(1800, CPY - 14, "EKS secrets envelope encryption (kms:Encrypt / Decrypt)", 18, color=KMS_RED)
c.text((K1 + K2) / 2, CPY + 40, "EKS Secrets\n(etcd)", 18, color=KMS_RED, lh=23)

# direct kms endpoint use (apps / SOPS / ESO decrypt): route under the lanes
BY = 2235
kp = (B2 + 2, kms_pill_y)
c.arrow(kp, (1835, kms_pill_y), (1835, BY), ((K1 + K2) / 2, BY), kms.bottom(), color=KMS_RED, dashed=True)
c.text(2120, BY + 30, "kms endpoint: app / SOPS / ESO decrypt", 17, color=KMS_RED)

# legend
c.text(1320, 150, "Legend", 20, "start", weight=700)
c.arrow((1320, 190), (1420, 190), color="ink");            c.text(1440, 197, "AWS API call via VPC endpoint", 18, "start")
c.arrow((1320, 230), (1420, 230), color=KMS_RED, dashed=True); c.text(1440, 237, "KMS key usage (encrypt / decrypt)", 18, "start")
pill(1830, 2190, 174, "name", "Interface")
pill(1830, 2190, 214, "name", "Gateway")

c.save(sys.argv[1] if len(sys.argv) > 1 else "eks_internal")
print("ok")
