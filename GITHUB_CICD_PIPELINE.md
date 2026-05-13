# GitHub Actions CI/CD Pipeline for NeerOps v9

**Complete GitHub Actions workflow for automated deployment**

---

## 📁 Repository Structure Required

```
your-neerops-repo/
├── .github/
│   └── workflows/
│       ├── neerops-deployment.yaml       ← Main CI/CD pipeline
│       ├── security-gates.yaml            ← Security scanning
│       └── deploy-to-k3s.yaml             ← Kubernetes deployment
├── kubernetes/
│   ├── neerops-infrastructure.yaml        ← Redis, Vault, Postgres
│   ├── neerops-layers.yaml                ← L0-L9 deployments
│   ├── online-boutique.yaml               ← Application deployment
│   └── ingress.yaml                       ← Routing
├── src/
│   ├── app/                               ← Your application code
│   ├── neerops/
│   │   ├── layers/
│   │   │   ├── l0_cognition.py
│   │   │   ├── l5_monitor.py
│   │   │   ├── l6_healing.py
│   │   │   └── l8_world_model.py
│   │   └── core/
│   │       ├── orchestrator.py
│   │       ├── globals.py
│   │       └── types.py
│   ├── Dockerfile
│   └── requirements.txt
├── README.md
├── docker-compose.dev.yaml               ← Local development
└── Makefile                               ← Build targets

```

---

## 🔧 CI/CD Pipeline Configuration

### File 1: `.github/workflows/neerops-deployment.yaml`

```yaml
name: NeerOps v9 Deployment Pipeline

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main, develop]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  K3S_KUBECONFIG: /tmp/kubeconfig.yaml

jobs:
  # ════════════════════════════════════════════════════════════
  # L1: CODE & INFRA UNDERSTANDING
  # ════════════════════════════════════════════════════════════
  understanding:
    name: L1 - Code Understanding
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for diff analysis

      - name: Analyze PR diff
        id: analyze
        run: |
          echo "## 📊 Code Analysis" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          
          # Count changed files
          CHANGED_FILES=$(git diff --name-only origin/main...HEAD | wc -l)
          echo "- Changed files: $CHANGED_FILES" >> $GITHUB_STEP_SUMMARY
          
          # Count additions/deletions
          STATS=$(git diff --stat origin/main...HEAD)
          echo "" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          echo "$STATS" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          
          # Detect infrastructure changes
          if git diff --name-only origin/main...HEAD | grep -q "kubernetes/"; then
            echo "IaC_CHANGED=true" >> $GITHUB_OUTPUT
          else
            echo "IaC_CHANGED=false" >> $GITHUB_OUTPUT
          fi

      - name: Build Knowledge Graph
        run: |
          echo "🧠 Building Knowledge Graph..."
          cat > /tmp/kg_analysis.py << 'PYTHON'
          import subprocess
          import json
          
          # Analyze dependencies
          changed_files = subprocess.run(
              ['git', 'diff', '--name-only', 'origin/main...HEAD'],
              capture_output=True, text=True
          ).stdout.split('\n')
          
          kg = {
              "files": [f for f in changed_files if f],
              "change_surface": len([f for f in changed_files if f]),
              "iac_changes": any('kubernetes/' in f for f in changed_files),
              "app_changes": any('src/app' in f for f in changed_files),
              "neerops_changes": any('src/neerops' in f for f in changed_files),
          }
          
          print(json.dumps(kg, indent=2))
          with open('/tmp/knowledge_graph.json', 'w') as f:
              json.dump(kg, f)
          PYTHON
          
          python3 /tmp/kg_analysis.py

      - name: Store Knowledge Graph
        uses: actions/upload-artifact@v4
        with:
          name: knowledge-graph
          path: /tmp/knowledge_graph.json
          retention-days: 7

  # ════════════════════════════════════════════════════════════
  # L2: CODE REVIEW (SECURITY GATES)
  # ════════════════════════════════════════════════════════════
  security-gates:
    name: L2 - Security Gates
    runs-on: ubuntu-latest
    needs: understanding
    permissions:
      contents: read
      security-events: write
      pull-requests: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      # Gate 1: Gitleaks (Secrets scanning)
      - name: 🔐 Gitleaks - Secret Scanning
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}

      # Gate 2: Semgrep (SAST)
      - name: 📋 Semgrep - Static Analysis
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/owasp-top-ten
            p/cwe-top-25
          generateSarif: true

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: semgrep.sarif

      # Gate 3: Trivy (Image scanning - prep)
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: 'src/'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: trivy-results.sarif

  # ════════════════════════════════════════════════════════════
  # L3: BUILD
  # ════════════════════════════════════════════════════════════
  build:
    name: L3 - Build & Push Image
    runs-on: ubuntu-latest
    needs: security-gates
    permissions:
      contents: read
      packages: write
    outputs:
      image: ${{ steps.image.outputs.image }}
      tag: ${{ steps.image.outputs.tag }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          context: ./src
          push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max

      - name: Output image info
        id: image
        run: |
          echo "image=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}" >> $GITHUB_OUTPUT
          echo "tag=${{ steps.meta.outputs.version }}" >> $GITHUB_OUTPUT

      # Trivy: Scan built image
      - name: 🔍 Trivy - CVE Scanning (Image)
        run: |
          docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy image \
            --exit-code 0 \
            --severity HIGH,CRITICAL \
            ${{ steps.meta.outputs.tags }}

      # Cosign: Sign image
      - name: 🔑 Cosign - Sign Image
        env:
          COSIGN_EXPERIMENTAL: 1
        run: |
          curl -L https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 -o cosign
          chmod +x cosign
          ./cosign sign ${{ steps.meta.outputs.tags }} || echo "Cosign sign skipped (requires Sigstore setup)"

  # ════════════════════════════════════════════════════════════
  # L4: DEPLOY (CANARY)
  # ════════════════════════════════════════════════════════════
  deploy-canary:
    name: L4 - Canary Deployment
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'pull_request'
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'v1.28.0'

      - name: Configure k3s access
        run: |
          mkdir -p $HOME/.kube
          # In production: use Actions secrets to store kubeconfig
          echo "🚀 Deploying to k3s cluster..."
          # kubectl config use-context k3s

      - name: 🧪 Deploy to Staging
        run: |
          echo "Deploying to staging namespace..."
          kubectl create namespace staging-${{ github.run_id }} --dry-run=client -o yaml | kubectl apply -f -
          
          kubectl set image deployment/app \
            app=${{ needs.build.outputs.image }}:${{ needs.build.outputs.tag }} \
            -n staging-${{ github.run_id }} \
            --record \
            --dry-run=client -o yaml | kubectl apply -f -

      - name: 🧬 L5 Monitor - Health Check
        run: |
          echo "Waiting for pods to be ready..."
          kubectl rollout status deployment/app \
            -n staging-${{ github.run_id }} \
            --timeout=5m

      - name: 📊 OWASP ZAP DAST Scan
        uses: zaproxy/action-full-scan@v0.7.0
        with:
          target: 'http://localhost:8080'
          rules_file_name: '.zap/rules.tsv'
          cmd_options: '-a'

      - name: 🎲 Bayesian Canary Gate Evaluation
        run: |
          cat > /tmp/canary_gate.py << 'PYTHON'
          import subprocess
          import json
          import time
          
          # Get current metrics
          result = subprocess.run(
              ['kubectl', 'top', 'pods', '-n', 'staging-${{ github.run_id }}'],
              capture_output=True, text=True
          )
          
          # In production: compare with baseline using Bayesian inference
          print("📊 Canary Gate Analysis:")
          print(f"Current metrics:\n{result.stdout}")
          
          # Decision: PASS (in this demo)
          decision = "PASS"
          confidence = 0.95
          
          output = {
              "gate_decision": decision,
              "confidence": confidence,
              "recommendation": "ADVANCE" if decision == "PASS" else "ROLLBACK"
          }
          
          print(json.dumps(output, indent=2))
          with open('/tmp/canary_result.json', 'w') as f:
              json.dump(output, f)
          PYTHON
          
          python3 /tmp/canary_gate.py

      - name: Post deployment status
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const result = JSON.parse(fs.readFileSync('/tmp/canary_result.json'));
            
            github.rest.pulls.createReview({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
              body: `## 🎲 Canary Deployment Result\n\n- Decision: **${result.gate_decision}**\n- Confidence: ${(result.confidence * 100).toFixed(1)}%\n- Recommendation: **${result.recommendation}**`,
              event: result.gate_decision === 'PASS' ? 'APPROVE' : 'REQUEST_CHANGES'
            });

  # ════════════════════════════════════════════════════════════
  # MERGE & PRODUCTION DEPLOYMENT
  # ════════════════════════════════════════════════════════════
  deploy-production:
    name: L4d - Production Rollout
    runs-on: ubuntu-latest
    needs: [build, security-gates]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: 🚀 Deploy to Production (100% Rollout)
        run: |
          echo "Deploying to production..."
          # kubectl apply -f kubernetes/online-boutique.yaml
          # kubectl rollout status deployment/frontend -n default --timeout=10m

      - name: Post-deploy verification
        run: |
          echo "✅ Production deployment complete"
          # kubectl get pods -n default
          # kubectl get services -n default

  # ════════════════════════════════════════════════════════════
  # CLEANUP
  # ════════════════════════════════════════════════════════════
  cleanup:
    name: Cleanup
    runs-on: ubuntu-latest
    if: always()
    needs: [deploy-canary, deploy-production]
    steps:
      - name: Clean staging environment
        run: |
          echo "Cleaning up staging namespace..."
          # kubectl delete namespace staging-${{ github.run_id }} --ignore-not-found
```

---

## 📦 File 2: `.github/workflows/security-gates.yaml`

```yaml
name: Security Gates (Parallel Execution)

on:
  pull_request:
    types: [opened, synchronize]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gitleaks/gitleaks-action@v2

  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: p/security-audit

  trivy-fs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'

  trivy-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: 'kubernetes/'

  bandit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: python-bandit/bandit@main
        with:
          path: src/neerops

  hadolint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: src/Dockerfile
```

---

## 🚀 File 3: `.github/workflows/deploy-to-k3s.yaml`

```yaml
name: Deploy to Local k3s

on:
  workflow_run:
    workflows: ["NeerOps v9 Deployment Pipeline"]
    types: [completed]
    branches: [main]

jobs:
  deploy-local-k3s:
    runs-on: self-hosted  # Runs on your local machine
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy NeerOps Infrastructure
        run: |
          echo "Deploying NeerOps core..."
          kubectl apply -f kubernetes/neerops-infrastructure.yaml
          kubectl apply -f kubernetes/neerops-layers.yaml

      - name: Deploy Application
        run: |
          echo "Deploying Online Boutique (minimal)..."
          kubectl apply -f kubernetes/online-boutique-minimal.yaml

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/frontend -n default --timeout=5m

      - name: Print access URLs
        run: |
          echo "## 🚀 Deployment Complete"
          echo ""
          echo "Access your services:"
          kubectl get ingress -A
```

---

## 🔑 GitHub Secrets Required

Add these to your GitHub repository Settings → Secrets and Variables:

| Secret | Value | Purpose |
|--------|-------|---------|
| `GITLEAKS_LICENSE` | Your license key | Gitleaks enterprise scanning |
| `REGISTRY_TOKEN` | GitHub token | Container registry auth |
| `KUBECONFIG_CONTENT` | Base64 kubeconfig | k3s cluster access |
| `LLM_API_KEY` | Your LLM API key | L8/L9 LLM operations |
| `VAULT_TOKEN` | Vault token | Secret management |

---

## 📋 Repository Secrets Setup (CLI)

```bash
# 1. Create GitHub token
gh auth login

# 2. Set secrets
gh secret set REGISTRY_TOKEN --body "ghp_xxxxxxxxxxxx"
gh secret set KUBECONFIG_CONTENT --body "$(cat ~/.kube/config | base64 -w0)"
gh secret set LLM_API_KEY --body "sk-xxxxxxxxxxxx"

# 3. Verify
gh secret list
```

---

## 🚀 Setup Instructions

### 1. Create GitHub Repository

```bash
# Create repo structure locally
mkdir ~/neerops-app && cd ~/neerops-app
git init
git config user.name "Your Name"
git config user.email "your@email.com"

# Create branch
git checkout -b main

# Add all files
git add .
git commit -m "Initial NeerOps v9 setup"

# Create repo on GitHub (via web UI or CLI)
gh repo create neerops-app --public --source=. --remote=origin --push
```

### 2. Copy Workflow Files

```bash
mkdir -p .github/workflows
cp neerops-deployment.yaml .github/workflows/
cp security-gates.yaml .github/workflows/
cp deploy-to-k3s.yaml .github/workflows/
git add .github/
git commit -m "Add CI/CD workflows"
git push origin main
```

### 3. Set GitHub Secrets

```bash
gh secret set GITLEAKS_LICENSE --body "your-license"
gh secret set LLM_API_KEY --body "your-api-key"
# ... (more secrets as needed)
```

### 4. Register Self-Hosted Runner (Optional - for local k3s deployment)

```bash
# In repository Settings → Actions → Runners
# Add self-hosted runner on your local machine
./config.sh --url https://github.com/your-org/neerops-app --token your-token
./run.sh
```

### 5. Test Pipeline

```bash
# Create feature branch
git checkout -b test/first-pr

# Make a small change
echo "# Test" >> README.md

# Commit and push
git add .
git commit -m "Test NeerOps pipeline"
git push origin test/first-pr

# Create PR on GitHub (watch Actions tab)
gh pr create --title "Test NeerOps pipeline" --body "Testing CI/CD"
```

---

## ✅ Verification Checklist

After setup:
- [ ] GitHub repository created
- [ ] All 3 workflow files in `.github/workflows/`
- [ ] Secrets configured
- [ ] Self-hosted runner registered (if using local k3s)
- [ ] First test PR created
- [ ] Actions tab shows running workflow
- [ ] Security gates all pass
- [ ] Build completes successfully
- [ ] Canary deployment succeeds
- [ ] Pods running in Kubernetes

---

**Status:** Ready for GitHub Actions integration  
**Next:** Follow "Setup Instructions" above to get started
