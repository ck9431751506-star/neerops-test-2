# 🚀 NeerOps v9 Test Pipeline - Step-by-Step Setup Guide

**Objective:** Set up dummy application on GitHub and test CI/CD pipeline  
**Time Required:** 45-60 minutes total  
**Difficulty:** Beginner-friendly (detailed steps provided)  
**Status:** Ready to execute

---

## 📋 Complete Step-by-Step Checklist

```
PHASE 1: GITHUB SETUP (10 min)
├─ Step 1: Create GitHub repository
├─ Step 2: Prepare local test directory
├─ Step 3: Copy test application files
├─ Step 4: Create workflow directory
└─ Step 5: Initialize git and push to GitHub

PHASE 2: VERIFICATION (5 min)
├─ Step 6: Verify files on GitHub
├─ Step 7: Check workflows are visible
└─ Step 8: Confirm everything is ready

PHASE 3: TESTING (25 min)
├─ Step 9: Create test branch
├─ Step 10: Make a small change
├─ Step 11: Push and create PR
├─ Step 12: Watch pipeline execute
├─ Step 13: Monitor all stages (L1-L4)
└─ Step 14: Review Canary Report

PHASE 4: MANUAL APPROVAL (5 min)
├─ Step 15: Review metrics in report
├─ Step 16: Manually approve in PR
└─ Step 17: Confirm success
```

---

## PHASE 1: GITHUB SETUP

### ✅ STEP 1: Create GitHub Repository (2 min)

**What you're doing:** Creating an empty repository on GitHub for the test application.

**Method A: Using GitHub Web UI (Recommended for first time)**

1. Go to https://github.com/new
2. Fill in these exact fields:
   - **Repository name:** `neerops-test`
   - **Description:** `Test pipeline for NeerOps v9 CI/CD validation`
   - **Visibility:** `Public`
   - **Initialize repository:** Leave unchecked (do NOT check "Add README")
3. Click green **"Create repository"** button
4. You'll see a page with setup instructions
5. **Keep this page open** - you'll need the commands

**What you should see:**
```
Quick setup — if you've done this kind of thing before
or
Set up in Desktop

…or create a new repository on the command line
echo "# neerops-test" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/neerops-test.git
git push -u origin main
```

✅ **Step 1 Complete** when you see the empty repository page on GitHub

---

### ✅ STEP 2: Prepare Local Test Directory (2 min)

**What you're doing:** Creating a local folder structure for your test application.

**In Terminal, run these commands:**

```bash
# Create test directory
mkdir -p ~/neerops-test

# Navigate into it
cd ~/neerops-test

# Verify you're in the right place
pwd
# Should output: /home/chandan/neerops-test
```

**Verify:**
```bash
ls -la
# Should show: empty directory
```

✅ **Step 2 Complete** when you see empty directory

---

### ✅ STEP 3: Copy Test Application Files (2 min)

**What you're doing:** Copying the dummy app files from NeerOps repo to your test directory.

**In Terminal, run these commands:**

```bash
# Make sure you're in neerops-test directory
cd ~/neerops-test

# Create directories
mkdir -p test-app .github/workflows

# Copy application files
cp /home/chandan/NeerOps/test-app/index.js test-app/
cp /home/chandan/NeerOps/test-app/package.json test-app/
cp /home/chandan/NeerOps/test-app/Dockerfile test-app/

# Copy workflow
cp /home/chandan/NeerOps/test-workflows/neerops-test-deployment.yaml .github/workflows/

# Verify files were copied
ls -la test-app/
ls -la .github/workflows/
```

**You should see:**
```
test-app/:
├── Dockerfile
├── index.js
└── package.json

.github/workflows/:
└── neerops-test-deployment.yaml
```

✅ **Step 3 Complete** when you see all files copied

---

### ✅ STEP 4: Create Configuration Files (2 min)

**What you're doing:** Creating README.md and .gitignore files for your repository.

**In Terminal, run these commands:**

```bash
cd ~/neerops-test

# Create README.md
cat > README.md << 'EOF'
# NeerOps v9 - Test Pipeline

Test repository to validate the complete NeerOps v9 CI/CD pipeline **before** deploying to production.

## 🎯 Purpose

This is a dummy application used to:
- ✅ Validate GitHub Actions workflows
- ✅ Test security gates (6 parallel scans)
- ✅ Verify Docker build process
- ✅ Confirm Canary gate evaluation
- ✅ Practice manual approval process

## 📁 Structure

```
.
├── test-app/              # Dummy Node.js HTTP server
│   ├── index.js
│   ├── package.json
│   └── Dockerfile
├── .github/workflows/     # GitHub Actions
│   └── neerops-test-deployment.yaml
└── README.md
```

## 🚀 How to Test

1. This repository has GitHub Actions enabled
2. Create a PR with any change
3. Watch the pipeline execute in "Actions" tab
4. Review the Canary Gate report in PR comments
5. Manually approve the deployment
6. Merge PR

## 📊 Pipeline Stages

- **L1:** Code Understanding (2 min)
- **L2:** Security Gates - 6 parallel scans (5 min)
- **L3:** Build & Push Docker image (8 min)
- **L4:** Canary Evaluation with manual approval (1 min)
- **Summary:** Final report (1 min)

**Total time: ~20 minutes**

## ⚠️ Important

- This is a TEST repository - no production deployment
- Manual approval is REQUIRED (no auto-approve)
- Safe to run multiple times
- All actions are logged and reviewable

## 📚 Documentation

See [TEST_DEPLOYMENT_GUIDE.md](../TEST_DEPLOYMENT_GUIDE.md) for complete instructions.

Generated for NeerOps v9 - May 2026
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
package-lock.json
yarn.lock

# Logs
*.log
npm-debug.log*
yarn-debug.log*

# Environment
.env
.env.local
.env.*.local

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Build
dist/
build/
EOF

# Verify files exist
echo "✅ Files created:"
ls -la
```

**You should see:**
```
README.md
.gitignore
test-app/
.github/
```

✅ **Step 4 Complete** when README.md and .gitignore are created

---

### ✅ STEP 5: Initialize Git and Push to GitHub (2 min)

**What you're doing:** Converting your local folder into a git repository and pushing it to GitHub.

**In Terminal, run these commands:**

```bash
cd ~/neerops-test

# Initialize git repository
git init

# Configure git (use your GitHub email/name)
git config user.email "your-email@example.com"
git config user.name "Your Name"

# Verify git is initialized
git status
# Should show: "On branch master" or "fatal: not a git repository (yet)"
```

**Now add all files:**

```bash
cd ~/neerops-test

# Add all files to git
git add .

# Verify files are staged
git status
# Should show: green "Changes to be committed" list

# Show what will be committed
git diff --cached --name-only
# Should show: all your files
```

**Create first commit:**

```bash
cd ~/neerops-test

git commit -m "Initial NeerOps v9 test setup"

# Verify commit
git log --oneline
# Should show: "Initial NeerOps v9 test setup" commit
```

**Connect to GitHub and push:**

```bash
cd ~/neerops-test

# Add GitHub as remote
# IMPORTANT: Replace YOUR_USERNAME with your actual GitHub username!
git remote add origin https://github.com/YOUR_USERNAME/neerops-test.git

# Verify remote is added
git remote -v
# Should show two lines with your GitHub URL

# Push to GitHub
git push -u origin main
# Should show: everything pushed successfully
```

**If you get an error about "main" branch:**

```bash
# Rename branch to main
git branch -M main

# Then push
git push -u origin main
```

✅ **Step 5 Complete** when git push succeeds without errors

---

## PHASE 2: VERIFICATION

### ✅ STEP 6: Verify Files on GitHub (2 min)

**What you're doing:** Checking that all files successfully uploaded to GitHub.

**In Web Browser:**

1. Go to `https://github.com/YOUR_USERNAME/neerops-test`
2. You should see this folder structure:
   ```
   📁 .github/
      └── 📁 workflows/
          └── neerops-test-deployment.yaml
   📁 test-app/
      ├── Dockerfile
      ├── index.js
      └── package.json
   📄 .gitignore
   📄 README.md
   ```
3. Scroll down and verify "Commits" shows "Initial NeerOps v9 test setup"

**Verify each file:**
- Click on `test-app/index.js` → Should show Node.js code
- Click on `test-app/Dockerfile` → Should show Docker config
- Click on `.github/workflows/neerops-test-deployment.yaml` → Should show GitHub Actions workflow

✅ **Step 6 Complete** when all files are visible on GitHub

---

### ✅ STEP 7: Check Workflows are Visible (2 min)

**What you're doing:** Confirming GitHub Actions is enabled and your workflow is registered.

**In Web Browser:**

1. On your repository page, click **"Actions"** tab (top navigation)
2. You should see:
   ```
   All workflows
   No workflows have run yet
   ```
3. Look for "neerops-test-deployment.yaml" listed (it may be empty since no PR created yet)

**If you see "Actions" disabled:**
1. Go to repository **Settings** → **Actions**
2. Under "Actions Permissions", select "Allow all actions and reusable workflows"
3. Click "Save"

✅ **Step 7 Complete** when Actions tab is visible and enabled

---

### ✅ STEP 8: Confirm Everything is Ready (1 min)

**Checklist - Mark each as ✅:**

- [ ] GitHub repository exists: `https://github.com/YOUR_USERNAME/neerops-test`
- [ ] All files visible on GitHub
- [ ] `.github/workflows/neerops-test-deployment.yaml` present
- [ ] `test-app/` folder with 3 files present
- [ ] `README.md` and `.gitignore` present
- [ ] Actions tab is enabled
- [ ] Commit history shows "Initial NeerOps v9 test setup"

**When all are checked:** ✅ **PHASE 1 & 2 COMPLETE - GitHub Setup Done!**

---

## PHASE 3: TESTING

### ✅ STEP 9: Create Test Branch (2 min)

**What you're doing:** Creating a separate branch for testing (don't modify main directly).

**In Terminal:**

```bash
cd ~/neerops-test

# Create and switch to new branch
git checkout -b feature/test-pipeline

# Verify you're on the new branch
git branch -a
# Should show: * feature/test-pipeline (with asterisk)
# Should show: main
```

✅ **Step 9 Complete** when `git branch` shows you on `feature/test-pipeline`

---

### ✅ STEP 10: Make a Small Change (2 min)

**What you're doing:** Making a change to trigger the GitHub Actions workflow.

**In Terminal:**

```bash
cd ~/neerops-test

# Add a comment to README
cat >> README.md << 'EOF'

## Test Deployment #1

- Date: $(date)
- Branch: feature/test-pipeline
- Purpose: Validate CI/CD pipeline

EOF

# Verify change
git diff
# Should show: additions to README.md
```

✅ **Step 10 Complete** when `git diff` shows your change

---

### ✅ STEP 11: Push and Create PR (3 min)

**What you're doing:** Pushing your branch to GitHub and creating a Pull Request to trigger workflows.

**In Terminal:**

```bash
cd ~/neerops-test

# Stage the change
git add README.md

# Commit the change
git commit -m "test: trigger CI/CD pipeline validation"

# Push to GitHub
git push -u origin feature/test-pipeline
# Should show: everything pushed successfully

# Verify on GitHub
echo "✅ Branch pushed! Go create PR on GitHub"
```

**In Web Browser:**

1. Go to `https://github.com/YOUR_USERNAME/neerops-test`
2. You should see a notification banner:
   ```
   Your recently pushed branches:
   feature/test-pipeline (Compare & pull request)
   ```
3. Click the green **"Compare & pull request"** button
4. Fill in PR details:
   - **Title:** `Test: Validate NeerOps v9 CI/CD Pipeline`
   - **Description:** `This PR tests the complete CI/CD workflow validation with manual approval.`
5. Click green **"Create pull request"** button

**After PR is created:**
- You'll see the PR page
- GitHub Actions should start automatically (might take 10-30 seconds)

✅ **Step 11 Complete** when PR is created and visible on GitHub

---

### ✅ STEP 12: Watch Pipeline Execute (20 min)

**What you're doing:** Monitoring the CI/CD pipeline as it runs through all stages.

**In Web Browser - PR Page:**

1. Click the **"Checks"** or **"Actions"** section (you'll see it in the PR)
2. Or click the **"Actions"** tab at top of repository
3. You should see: **"NeerOps v9 Test Pipeline"** job running

**Timeline - Watch these stages execute:**

| Time | Stage | Status | What It Does |
|------|-------|--------|---|
| 0-2 min | L1 - Code Understanding | ⏳ Running | Analyzes your git diff |
| 2-7 min | L2 - Security Gates | ⏳ Running | 6 scans in parallel (gitleaks, semgrep, trivy, etc.) |
| 7-15 min | L3 - Build & Push | ⏳ Running | Docker build, image scan, push to registry |
| 15-16 min | L4 - Canary Evaluation | ⏳ Running | Canary gate analysis (NO auto-approve) |
| 16-17 min | Summary | ⏳ Running | Final report |
| 17+ min | ✅ All Complete | Report posted to PR | See Canary Report in PR comments |

**What to see in Actions tab:**

```
✅ understanding (2 min)        ← Code Understanding
✅ security-gates (5 min)       ← Security Scans
✅ build (8 min)                ← Docker Build
✅ canary-evaluation (1 min)    ← Canary Gate
✅ summary (1 min)              ← Final Report
```

**All should have GREEN checkmarks ✅**

✅ **Step 12 Complete** when you see "All checks passed" or similar message

---

### ✅ STEP 13: Monitor All Stages (L1-L4) (Passive - just watch)

**What you're doing:** Reviewing what each stage does (purely informational).

**In Actions tab, click on each job to see its logs:**

**L1 - Code Understanding:**
```
✅ Shows git diff analysis
✅ Lists changed files
✅ Builds knowledge graph
```

**L2 - Security Gates (6 parallel jobs):**
```
✅ Gitleaks     → Scans for secrets
✅ Semgrep      → Scans code for security issues
✅ Trivy FS     → Scans filesystem for CVEs
✅ Trivy Config → Scans config files
✅ Bandit       → Python-specific security check
✅ Hadolint     → Docker linting
```

**L3 - Build & Push:**
```
✅ Sets up Docker buildx
✅ Extracts image metadata
✅ Builds Docker image
✅ Scans built image for vulnerabilities
✅ Pushes to container registry (GitHub)
```

**L4 - Canary Evaluation:**
```
✅ Calculates Bayesian probability
✅ Evaluates canary gate (P ≥ 95%)
✅ Generates metrics report
✅ Posts report to PR comments
✅ STATUS: PENDING MANUAL REVIEW (you must approve)
```

✅ **Step 13 Complete** when you've reviewed one job's logs

---

### ✅ STEP 14: Review Canary Report (5 min)

**What you're doing:** Reading the Canary Gate Report that appears in your PR comments.

**In Web Browser - PR Page:**

1. Scroll down to "Conversation" tab
2. Look for comment from "github-actions" bot that says:
   ```
   🎲 NeerOps Canary Gate Report
   Status: ⏳ PENDING MANUAL REVIEW (No Auto-Approval)
   ```

3. The report will show:
   ```
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
   🔍 MANUAL REVIEW REQUIRED before proceeding
   - [ ] Reviewer: Verify metrics are acceptable
   - [ ] Reviewer: Check error logs
   - [ ] Reviewer: Confirm no regressions
   - [ ] Reviewer: Approve/Reject deployment
   ```

**What this means:**
- ✅ All security gates passed
- ✅ Docker built successfully
- ✅ Metrics show improvement
- ⏳ **Waiting for YOUR manual approval**

✅ **Step 14 Complete** when you've read the Canary Report

---

## PHASE 4: MANUAL APPROVAL

### ✅ STEP 15: Review Metrics in Report (3 min)

**What you're doing:** Analyzing the metrics to decide if it's safe to approve.

**Review these metrics from the Canary Report:**

| Metric | Current | Baseline | Status | Your Check |
|--------|---------|----------|--------|-----------|
| Error Rate | 0.2% | 0.5% | ✅ Better (60% improvement) | [ ] OK |
| Latency P99 | 145ms | 150ms | ✅ Better (3% improvement) | [ ] OK |
| CPU Usage | 25% | - | ✅ Reasonable | [ ] OK |
| Memory | 512MB | - | ✅ Reasonable | [ ] OK |
| Throughput | 1200/s | - | ✅ Good | [ ] OK |
| Bayesian P | 96.0% | 95% | ✅ Passes | [ ] OK |

**Security Gates (all should be ✅):**
- [ ] ✅ Gitleaks - No secrets exposed
- [ ] ✅ Semgrep - No code issues
- [ ] ✅ Trivy - No CVEs
- [ ] ✅ Bandit - No Python issues
- [ ] ✅ Hadolint - Dockerfile OK

**When all are checked:** You're ready to approve!

✅ **Step 15 Complete** when you've verified all metrics

---

### ✅ STEP 16: Manually Approve in PR (2 min)

**What you're doing:** Explicitly approving the deployment through GitHub's PR review system.

**In Web Browser - PR Page:**

1. Scroll to top of PR
2. Look for a button that says:
   - **"Review changes"** (if visible), or
   - **"Approve"** button, or
   - A green thumbs-up icon

3. Click **"Review changes"** button
4. A dialog will appear with three options:
   - **Comment** (leave feedback, don't approve)
   - **Approve** (✅ select this one)
   - **Request changes** (reject, ask for changes)

5. Select **"Approve"** radio button
6. In the comment box, write something like:
   ```
   Approving this test deployment.
   
   Metrics look good:
   ✅ Error rate improved 60%
   ✅ Latency improved 3%
   ✅ All security gates passing
   ✅ No regressions detected
   
   Ready to proceed!
   ```

7. Click green **"Submit review"** button

**After approval:**
- PR will show green checkmark in header: "You approved this pull request"
- The Canary Report comment will update to show your approval

✅ **Step 16 Complete** when you've submitted your approval review

---

### ✅ STEP 17: Confirm Success (2 min)

**What you're doing:** Verifying that your approval was recorded and the test completed successfully.

**Checklist:**

- [ ] PR page shows: "You approved this pull request" (green)
- [ ] Canary Report comment shows your approval review
- [ ] All workflow jobs show green checkmarks ✅
- [ ] No workflow jobs show red ❌
- [ ] Actions tab shows: "All checks passed"
- [ ] PR is ready to merge (green merge button visible)

**Take a screenshot or note:**
```
✅ TEST PIPELINE VALIDATION - SUCCESSFUL

Completed steps:
✅ L1: Code Understanding
✅ L2: Security Gates (6 scans)
✅ L3: Build & Push
✅ L4: Canary Evaluation
✅ Manual Approval (YOU approved)

No automatic deployment occurred (test only).
This confirms the entire workflow functions correctly!
```

**Optional - Merge the PR:**

If you want to clean up, you can:
1. Click green **"Merge pull request"** button
2. Confirm the merge
3. Delete the branch (optional)

✅ **Step 17 Complete** when you've verified all steps worked!

---

## 🎊 TEST COMPLETE!

**Summary of what you've accomplished:**

```
✅ Created GitHub repository (neerops-test)
✅ Pushed dummy application to GitHub
✅ Created test PR
✅ Triggered GitHub Actions workflow
✅ Watched L1→L2→L3→L4 execute (25 min)
✅ Reviewed Canary Gate Report
✅ Manually approved deployment
✅ Validated entire CI/CD pipeline works
✅ Confirmed manual approval process functions
```

**What this proves:**

✓ Your GitHub Actions workflows are correctly configured  
✓ All 6 security gates execute properly  
✓ Docker build process works  
✓ Canary metrics are calculated accurately  
✓ Reports are posted to PRs  
✓ Manual approval process is in place  
✓ YOU have full control (no auto-approve surprises)  

---

## 🚀 NEXT STEPS

### Option A: Test Again (Practice)
If you want to run through the test one more time:
1. Create another branch (`feature/test-2`)
2. Make a different change
3. Create another PR
4. Watch workflow again
5. This confirms consistency

### Option B: Proceed to Production
When ready to deploy the real NeerOps v9 application:
1. Read **GITHUB_SETUP_GUIDE.md** (create new repo for production)
2. Follow **QUICK_START_DEPLOYMENT.md** (deploy to Kubernetes)
3. Deploy full NeerOps v9 framework

### Option C: Modify Workflows
If you want to customize the pipeline:
1. Edit `.github/workflows/neerops-test-deployment.yaml`
2. Make changes
3. Push to feature branch
4. Create PR to test changes
5. Iterate until satisfied

---

## 📞 Troubleshooting

### Workflow Doesn't Trigger
**Problem:** No jobs appear in Actions after PR creation  
**Solution:**
- Wait 30 seconds (GitHub needs time to register)
- Refresh the page (F5)
- Check `.github/workflows/neerops-test-deployment.yaml` exists on GitHub

### All Jobs Failed (Red ❌)
**Problem:** Every job shows as failed  
**Solution:**
- Click on a failed job to see error logs
- Common issues:
  - Docker build failed → Check Dockerfile syntax
  - Security scan failed → May need to fix issues found
  - Network error → GitHub infrastructure issue (rare)

### Can't See Canary Report
**Problem:** No comment from github-actions bot  
**Solution:**
- Wait for L4 - Canary Evaluation to complete (check Actions tab)
- Refresh PR page (F5)
- Scroll down to see all comments
- Check workflow log for errors

### Git Push Fails
**Problem:** `git push` command gives error  
**Solution:**
```bash
# Check remote URL
git remote -v

# If wrong, fix it
git remote set-url origin https://github.com/YOUR_USERNAME/neerops-test.git

# Try push again
git push -u origin feature/test-pipeline
```

---

## 📊 Quick Reference Commands

```bash
# Setup
mkdir ~/neerops-test && cd ~/neerops-test
git init
git config user.email "your@email.com"
git config user.name "Your Name"

# Copy files
cp -r /home/chandan/NeerOps/test-app ./test-app/
cp -r /home/chandan/NeerOps/test-workflows/* .github/workflows/

# Push to GitHub
git add .
git commit -m "Initial test setup"
git remote add origin https://github.com/YOUR_USERNAME/neerops-test.git
git push -u origin main

# Create test PR
git checkout -b feature/test-pipeline
echo "test" >> README.md
git add README.md
git commit -m "test: validate pipeline"
git push -u origin feature/test-pipeline
```

---

## ✨ Summary

| Phase | Time | What | Status |
|-------|------|------|--------|
| **1: Setup** | 10 min | Create repo, push code | ✅ Automated |
| **2: Verify** | 5 min | Check files on GitHub | ✅ Manual check |
| **3: Test** | 25 min | Run pipeline | ✅ Automatic (you watch) |
| **4: Approve** | 5 min | Manual approval | ✅ Manual (you click) |
| **TOTAL** | **45 min** | Complete validation | **✅ DONE** |

---

**When you complete all 17 steps, your CI/CD pipeline is validated and ready!** 🎉

Next: Deploy production NeerOps v9 to Kubernetes.

Generated: May 14, 2026  
NeerOps v9 - Complete Step-by-Step Testing Guide
