# NEEROps v9.0 - Production Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Configuration](#configuration)
6. [Integration](#integration)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Python 3.11+
- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.24+ (for K8s deployment)
- kubectl 1.24+ (for K8s management)

### System Requirements
- **Minimum:** 2 CPU, 4GB RAM
- **Recommended:** 4 CPU, 8GB RAM (production)
- **Disk:** 20GB minimum

### Required Services (Production)
- Redis 7.0+ (Event Bus)
- PostgreSQL 15+ (Heuristic Library)
- HashiCorp Vault 1.13+ (Secrets)
- Jaeger 1.35+ (Tracing)
- Kubernetes cluster (for orchestration)

---

## Local Development

### 1. Clone Repository
```bash
git clone https://github.com/your-org/neerops.git
cd neerops/neerops_platform
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment
```bash
cp .env.example .env
# Edit .env with local settings
```

### 5. Run Tests
```bash
python tests.py
```

### 6. Start Platform
```bash
python cli.py start
```

### 7. Process Test PR
```bash
python cli.py pr --id test-001 --title "Feature X" --branch main
```

---

## Docker Deployment

### Local Development with Docker Compose

#### 1. Build Image
```bash
docker build -t neerops:latest .
```

#### 2. Start Services
```bash
docker-compose up -d
```

This starts:
- Redis (Event Bus)
- PostgreSQL (Heuristics)
- Vault (Secrets)
- Jaeger (Tracing)
- NEEROps platform

#### 3. Verify Services
```bash
docker-compose ps
docker-compose logs -f neerops
```

#### 4. Access Services
- NEEROps API: http://localhost:8000
- Jaeger UI: http://localhost:16686
- Vault UI: http://localhost:8200 (token: devtoken)
- Redis: localhost:6379

#### 5. Process PR
```bash
docker-compose exec neerops python cli.py pr \
  --id test-001 \
  --title "Feature X" \
  --branch main
```

#### 6. Cleanup
```bash
docker-compose down -v  # -v removes volumes
```

---

## Kubernetes Deployment

### 1. Prerequisites
- K8s cluster running (minikube, EKS, GKE, etc.)
- kubectl configured
- Docker registry access (for custom image)

### 2. Build and Push Image
```bash
# Tag image
docker tag neerops:latest your-registry/neerops:v9.0.0

# Push to registry
docker push your-registry/neerops:v9.0.0
```

### 3. Update Image in Manifests
```bash
sed -i 's|neerops:latest|your-registry/neerops:v9.0.0|g' kubernetes/deployment.yaml
```

### 4. Deploy to Kubernetes
```bash
# Create namespace and deploy
kubectl apply -f kubernetes/deployment.yaml

# Verify deployment
kubectl get pods -n neerops
kubectl get svc -n neerops
```

### 5. Check Deployment Status
```bash
# Watch rollout
kubectl rollout status deployment/neerops -n neerops

# View logs
kubectl logs -f deployment/neerops -n neerops

# Describe deployment
kubectl describe deployment neerops -n neerops
```

### 6. Access Services
```bash
# Port forward to NEEROps
kubectl port-forward -n neerops svc/neerops-service 8000:8000

# Port forward to Jaeger
kubectl port-forward -n neerops svc/jaeger-service 16686:16686

# Now accessible at:
# - http://localhost:8000 (NEEROps)
# - http://localhost:16686 (Jaeger UI)
```

### 7. Scale Deployment
```bash
# Manual scaling
kubectl scale deployment neerops -n neerops --replicas=5

# HPA will auto-scale based on CPU/memory
# Min: 3 replicas, Max: 10 replicas
```

### 8. Update Deployment
```bash
# Update image
kubectl set image deployment/neerops \
  neerops=your-registry/neerops:v9.0.1 \
  -n neerops

# Monitor rollout
kubectl rollout status deployment/neerops -n neerops

# Rollback if needed
kubectl rollout undo deployment/neerops -n neerops
```

### 9. Cleanup
```bash
kubectl delete namespace neerops
```

---

## Configuration

### Environment Variables

Create `.env` file with:

```bash
# Application
DEBUG=False
LOG_LEVEL=INFO

# Event Bus
EVENT_BUS_TYPE=redis         # mock | redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Vault
VAULT_TYPE=hashicorp         # mock | hashicorp
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=devtoken

# OTEL Tracing
OTEL_TYPE=jaeger             # mock | jaeger
JAEGER_HOST=localhost
JAEGER_PORT=6831

# Database
QLDB_TYPE=mock               # mock | aws
QLDB_LEDGER_NAME=neerops-ledger

# Deployment
CANARY_TIMEOUT_MINUTES=45
GATE_P_SUCCESS_MIN=0.95

# LLM Configuration
LLM_PROVIDER=openai          # mock | openai | claude
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Feature Flags
FEATURE_RL_TRAINING=True
FEATURE_PROMPT_EVOLUTION=True
SUPERVISOR_ENABLED=True

# Kubernetes
K8S_ENABLED=False
K8S_NAMESPACE=neerops
```

### ConfigMap & Secrets (Kubernetes)

```bash
# Create ConfigMap
kubectl create configmap neerops-config \
  --from-file=.env \
  -n neerops

# Create Secret
kubectl create secret generic neerops-secrets \
  --from-literal=VAULT_TOKEN=devtoken \
  --from-literal=OPENAI_API_KEY=sk-... \
  -n neerops
```

---

## Integration

### GitHub Webhook Setup

1. **Create Webhook** in GitHub repo settings:
   - URL: `https://your-domain.com/webhook/github`
   - Content type: `application/json`
   - Events: Pull requests, Push
   - Secret: Generate and configure in `.env` as `GITHUB_WEBHOOK_SECRET`

2. **Configure NEEROps** to accept webhooks:
   ```python
   # In main.py, add webhook listener
   from flask import Flask
   app = Flask(__name__)
   
   @app.route('/webhook/github', methods=['POST'])
   def github_webhook():
       payload = request.get_json()
       platform.handle_pr_webhook(payload)
       return {"status": "ok"}
   
   if __name__ == "__main__":
       app.run(host="0.0.0.0", port=8000)
   ```

### Slack Notifications

Configure in `.env`:
```bash
ALERT_CHANNELS=slack
SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

### PagerDuty Escalation

Configure in `.env`:
```bash
PAGERDUTY_TOKEN=<token>
ALERT_CHANNELS=pagerduty
```

---

## Monitoring

### Prometheus Metrics

Add Prometheus scrape job:
```yaml
scrape_configs:
  - job_name: 'neerops'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
```

### Jaeger Distributed Tracing

Access Jaeger UI at http://localhost:16686

- Select "neerops" service
- View traces for PR deployments
- Analyze layer execution times

### Application Logs

```bash
# Docker
docker logs neerops

# Kubernetes
kubectl logs -f deployment/neerops -n neerops

# Local file
tail -f /var/log/neerops/app.log
```

### Health Checks

```bash
# CLI health check
python cli.py health

# HTTP health check
curl http://localhost:8000/health

# Kubernetes probe
kubectl exec -it <pod-name> -n neerops -- \
  python -c "from config import Config; print('OK' if Config.validate() else 'FAIL')"
```

---

## Troubleshooting

### Issue: Redis Connection Failed

```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli -h localhost -p 6379 PING

# Solution: Start Redis
docker-compose up redis
```

### Issue: Vault Authentication Failed

```bash
# Check Vault token
echo $VAULT_TOKEN

# Verify Vault is running
curl http://localhost:8200/v1/sys/health

# Solution: Update VAULT_TOKEN in .env
export VAULT_TOKEN=devtoken
```

### Issue: Kubernetes Pod CrashLoopBackOff

```bash
# Check pod logs
kubectl logs <pod-name> -n neerops

# Describe pod
kubectl describe pod <pod-name> -n neerops

# Common causes:
# 1. Image pull failed - check image registry
# 2. ConfigMap/Secret missing - create them
# 3. Resource limits - increase limits in deployment
```

### Issue: High Memory Usage

```bash
# Check resource usage
kubectl top pods -n neerops

# Increase limits in deployment.yaml
resources:
  limits:
    memory: 2Gi

# Apply update
kubectl apply -f kubernetes/deployment.yaml
```

### Issue: Tests Failing

```bash
# Run tests with verbose output
python tests.py -v

# Run specific test class
python -m pytest tests.py::TestCore -v

# Run with coverage
pytest tests.py --cov=core --cov=layers
```

---

## Production Checklist

- [ ] All services deployed and healthy
- [ ] Database backups configured
- [ ] Secret rotation enabled (Vault)
- [ ] Monitoring and alerting active
- [ ] Log aggregation configured
- [ ] Disaster recovery plan tested
- [ ] Load testing completed (>100 PR/hour)
- [ ] Security scanning enabled (Gitleaks, Semgrep, Trivy)
- [ ] RL training pipeline running
- [ ] Supervisor health checks active
- [ ] GitHub webhook configured
- [ ] Slack/PagerDuty notifications working

---

## Performance Tuning

### Redis Optimization
```bash
# Increase max connections
redis-cli CONFIG SET maxclients 10000

# Enable persistence
redis-cli CONFIG SET save "60 1000"
```

### PostgreSQL Optimization
```sql
-- Connection pooling
-- CREATE USER neerops_pool WITH PASSWORD '...';
-- ALTER ROLE neerops_pool SET maintenance_work_mem = 1GB;

-- Index optimization
CREATE INDEX idx_heuristics_confidence ON heuristics(confidence DESC);
CREATE INDEX idx_trajectories_date ON trajectories(collected_at DESC);
```

### Application Tuning
```bash
# Set in .env
MONITOR_METRICS_WINDOW=20        # Reduce for faster anomaly detection
HEALING_HEURISTIC_MIN=0.5        # Lower = more aggressive heuristic use
LLM_RATE_LIMIT_PER_MINUTE=5      # Increase for higher LLM budget
```

---

## Support

For issues or questions:
1. Check [README.md](README.md)
2. Review [IMPLEMENTATION.md](IMPLEMENTATION.md)
3. Check logs: `docker-compose logs neerops`
4. Open GitHub issue with logs and config

---

**Version:** 9.0.0  
**Last Updated:** 2024  
**Status:** Production Ready ✓
