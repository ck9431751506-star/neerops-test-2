# 🚀 NeerOps v9 Deployment - Quick Start Guide

**Get from zero to deployed NeerOps v9 + GitHub CI/CD in 2-3 hours**

---

## 📋 Prerequisites Checklist

Before you start, verify you have:

- ✅ **System specs reviewed:** 4 CPU, 9.6 GB RAM, 112 GB free disk
- ✅ **k3s running:** Kubernetes cluster available
- ✅ **Docker installed:** Docker version 28.2.2+
- ✅ **GitHub account:** Ready to create repository
- ✅ **GitHub CLI installed:** `gh` command available (optional but recommended)

---

## 🎯 Step 1: Prepare Environment (10 min)

### 1.1 Clean up terminating namespaces

```bash
# Check current namespaces
kubectl get ns -o wide

# Wait for online-boutique to finish terminating
kubectl get ns -w | grep online-boutique

# Should see this eventually:
# (no online-boutique)
```

### 1.2 Free up system resources

```bash
# Option A: Close VS Code (frees ~6% memory)
# Option B: Stop unnecessary services
sudo systemctl stop docker   # Temporarily
sudo systemctl stop kubelet  # Temporarily (if not k3s)

# Or just reduce to essential processes
```

### 1.3 Create NeerOps namespace

```bash
kubectl create namespace neerops
kubectl label namespace neerops version=v9.0
```

---

## 📦 Step 2: Clone & Setup Repository (5 min)

### 2.1 Create local repository structure

```bash
# Create working directory
cd ~ && mkdir neerops-deployment && cd neerops-deployment

# Initialize git
git init
git config user.name "Your Name"
git config user.email "your-email@github.com"

# Create directory structure
mkdir -p .github/workflows
mkdir -p kubernetes/{services,configs}
mkdir -p src/{app,neerops/{layers,core}}
mkdir -p tests/{unit,integration}
```

### 2.2 Copy NeerOps documentation to repository

```bash
# Copy from /home/chandan/NeerOps/
cp /home/chandan/NeerOps/NEEROPS_V9_ARCHITECTURE.md .
cp /home/chandan/NeerOps/NEEROPS_V9_IMPLEMENTATION.md .
cp /home/chandan/NeerOps/GITHUB_CICD_PIPELINE.md .

# Create README
cat > README.md << 'EOF'
# NeerOps v9 Deployment

Goal-centric autonomous DevOps with real-time healing and LLMOps integration.

## Quick Start

1. Create namespace: `kubectl create namespace neerops`
2. Deploy infrastructure: `kubectl apply -f kubernetes/`
3. Submit PR to trigger pipeline

## Documentation

- [Architecture](NEEROPS_V9_ARCHITECTURE.md)
- [Implementation](NEEROPS_V9_IMPLEMENTATION.md)
- [CI/CD Pipeline](GITHUB_CICD_PIPELINE.md)
EOF
```

---

## 🔧 Step 3: Create Kubernetes Manifests (15 min)

### 3.1 Create NeerOps infrastructure deployment

```bash
cat > kubernetes/neerops-infrastructure.yaml << 'EOF'
---
# Redis (Event Bus)
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
  namespace: neerops
data:
  redis.conf: |
    appendonly yes
    appendfsync everysec
    maxmemory 256mb
    maxmemory-policy allkeys-lru

---
apiVersion: v1
kind: Pod
metadata:
  name: redis-dev
  namespace: neerops
  labels:
    app: redis
spec:
  containers:
  - name: redis
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    ports:
    - containerPort: 6379
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
    volumeMounts:
    - name: redis-storage
      mountPath: /data
  volumes:
  - name: redis-storage
    emptyDir: {}

---
# Redis Service
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: neerops
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP

---
# PostgreSQL (State Store)
apiVersion: v1
kind: Pod
metadata:
  name: postgres-dev
  namespace: neerops
  labels:
    app: postgres
spec:
  containers:
  - name: postgres
    image: postgres:15-alpine
    env:
    - name: POSTGRES_PASSWORD
      value: "neerops-dev"
    - name: POSTGRES_DB
      value: "neerops"
    ports:
    - containerPort: 5432
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
    volumeMounts:
    - name: postgres-storage
      mountPath: /var/lib/postgresql/data
  volumes:
  - name: postgres-storage
    emptyDir: {}

---
# PostgreSQL Service
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: neerops
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP

---
# Prometheus (Metrics)
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: neerops
data:
  prometheus.yaml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    scrape_configs:
    - job_name: 'kubernetes-apiservers'
      kubernetes_sd_configs:
      - role: endpoints
      relabel_configs:
      - source_labels: [__meta_kubernetes_namespace]
        action: keep
        regex: default|kube-system

---
apiVersion: v1
kind: Pod
metadata:
  name: prometheus-dev
  namespace: neerops
  labels:
    app: prometheus
spec:
  containers:
  - name: prometheus
    image: prom/prometheus:latest
    args:
    - "--config.file=/etc/prometheus/prometheus.yaml"
    - "--storage.tsdb.path=/prometheus"
    ports:
    - containerPort: 9090
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "200m"
    volumeMounts:
    - name: prometheus-config
      mountPath: /etc/prometheus
    - name: prometheus-storage
      mountPath: /prometheus
  volumes:
  - name: prometheus-config
    configMap:
      name: prometheus-config
  - name: prometheus-storage
    emptyDir: {}

---
# Prometheus Service
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: neerops
spec:
  selector:
    app: prometheus
  ports:
  - port: 9090
    targetPort: 9090
  type: ClusterIP
EOF
```

### 3.2 Create NeerOps layers deployment

```bash
cat > kubernetes/neerops-layers.yaml << 'EOF'
---
# L0 Cognition
apiVersion: v1
kind: Pod
metadata:
  name: l0-cognition
  namespace: neerops
  labels:
    layer: l0
spec:
  containers:
  - name: cognition
    image: python:3.11-slim
    command: ["python", "-c", "print('L0 Cognition Running')"]
    resources:
      requests:
        memory: "100Mi"
        cpu: "50m"
      limits:
        memory: "200Mi"
        cpu: "100m"

---
# L5 Monitor
apiVersion: v1
kind: Pod
metadata:
  name: l5-monitor
  namespace: neerops
  labels:
    layer: l5
spec:
  containers:
  - name: monitor
    image: python:3.11-slim
    command: ["python", "-c", "print('L5 Monitor Running')"]
    resources:
      requests:
        memory: "100Mi"
        cpu: "50m"
      limits:
        memory: "200Mi"
        cpu: "100m"

---
# L6 Healing
apiVersion: v1
kind: Pod
metadata:
  name: l6-healing
  namespace: neerops
  labels:
    layer: l6
spec:
  containers:
  - name: healing
    image: python:3.11-slim
    command: ["python", "-c", "print('L6 Healing Running')"]
    resources:
      requests:
        memory: "100Mi"
        cpu: "50m"
      limits:
        memory: "200Mi"
        cpu: "100m"

---
# L8 World Model
apiVersion: v1
kind: Pod
metadata:
  name: l8-world-model
  namespace: neerops
  labels:
    layer: l8
spec:
  containers:
  - name: world-model
    image: python:3.11-slim
    command: ["python", "-c", "print('L8 World Model Running')"]
    resources:
      requests:
        memory: "100Mi"
        cpu: "50m"
      limits:
        memory: "200Mi"
        cpu: "100m"
EOF
```

### 3.3 Create minimal Online Boutique deployment

```bash
cat > kubernetes/online-boutique-minimal.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: boutique

---
# Frontend
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: boutique
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: gcr.io/google-samples/microservices-demo/frontend:v0.3.9
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"

---
# Frontend Service
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: boutique
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer

---
# CartService
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cartservice
  namespace: boutique
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cartservice
  template:
    metadata:
      labels:
        app: cartservice
    spec:
      containers:
      - name: cartservice
        image: gcr.io/google-samples/microservices-demo/cartservice:v0.3.9
        ports:
        - containerPort: 7070
        resources:
          requests:
            memory: "200Mi"
            cpu: "100m"
          limits:
            memory: "400Mi"
            cpu: "200m"

---
# CartService Service
apiVersion: v1
kind: Service
metadata:
  name: cartservice
  namespace: boutique
spec:
  selector:
    app: cartservice
  ports:
  - port: 7070
    targetPort: 7070
  type: ClusterIP

---
# ProductCatalog
apiVersion: apps/v1
kind: Deployment
metadata:
  name: productcatalogservice
  namespace: boutique
spec:
  replicas: 1
  selector:
    matchLabels:
      app: productcatalogservice
  template:
    metadata:
      labels:
        app: productcatalogservice
    spec:
      containers:
      - name: productcatalogservice
        image: gcr.io/google-samples/microservices-demo/productcatalogservice:v0.3.9
        ports:
        - containerPort: 3550
        resources:
          requests:
            memory: "200Mi"
            cpu: "100m"
          limits:
            memory: "400Mi"
            cpu: "200m"

---
# ProductCatalog Service
apiVersion: v1
kind: Service
metadata:
  name: productcatalogservice
  namespace: boutique
spec:
  selector:
    app: productcatalogservice
  ports:
  - port: 3550
    targetPort: 3550
  type: ClusterIP
EOF
```

---

## 🐙 Step 4: Create GitHub Repository (5 min)

### 4.1 Create repo on GitHub

```bash
# Option A: Using GitHub Web UI
# 1. Go to https://github.com/new
# 2. Name: "neerops-deployment"
# 3. Description: "NeerOps v9 autonomous DevOps platform"
# 4. Public
# 5. Create repository

# Option B: Using GitHub CLI
gh repo create neerops-deployment --public --source=. --remote=origin --push
```

### 4.2 Add CI/CD workflows

```bash
# Copy CI/CD workflow from documentation
cat > .github/workflows/neerops-deployment.yaml << 'EOF'
[Paste content from GITHUB_CICD_PIPELINE.md - neerops-deployment.yaml section]
EOF

# Commit and push
git add .github/workflows/
git commit -m "Add NeerOps CI/CD workflows"
git push origin main
```

---

## 🔐 Step 5: Configure GitHub Secrets (5 min)

```bash
# Create secrets for CI/CD pipeline
gh secret set GITLEAKS_LICENSE --body "free"
gh secret set LLM_API_KEY --body "sk-test" # Use real key in production
gh secret set REGISTRY_TOKEN --body "$(echo -n 'token' | base64)"

# Verify secrets
gh secret list
```

---

## 🚀 Step 6: Deploy to Kubernetes (10 min)

### 6.1 Deploy NeerOps infrastructure

```bash
kubectl apply -f kubernetes/neerops-infrastructure.yaml

# Wait for pods
kubectl get pods -n neerops -w

# Expected output:
# NAME              READY   STATUS    RESTARTS   AGE
# redis-dev         1/1     Running   0          10s
# postgres-dev      1/1     Running   0          10s
# prometheus-dev    1/1     Running   0          10s
```

### 6.2 Deploy NeerOps layers

```bash
kubectl apply -f kubernetes/neerops-layers.yaml

# Verify layers
kubectl get pods -n neerops -l layer=
```

### 6.3 Deploy application

```bash
kubectl apply -f kubernetes/online-boutique-minimal.yaml

# Wait for application
kubectl get pods -n boutique -w

# Get access URL
kubectl get svc -n boutique
# NAME       TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)
# frontend   LoadBalancer   10.43.x.x     <pending>     80:3xxxx/TCP
```

---

## ✅ Step 7: Test the Pipeline (10 min)

### 7.1 Create feature branch

```bash
git checkout -b feature/test-pipeline
echo "# Test NeerOps Pipeline" >> README.md
git add .
git commit -m "Test NeerOps pipeline trigger"
git push origin feature/test-pipeline
```

### 7.2 Create Pull Request

```bash
# Via web UI: https://github.com/your-user/neerops-deployment/pull/new/feature/test-pipeline
# Or via CLI:
gh pr create --title "Test NeerOps pipeline" --body "Testing CI/CD workflow"
```

### 7.3 Monitor Actions

```bash
# Watch GitHub Actions
gh run list

# Or view in web UI:
# https://github.com/your-user/neerops-deployment/actions
```

---

## 📊 Step 8: Verify Deployment (5 min)

```bash
# Check all components
echo "=== NeerOps Status ===" && \
kubectl get pods -n neerops && \
echo "" && echo "=== Application Status ===" && \
kubectl get pods -n boutique && \
echo "" && echo "=== Services ===" && \
kubectl get svc -A

# Check logs
kubectl logs -n neerops l0-cognition
kubectl logs -n boutique -f deployment/frontend

# Access services
# Frontend: kubectl port-forward -n boutique svc/frontend 8080:80
# Prometheus: kubectl port-forward -n neerops svc/prometheus 9090:9090
```

---

## 🎯 Success Criteria

You'll know it's working when:

- ✅ All 5 NeerOps pods running in `neerops` namespace
- ✅ All application pods running in `boutique` namespace
- ✅ GitHub Actions workflows complete successfully
- ✅ Frontend accessible at localhost:8080 (via port-forward)
- ✅ Prometheus metrics available
- ✅ PR shows canary deployment results

---

## 🐛 Troubleshooting

### Pod won't start
```bash
kubectl describe pod <pod-name> -n neerops
kubectl logs <pod-name> -n neerops
```

### Namespace terminating
```bash
kubectl get namespace online-boutique -o yaml | grep finalizers
# Remove finalizer if stuck:
kubectl patch namespace online-boutique -p '{"metadata":{"finalizers":null}}'
```

### GitHub Actions failing
```bash
# Check workflow logs in GitHub UI
# Settings → Actions → Workflows → [workflow name]
```

### Out of memory
```bash
# Check resource usage
kubectl top nodes
kubectl top pods -A

# Reduce replicas or increase resource limits
```

---

## 📖 Next Steps

1. **Review documentation:**
   - Read [NEEROPS_V9_ARCHITECTURE.md](NEEROPS_V9_ARCHITECTURE.md)
   - Study [NEEROPS_V9_IMPLEMENTATION.md](NEEROPS_V9_IMPLEMENTATION.md)

2. **Customize for your app:**
   - Replace `online-boutique-minimal.yaml` with your app
   - Update CI/CD workflows with your build steps

3. **Set up monitoring:**
   - Configure alert rules in Prometheus
   - Set up dashboard in Grafana

4. **Enable security gates:**
   - Configure Gitleaks API key
   - Set up Trivy registration token
   - Enable ZAP scanning

5. **Production readiness:**
   - Set up HA Orchestrator (2 replicas)
   - Deploy full Redis Sentinel (3 nodes)
   - Set up Vault cluster (3 nodes)
   - Enable QLDB for audit logs

---

## 📞 Support

For issues or questions:
- Check documentation files
- Review Kubernetes events: `kubectl get events -A --sort-by='.lastTimestamp'`
- Check container logs: `kubectl logs -n neerops <pod>`

---

**Status:** ✅ Ready to Deploy  
**Estimated Time:** 2-3 hours  
**Next:** Follow steps 1-8 above
