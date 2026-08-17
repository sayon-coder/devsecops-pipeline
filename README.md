# Autonomous Secure DevSecOps Infrastructure Pipeline

![Pipeline Status](https://github.com/sayon-coder/devsecops-pipeline/actions/workflows/pipeline.yml/badge.svg)

A production-grade DevSecOps pipeline built on AWS, designed to automatically enforce security at every stage of the software delivery lifecycle — from code commit to cloud deployment.

---

## Architecture Overview
Git Push → Secret Scan (Gitleaks) → IaC Scan (Trivy) → Container Scan (Trivy) → Deploy (Terraform) → Observe (Splunk)

Every stage is a hard gate. A failure at any point blocks the entire pipeline.

---

## What This Pipeline Does

### 1. Secret Detection
Every commit is scanned by **Gitleaks** before anything else runs. If a hardcoded API key, password, or token is detected anywhere in the repository history, the pipeline fails immediately. A pre-commit hook enforces this locally as well — secrets are caught before they ever leave the developer's machine.

### 2. IaC Security Scan
Terraform infrastructure files are scanned by **Trivy** for misconfigurations before any infrastructure is provisioned. This catches issues like open security groups, unencrypted storage, or overly permissive IAM policies at the code level, not after deployment.

### 3. Container Build & Security Scan
The application Docker image is built using a hardened **Python 3.12 Alpine** base image and scanned by **Trivy** for known CVEs. The pipeline is configured with `exit-code: 1` on CRITICAL or HIGH severity findings — any vulnerable image is automatically rejected and never deployed.

Security decisions in the Dockerfile:
- Alpine base image: minimal attack surface, no unnecessary OS packages
- Non-root user: application runs as `appuser`, not root
- No package caches: `--no-cache-dir` prevents stale dependency storage

### 4. Infrastructure Deployment
On passing all security gates, **Terraform** provisions a high-availability multi-subnet AWS VPC:
- Public subnets across two Availability Zones (load balancer + web tier)
- Private subnet for the application tier
- Internet Gateway with route tables
- All Terraform state stored remotely in an encrypted, versioned S3 bucket

### 5. Observability
Pipeline execution events are streamed in real-time to **Splunk Observability Cloud** via the ingest API. Every deployment records the commit SHA, branch, actor, and pipeline status — providing a full audit trail of every change that reached production.

---

## Security Decisions

| Decision | Reason |
|----------|--------|
| Alpine base image | Eliminates ~80% of CVEs present in Debian-based images |
| Non-root container user | Limits blast radius if the container is compromised |
| Hard Trivy gate (exit-code 1) | Vulnerable images are blocked, not just flagged |
| Remote Terraform state (S3) | Encrypted, versioned, team-accessible — never local |
| GitHub Secrets for credentials | Zero plaintext secrets in source code or logs |
| Pre-commit Gitleaks hook | Catches secrets before they enter version control |

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Terraform | Infrastructure as Code — VPC, subnets, networking |
| GitHub Actions | CI/CD pipeline orchestration |
| Trivy | Container and IaC vulnerability scanning |
| Gitleaks | Secret detection in commits and history |
| Docker (Alpine) | Hardened application containerization |
| AWS (ap-south-1) | Cloud infrastructure provider |
| Splunk Observability Cloud | Real-time pipeline event streaming |
| pre-commit | Local secret and code quality hooks |

---

## Project Structure
devsecops-pipeline/
├── .github/
│ └── workflows/
│ └── pipeline.yml # Main CI/CD pipeline
├── app/
│ ├── main.py # Flask application
│ ├── requirements.txt # Python dependencies
│ └── Dockerfile # Hardened Alpine container
├── terraform/
│ ├── provider.tf # AWS provider + S3 backend
│ ├── variables.tf # Input variables
│ └── vpc.tf # Multi-subnet HA VPC
├── .pre-commit-config.yaml # Local security hooks
└── .gitignore

---

## Pipeline Stages
Secret Detection (Gitleaks)
↓
IaC Security Scan (Trivy fs ./terraform)
↓
Build & Container Scan (Trivy image)
↓
Deploy Infrastructure (Terraform apply)
↓
Stream Logs to Splunk

---

## Autonomous CVE Remediation

When Trivy detects fixable CRITICAL/HIGH vulnerabilities, the pipeline does not just fail and stop. It autonomously:

1. Parses the Trivy JSON report to identify packages with available fixes
2. Generates a patched Dockerfile with security updates applied
3. Creates a new git branch named `auto-remediation/{commit}-fix-cves`
4. Opens a Pull Request authored by the pipeline bot with a full remediation report
5. Labels the PR with `security` and `automated-remediation` for triage
6. Streams the remediation event to Splunk Observability

This closes the loop from detection to remediation without human intervention — mean time to remediation measured in seconds, not days.

## Key Design Principles

**Shift-left security** — Security checks run before deployment, not after. Issues are caught at the earliest possible point in the pipeline where they are cheapest to fix.

**Hard gates over warnings** — Every security scan uses `exit-code: 1`. The pipeline does not produce security reports and continue. It stops.

**Zero plaintext credentials** — All secrets are stored in GitHub Actions Secrets and AWS Secrets Manager. No credentials appear in source code, logs, or Terraform state.

**Immutable infrastructure** — Terraform manages all infrastructure as code. No manual changes to the AWS console. Every environment is reproducible from a single `terraform apply`.
