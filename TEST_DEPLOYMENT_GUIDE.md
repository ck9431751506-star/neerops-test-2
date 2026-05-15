# 🧪 NeerOps v9 CI/CD Test Guide - Full Pipeline Validation

**Purpose:** Test the complete NeerOps v9 CI/CD pipeline with a dummy application  
**Duration:** 30-45 minutes (including workflow execution)  
**Status:** Manual approval required (no auto-approve)

---

## 📋 Overview

This guide helps you validate that your complete NeerOps v9 CI/CD pipeline works correctly **before deploying the production application**.

### What You're Testing

```
Dummy Test App (Node.js)
        ↓
GitHub Repository
        ↓
Push Code & Create PR
        ↓
GitHub Actions Triggered
        ├─ L1: Code Understanding (2 min)
        ├─ L2: Security Gates (5 min)
        ├─ L3: Build & Push (8 min)
        ├─ L4: Canary Evaluation (1 min)
        └─ Results Posted to PR
        ↓
YOU manually review & approve
```

### Key Difference: Manual Approval Required

Unlike production deployments that auto-approve passing gates, **this test pipeline requires YOU to manually review and approve** before any deployment proceeds. This gives you confidence in the process.

---

## 🎯 Step 1: Create Test GitHub Repository (5 min)

### Option A: Web UI
1. Go to https://github.com/new
2. **Repository name:** `neerops-test` (or `neerops-deployment-test`)
3. **Description:** "Test pipeline for NeerOps v9 CI/CD validation"
4. **Visibility:** Public
5. **Initialize:** Leave unchecked
6. Click **Create repository**

### Option B: GitHub CLI
```bash
gh repo create neerops-test --public
```

---

## 🚀 Step 2: Push Test Application to GitHub (5 min)

### Create local test repository

```bash
# Create a new directory for the test repo
mkdir ~/neerops-test
cd ~/neerops-test

# Initialize git
git init
git config user.email "your@email.com"
git config user.name "Your Name"
git branch -M main

# Create directory structure
mkdir -p test-app test-workflows

# Copy the dummy app files
cp /home/chandan/NeerOps/test-app/index.js test-app/
cp /home/chandan/NeerOps/test-app/package.json test-app/
cp /home/chandan/NeerOps/test-app/Dockerfile test-app/

# Create .github/workflows directory
mkdir -p .github/workflows

# Copy modified test workflow (NO auto-approve)
cp /home/chandan/NeerOps/test-workflows/neerops-test-deployment.yaml .github/workflows/

# Create README
cat > README.md << 'EOF'
# NeerOps v9 - Test Pipeline

This is a test repository to validate the NeerOps v9 CI/CD pipeline before production deployment.

## Quick Test

1. Create a PR with any change
2. Watch GitHub Actions execute
3. Review the Canary Gate report
4. Manually approve to proceed

## Structure

- `test-app/` - Dummy Node.js application
- `.github/workflows/` - GitHub Actions workflows
- `neerops-test-deployment.yaml` - Main test pipeline (manual review required)

## Key Features

- ✅ All security gates (Gitleaks, Semgrep, Trivy)
- ✅ Docker build and push
- ✅ Canary gate evaluation
- ✅ Manual approval required (no auto-approve)

## Next Steps

After validating this test pipeline, deploy the production NeerOps framework to your main repository.
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
node_modules/
dist/
build/
*.log
.env
.env.local
.DS_Store
EOF

# Add all files and commit
git add .
git commit -m "Initial test setup for NeerOps v9 CI/CD pipeline"

# Add GitHub as remote (use YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/neerops-test.git

# Push to GitHub
git push -u origin main
```

**Replace `YOUR_USERNAME` with your actual GitHub username!**

---

## ✅ Step 3: Verify Files on GitHub (2 min)

After push completes:

1. Go to `https://github.com/YOUR_USERNAME/neerops-test`
2. Verify you see:
   - ✅ `test-app/` folder with index.js, package.json, Dockerfile
   - ✅ `.github/workflows/neerops-test-deployment.yaml`
   - ✅ `README.md`
   - ✅ `.gitignore`

---

## 🧪 Step 4: Create First Test PR (10 min)

This triggers the entire CI/CD pipeline.

```bash
cd ~/neerops-test

# Create a test branch
git checkout -b feature/test-deployment

# Make a small change to trigger workflow
echo "# Test change - $(date)" >> README.md

# Commit and push
git add README.md
git commit -m "test: trigger CI/CD pipeline validation"
git push origin feature/test-deployment
```

---

## 📍 Step 5: Create PR on GitHub (2 min)

1. Go to `https://github.com/YOUR_USERNAME/neerops-test`
2. You should see a banner saying "Compare & pull request"
3. Click **Create pull request**
4. Add title: "Test: Validate NeerOps v9 CI/CD Pipeline"
5. Click **Create pull request**

---

## 👀 Step 6: Watch the Pipeline Execute (15-20 min)

Once you create the PR, GitHub Actions automatically triggers.

### Monitor the pipeline:

1. Click **Actions** tab at top of repository
2. You should see "NeerOps v9 Test Pipeline" job running
3. Watch jobs execute in order:
   - **L1 - Code Understanding** (2 min)
   - **L2 - Security Gates** (5 min)
   - **L3 - Build & Push** (8 min)
   - **L4 - Canary Evaluation** (1 min)
   - **Summary** (1 min)

### What Each Stage Does

| Stage | Time | What It Checks |
|-------|------|---|
| **L1** | 2 min | Code changes analysis |
| **L2** | 5 min | 6 security scans (secrets, SAST, CVEs, Python, Docker) |
| **L3** | 8 min | Docker build, image scanning, push to registry |
| **L4** | 1 min | Canary metrics evaluation |

### Viewing Logs

Click on each job name to see detailed logs:

```
L1 - Code Understanding
  └─ Shows git diff analysis

L2 - Security Gates
  ├─ Gitleaks (secret scanning)
  ├─ Semgrep (static analysis)
  ├─ Trivy (vulnerability scanning)
  └─ ... (all 6 security tools)

L3 - Build & Push
  ├─ Docker buildx setup
  ├─ Extract metadata
  ├─ Build image
  └─ Push to registry

L4 - Canary Evaluation
  └─ Canary gate analysis
```

---

## 📊 Step 7: Review Canary Gate Report (5 min)

After L4 completes, scroll back to the PR conversation and you'll see:

### Example Report:

```
🎲 NeerOps Canary Gate Report

Status: ⏳ PENDING MANUAL REVIEW (No Auto-Approval)

Metrics Summary
- Error Rate: 0.2% (baseline: 0.5%)
- P99 Latency: 145ms (baseline: 150ms)
- CPU Usage: 25%
- Memory Usage: 512MB
- Throughput: 1200 req/s

Bayesian Gate Analysis
- P(new ≥ baseline): 96.0%
- Gate Threshold: 95%
- Passes Gate: ✅ YES
- Recommendation: PROCEED

Next Steps
🔍 MANUAL REVIEW REQUIRED before proceeding to production

- [ ] Reviewer: Verify metrics are acceptable
- [ ] Reviewer: Check error logs and traces
- [ ] Reviewer: Confirm no regressions
- [ ] Reviewer: Approve/Reject deployment

Note: This PR will NOT be automatically approved. A human reviewer must explicitly approve the deployment after verifying the canary metrics above.
```

### What This Means

✅ **Metrics passed the gate** (error rate down, latency down, etc.)  
⏳ **But you must manually approve** before proceeding  
🔍 **You're in control** - you decide if it's safe to deploy

---

## ✅ Step 8: Manual Approval Process

### How to Approve (Example)

In the PR, go to **Review changes** and:

1. Click **Review changes** button (top right)
2. Select **Approve**
3. Leave comment:
   ```
   Approving this change - metrics look good:
   - Error rate improved 60%
   - Latency improved 3%
   - No security gate failures
   - All tests passing
   
   Ready to proceed with deployment.
   ```
4. Click **Approve** button

### How to Reject (If Issues Found)

1. Click **Review changes** button
2. Select **Request changes**
3. Comment with what needs to be fixed
4. Click **Request changes**

---

## 🎯 What to Validate

When reviewing the Canary Report, check these metrics:

### Error Rate
```
Current:   0.2%
Baseline:  0.5%
Status:    ✅ Improved 60%
```

### Latency (P99)
```
Current:   145ms
Baseline:  150ms
Status:    ✅ Improved 3%
```

### Bayesian Gate
```
P(new ≥ baseline): 96% (threshold: 95%)
Status:            ✅ PASSES
```

### Security Gates
Look for green checkmarks on all security scans:
- ✅ Gitleaks (no secrets exposed)
- ✅ Semgrep (no SAST issues)
- ✅ Trivy (no CVEs)
- ✅ Bandit (no Python security issues)
- ✅ Hadolint (Dockerfile OK)

---

## 📌 Step 9: Complete the Test

After approval:

1. The pipeline **does not auto-deploy** (this is test-only)
2. You've validated:
   - ✅ Workflows trigger correctly
   - ✅ All 6 security gates execute
   - ✅ Docker build completes
   - ✅ Canary report generates
   - ✅ Manual approval process works
   - ✅ No auto-approve without review

3. Merge the PR (or close it)

---

## 🚀 Next Steps After Successful Test

Once this test pipeline passes and you're confident:

1. **Push Production NeerOps v9** to main repository
2. **Modify workflows for production** (add auto-approve for passing gates if desired)
3. **Deploy to Kubernetes** following QUICK_START_DEPLOYMENT.md

---

## 🔧 Troubleshooting

### Workflows Don't Trigger

**Problem:** No jobs appear in Actions tab  
**Solution:** 
- Check `.github/workflows/` directory exists
- Verify workflow file is named correctly
- Wait 30 seconds for GitHub to register

### Security Gate Fails

**Problem:** One of the security scans fails  
**Solution:**
- Click on the failed job to see details
- Fix the issue (e.g., secrets in code)
- Push new commit to same PR
- Workflow re-triggers automatically

### Build Fails

**Problem:** Docker build fails  
**Solution:**
- Check `test-app/Dockerfile` is valid
- Verify `test-app/package.json` is correct
- Click on build job to see error message

### Can't Push to GitHub

**Problem:** `git push` fails  
**Solution:**
```bash
# Check remote is set correctly
git remote -v
# Should show: origin  https://github.com/YOUR_USERNAME/neerops-test.git

# If not, set it:
git remote set-url origin https://github.com/YOUR_USERNAME/neerops-test.git

# Then try push again
git push -u origin main
```

---

## 📊 Success Criteria

You'll know the test is successful when:

✅ All 5 jobs complete (L1, L2, L3, L4, Summary)  
✅ No red ❌ marks (all green ✅)  
✅ Canary gate report posted to PR  
✅ Report shows "PENDING MANUAL REVIEW"  
✅ You can review and manually approve  
✅ PR can be merged or closed  

---

## 💡 Key Learnings

### This Test Validates:

1. **Workflow Triggering** - Actions fire on PR creation
2. **Security Gates** - All 6 scans execute in parallel
3. **Build Process** - Docker image builds and pushes
4. **Canary Evaluation** - Metrics collected and analyzed
5. **Manual Approval** - Review required, no auto-approve
6. **Reporting** - Clear feedback to PR

### For Production:

You can then modify workflows to:
- Auto-approve passing gates (optional)
- Deploy to staging automatically
- Run full integration tests
- Deploy to production on main branch
- Auto-rollback on failures

---

## 📞 Commands Reference

### Test Repo Setup
```bash
# Create and push test app
mkdir ~/neerops-test && cd ~/neerops-test
git init
git config user.email "your@email.com"
git config user.name "Your Name"

# Add files and commit
git add .
git commit -m "Initial test setup"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/neerops-test.git
git push -u origin main
```

### Create Test PR
```bash
# Create branch
git checkout -b feature/test

# Make change
echo "test" >> README.md

# Push and create PR
git add .
git commit -m "test: trigger pipeline"
git push origin feature/test

# Then go to GitHub to create PR
```

### Monitor Pipeline
```bash
# Watch in terminal (optional, GitHub UI is clearer)
watch -n 5 "gh run list -R YOUR_USERNAME/neerops-test"
```

---

## ✨ Final Notes

- **This is a test repository** - separate from production
- **Manual approval is the default** - you control deployments
- **No data is deployed** - this validates the process only
- **All logs are preserved** - review anytime in Actions tab
- **Reusable for CI/CD validation** - test any changes here first

---

**Status:** Ready to test  
**Time Estimate:** 30-45 minutes  
**Next:** Follow steps 1-9 above to validate your pipeline

Generated: May 14, 2026  
NeerOps v9 - Test Pipeline Validation Guide
