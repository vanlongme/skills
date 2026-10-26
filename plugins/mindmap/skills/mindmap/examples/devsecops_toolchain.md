# DevSecOps toolchain trên EKS {icon:aws/compute/elastic-kubernetes-service}

## Source & CI {color:#E07B00}
- GitLab {icon:onprem/vcs/gitlab}
  - Monorepo · MR approval
  - GitLab CI runners
- Jenkins agents {icon:onprem/ci/jenkins}
  - Namespace riêng
  - Karpenter spot nodes

## Code security {color:#147EBA}
- SAST
  - Coverity {logo:coverity}
  - Semgrep rules
- SCA
  - Black Duck {logo:blackduck}
  - Nexus Firewall {logo:sonatype}
- IAST · Seeker

## Supply chain {color:#7AA116}
- Ký image bằng Cosign {logo:cosign}
- Kyverno verify-image policy {logo:kyverno}
- Trivy Operator {icon:onprem/security/trivy}
  - DB mirror từ ECR
  - Quét image trong cluster

## Delivery {color:#8C4FFF}
- Argo CD (GitOps) {icon:onprem/gitops/argocd}
  - App of apps
  - Sync waves
- Terraform cho GitLab & hạ tầng
- Gateway API · agentgateway {logo:agentgateway}

## Runtime {color:#D13212}
- Cilium + VPC CNI chaining {logo:cilium}
- Tetragon runtime enforcement {logo:tetragon}
- Bottlerocket AMI

## Observability {color:#00A4A6}
- Grafana LGTM {icon:onprem/monitoring/grafana}
  - Loki · logs
  - Mimir · metrics
  - Tempo · traces
- Alloy collectors {logo:alloy}
