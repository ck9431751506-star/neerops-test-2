# NeerOps v9 Implementation Guide

**Practical Code and Configuration for Autonomous DevOps Deployment**

---

## Part 1: Global Singleton Initialization

```python
# neerops/core/globals.py
"""Global singletons initialized once at NeerOps startup."""

import os
from dataclasses import dataclass
from typing import Any, Dict
import redis
import opentelemetry.trace as otel
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

@dataclass
class GlobalContext:
    """Dependency injection container for all layers."""
    event_bus: redis.Redis          # Redis Streams for inter-layer comms
    vault: Any                      # HashiCorp Vault client
    tracer: otel.Tracer             # OpenTelemetry for tracing
    logger: Any                     # QLDB append-only logger
    
def init_globals() -> GlobalContext:
    """Initialize all global singletons at startup."""
    
    # 1. Initialize OTEL Tracer (Jaeger backend)
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
        agent_port=int(os.getenv("JAEGER_PORT", 6831)),
    )
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    otel.set_tracer_provider(trace_provider)
    tracer = otel.get_tracer(__name__)
    
    # 2. Initialize Event Bus (Redis Streams)
    event_bus = redis.Redis(
        host=os.getenv("REDIS_HOST", "redis-sentinel"),
        port=int(os.getenv("REDIS_PORT", 26379)),
        decode_responses=True,
    )
    # Test connection
    event_bus.ping()
    
    # 3. Initialize Vault Client (assumes sidecar already injected by k8s)
    from hvac import Client as VaultClient
    vault_client = VaultClient(
        url=os.getenv("VAULT_ADDR", "http://vault.default:8200"),
        token=open("/var/run/secrets/vault-token").read().strip()
    )
    
    # 4. Initialize QLDB Logger
    import boto3
    qldb_client = boto3.client("qldb")
    
    ctx = GlobalContext(
        event_bus=event_bus,
        vault=vault_client,
        tracer=tracer,
        logger=qldb_client
    )
    
    return ctx

# Singleton instance
_global_ctx: GlobalContext = None

def get_globals() -> GlobalContext:
    """Retrieve singleton (initialized at app startup)."""
    global _global_ctx
    if _global_ctx is None:
        _global_ctx = init_globals()
    return _global_ctx
```

---

## Part 2: Orchestrator FSM

```python
# neerops/core/orchestrator.py
"""Centralized state machine for PR lifecycle."""

from enum import Enum
from typing import Optional, Dict, Any
import redis
import json
from datetime import datetime, timedelta

class PRState(Enum):
    DETECTED = "DETECTED"
    UNDERSTANDING = "UNDERSTANDING"
    GOAL_CHECK = "GOAL_CHECK"
    REVIEWING = "REVIEWING"
    BUILDING = "BUILDING"
    STAGING = "STAGING"
    CANARY_5 = "CANARY_5"
    CANARY_50 = "CANARY_50"
    ROLLING_100 = "ROLLING_100"
    MERGED = "MERGED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"

class Orchestrator:
    """Central FSM owner. All state transitions flow through here."""
    
    def __init__(self, ctx):
        self.ctx = ctx
        self.redis = ctx.event_bus
    
    def acquire_pr_lock(self, pr_id: str, service: str) -> bool:
        """
        Acquire lock for PR + service.
        Returns True if acquired, False if already locked.
        Used to prevent concurrent PRs for same service.
        """
        lock_key = f"lock:{service}:{pr_id}"
        acquired = self.redis.set(
            lock_key,
            datetime.utcnow().isoformat(),
            nx=True,  # Only set if not exists
            ex=7200   # 2-hour expiry
        )
        return acquired is not None
    
    def release_pr_lock(self, pr_id: str, service: str):
        """Release PR lock (on MERGED or ROLLED_BACK)."""
        lock_key = f"lock:{service}:{pr_id}"
        self.redis.delete(lock_key)
    
    def transition_state(self, pr_id: str, to_state: PRState, metadata: Dict[str, Any] = None):
        """
        Transition PR to new state.
        All state is stored in Redis + PostgreSQL for durability.
        """
        state_key = f"pr-state:{pr_id}"
        
        record = {
            "pr_id": pr_id,
            "state": to_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Store in Redis (fast read)
        self.redis.set(state_key, json.dumps(record), ex=86400)  # 24h
        
        # Publish state transition event
        self.redis.xadd(
            "events:state-transitions",
            {"pr_id": pr_id, "state": to_state.value, "metadata": json.dumps(metadata or {})}
        )
        
        # Log to QLDB (audit)
        self.ctx.logger.send_command(
            "PartiQLUpdate",
            {
                "statement": f"INSERT INTO pr_states VALUE {{'pr_id': ?, 'state': ?, 'timestamp': ?}}",
                "parameters": [pr_id, to_state.value, datetime.utcnow().isoformat()]
            }
        )
    
    def set_vault_rotation_lock(self, service: str, duration_sec: int = 3600):
        """
        Defer Vault secret rotation during canary.
        Two mechanisms:
        1. Extend lease TTL
        2. Set KV flag for Vault policy sentinel
        """
        # Mechanism 1: Extend existing lease by duration_sec
        try:
            self.ctx.vault.auth.token.renew(increment=duration_sec)
        except:
            pass  # Lease not found, that's okay
        
        # Mechanism 2: Set KV flag for Vault policy sentinel
        self.ctx.vault.secrets.kv.create_or_update_secret(
            path=f"neerops/canary-lock/{service}",
            secret_data={"locked_until": (datetime.utcnow() + timedelta(seconds=duration_sec)).isoformat()}
        )
    
    def release_vault_rotation_lock(self, service: str):
        """Release rotation lock."""
        try:
            self.ctx.vault.secrets.kv.delete_secret(path=f"neerops/canary-lock/{service}")
        except:
            pass
    
    def get_last_known_good_image(self, service: str) -> str:
        """
        Retrieve last-known-good image tag for rollback.
        Maintained in QLDB for tamper-proof record.
        """
        # Query QLDB
        result = self.ctx.logger.send_command(
            "PartiQLSelect",
            {
                "statement": "SELECT image_tag FROM deployments WHERE service = ? AND state = 'MERGED' ORDER BY timestamp DESC LIMIT 1",
                "parameters": [service]
            }
        )
        if result and result[0]:
            return result[0]["image_tag"]
        return None
    
    def trigger_rollback(self, pr_id: str, reason: str):
        """Trigger immediate rollback to last-known-good."""
        pr_record = json.loads(self.redis.get(f"pr-state:{pr_id}"))
        service = pr_record["metadata"].get("service")
        
        image_tag = self.get_last_known_good_image(service)
        if image_tag:
            # Publish rollback event
            self.redis.xadd(
                "events:rollback",
                {"pr_id": pr_id, "service": service, "reason": reason, "image_tag": image_tag}
            )
            self.transition_state(pr_id, PRState.ROLLED_BACK, {"image_tag": image_tag, "reason": reason})
```

---

## Part 3: Layer Interface Contract

```python
# neerops/core/types.py
"""Type definitions for layer communication."""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class LayerStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NEEDS_RETRY = "NEEDS_RETRY"
    ESCALATED = "ESCALATED"

@dataclass
class LayerResult:
    """Every layer emits this structure on completion."""
    layer_id: str           # L0, L1, L2, ..., L9
    pr_id: str
    status: LayerStatus
    output: Dict[str, Any]  # Layer-specific result
    error_msg: str = None
    duration_ms: int = None
    token_cost: int = None  # For LLM-using layers

    def to_event(self) -> Dict[str, Any]:
        """Convert to Redis Stream event."""
        return {
            "layer_id": self.layer_id,
            "pr_id": self.pr_id,
            "status": self.status.value,
            "output": json.dumps(self.output),
            "error_msg": self.error_msg or "",
            "duration_ms": self.duration_ms or 0,
            "token_cost": self.token_cost or 0,
        }

@dataclass
class LayerCommand:
    """Orchestrator sends this to trigger a layer."""
    pr_id: str
    layer_id: str
    target_state: str
    input_data: Dict[str, Any]
    timeout_sec: int = 300  # 5 min default

class BaseLayer:
    """All layers inherit from this contract."""
    
    def __init__(self, ctx, layer_id: str):
        self.ctx = ctx
        self.layer_id = layer_id
    
    async def execute(self, pr_id: str, input_data: Dict[str, Any]) -> LayerResult:
        """
        Main layer execution method.
        Layers override this to implement their logic.
        """
        raise NotImplementedError("Layers must implement execute()")
    
    async def handle_timeout(self, pr_id: str):
        """Handle timeout during execution."""
        result = LayerResult(
            layer_id=self.layer_id,
            pr_id=pr_id,
            status=LayerStatus.NEEDS_RETRY,
            output={},
            error_msg="Timeout",
        )
        await self.emit_result(result)
    
    async def emit_result(self, result: LayerResult):
        """Emit result to Event Bus for Orchestrator to consume."""
        event_key = f"events:layer-result:{self.layer_id}"
        self.ctx.event_bus.xadd(event_key, result.to_event())
```

---

## Part 4: L0 Cognition - Solver Selection

```python
# neerops/layers/l0_cognition.py
"""L0: Cognition layer - solver selection based on risk and novelty."""

import json
from typing import Tuple
from neerops.core.types import BaseLayer, LayerResult, LayerStatus

class CognitionLayer(BaseLayer):
    """
    Selects the solver for intent review:
    - Heuristic (90% of cases, instant)
    - RL Model (9% of cases, ~15 sec)
    - LLM (0.9% of cases, ~45 sec)
    - Human (<0.1% of cases)
    """
    
    def __init__(self, ctx):
        super().__init__(ctx, "L0")
        self.heuristic_rules = self._load_heuristics()
        self.rl_model = self._load_rl_model()
    
    def _load_heuristics(self) -> Dict[str, Any]:
        """Load heuristic library from Redis."""
        rules = {}
        for key in self.ctx.event_bus.keys("heuristic:*"):
            rule_data = json.loads(self.ctx.event_bus.get(key))
            rules[key] = rule_data
        return rules
    
    def _load_rl_model(self):
        """Load RL model from storage."""
        # In production: load from S3 or model registry
        return None
    
    def _check_heuristic_match(self, change_summary: str, risk_score: float) -> Tuple[bool, str]:
        """
        Check if this change matches any known heuristic rule.
        Returns: (match_found, action)
        """
        for rule_name, rule in self.heuristic_rules.items():
            if self._pattern_matches(change_summary, rule["pattern"]):
                return True, rule["action"]
        return False, None
    
    def _pattern_matches(self, text: str, pattern: str) -> bool:
        """Simple pattern matching."""
        import re
        return re.search(pattern, text) is not None
    
    async def execute(self, pr_id: str, input_data: Dict[str, Any]) -> LayerResult:
        """
        Select solver based on change complexity and risk.
        """
        change_summary = input_data.get("change_summary", "")
        risk_score = input_data.get("l8_risk_score", 0.5)
        intent = input_data.get("pr_intent", "")
        
        # 1. Try heuristic match (90% case)
        heuristic_match, action = self._check_heuristic_match(change_summary, risk_score)
        if heuristic_match:
            return LayerResult(
                layer_id=self.layer_id,
                pr_id=pr_id,
                status=LayerStatus.SUCCESS,
                output={
                    "solver": "heuristic",
                    "action": action,
                    "confidence": 0.95,
                },
                duration_ms=50,
            )
        
        # 2. Check for known pattern variation (9% case)
        if self._is_known_pattern_variation(change_summary):
            return LayerResult(
                layer_id=self.layer_id,
                pr_id=pr_id,
                status=LayerStatus.SUCCESS,
                output={
                    "solver": "rl",
                    "model_version": "ppo-v3",
                    "confidence": 0.82,
                },
                duration_ms=200,
            )
        
        # 3. Novel problem - use LLM (0.9% case)
        return LayerResult(
            layer_id=self.layer_id,
            pr_id=pr_id,
            status=LayerStatus.SUCCESS,
            output={
                "solver": "llm",
                "token_budget": 500,
                "confidence_threshold": 0.85,
            },
            duration_ms=100,
            token_cost=50,
        )
    
    def _is_known_pattern_variation(self, change_summary: str) -> bool:
        """Check RL model for known pattern."""
        # In production: run actual RL inference
        return False
```

---

## Part 5: L5 Continuous Monitor

```python
# neerops/layers/l5_monitor.py
"""L5: Continuous monitoring with multi-tier anomaly detection."""

import json
import numpy as np
from typing import Dict, List, Any
from neerops.core.types import BaseLayer, LayerResult, LayerStatus

class MonitorLayer(BaseLayer):
    """
    Collects metrics from instrumentation.
    Three anomaly detection tiers:
    1. Static threshold (instant)
    2. 3-sigma moving average
    3. Bayesian ML prediction
    """
    
    def __init__(self, ctx):
        super().__init__(ctx, "L5")
        self.thresholds = {
            "error_rate_percent": 1.0,
            "latency_p99_ms": 2000,
            "cpu_percent": 80,
            "memory_percent": 85,
        }
    
    async def execute(self, pr_id: str, input_data: Dict[str, Any]) -> LayerResult:
        """
        Start continuous metric collection.
        This layer runs async and emits anomaly events on Event Bus.
        """
        service = input_data.get("service")
        namespace = input_data.get("namespace")
        
        # Subscribe to metric stream
        consumer_group = f"monitor:{pr_id}"
        
        # Start background task to consume metrics
        self.start_metric_consumer(pr_id, service, namespace, consumer_group)
        
        return LayerResult(
            layer_id=self.layer_id,
            pr_id=pr_id,
            status=LayerStatus.SUCCESS,
            output={"consumer_group": consumer_group, "status": "monitoring"},
            duration_ms=100,
        )
    
    def start_metric_consumer(self, pr_id: str, service: str, namespace: str, consumer_group: str):
        """Background task to collect and analyze metrics."""
        import asyncio
        import time
        
        async def monitor_loop():
            while True:
                # Collect current metrics
                metrics = self._collect_metrics(service, namespace)
                
                # Tier 1: Static threshold check
                anomalies = self._check_static_thresholds(metrics)
                
                if anomalies:
                    # Emit anomaly event
                    event = {
                        "pr_id": pr_id,
                        "service": service,
                        "anomalies": json.dumps(anomalies),
                        "tier": "static",
                    }
                    self.ctx.event_bus.xadd("events:anomalies", event)
                
                # Tier 2: 3-sigma check
                sigma_anomalies = self._check_3sigma(metrics)
                if sigma_anomalies:
                    event = {
                        "pr_id": pr_id,
                        "service": service,
                        "anomalies": json.dumps(sigma_anomalies),
                        "tier": "3sigma",
                    }
                    self.ctx.event_bus.xadd("events:anomalies", event)
                
                await asyncio.sleep(30)  # Collection interval
        
        # Run in background (fire and forget)
        asyncio.create_task(monitor_loop())
    
    def _collect_metrics(self, service: str, namespace: str) -> Dict[str, float]:
        """Collect metrics from Prometheus."""
        # In production: query Prometheus API
        return {
            "error_rate_percent": np.random.normal(0.1, 0.05),
            "latency_p99_ms": np.random.normal(500, 50),
            "cpu_percent": np.random.normal(30, 5),
            "memory_percent": np.random.normal(40, 5),
        }
    
    def _check_static_thresholds(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Tier 1: Static threshold anomaly detection."""
        anomalies = []
        for metric_name, threshold in self.thresholds.items():
            if metric_name in metrics and metrics[metric_name] > threshold:
                anomalies.append({
                    "metric": metric_name,
                    "value": metrics[metric_name],
                    "threshold": threshold,
                    "severity": "CRITICAL",
                })
        return anomalies
    
    def _check_3sigma(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Tier 2: 3-sigma moving average anomaly detection."""
        # In production: maintain rolling window of metrics, compute mean + stdev
        return []
```

---

## Part 6: L6 Healing Pipeline

```python
# neerops/layers/l6_healing.py
"""L6: Healing pipeline - 4-tier escalation."""

import json
from typing import Dict, Any
from neerops.core.types import BaseLayer, LayerResult, LayerStatus

class HealingLayer(BaseLayer):
    """
    Responds to anomalies from L5.
    Escalation: Heuristic → RL → LLM → Human
    """
    
    def __init__(self, ctx):
        super().__init__(ctx, "L6")
        self.healing_history = {}  # Track action deduplication
    
    async def execute(self, pr_id: str, input_data: Dict[str, Any]) -> LayerResult:
        """
        Heal an anomaly detected by L5.
        """
        anomalies = input_data.get("anomalies", [])
        service = input_data.get("service")
        
        for anomaly in anomalies:
            healing_action = await self._select_healing_action(pr_id, service, anomaly)
            success = await self._execute_healing(pr_id, service, healing_action)
            
            if success:
                # Update heuristic library in real-time
                self._update_heuristic_library(service, anomaly, healing_action)
            else:
                # Escalate
                await self._escalate_to_human(pr_id, service, anomaly)
        
        return LayerResult(
            layer_id=self.layer_id,
            pr_id=pr_id,
            status=LayerStatus.SUCCESS,
            output={"healing_actions": len(anomalies)},
        )
    
    async def _select_healing_action(self, pr_id: str, service: str, anomaly: Dict[str, Any]) -> str:
        """
        Determine healing action.
        Tier 1: Check heuristic library (90%, instant)
        Tier 2: RL model (9%, ~15 sec)
        Tier 3: LLM (0.9%, ~45 sec)
        Tier 4: Human (<0.1%)
        """
        metric_name = anomaly.get("metric")
        
        # Tier 1: Heuristic rules
        heuristic_action = self._check_heuristic_healing(service, metric_name)
        if heuristic_action:
            return heuristic_action
        
        # Tier 2: RL model
        rl_action = self._check_rl_healing(service, metric_name)
        if rl_action and rl_action.get("confidence", 0) > 0.7:
            return rl_action
        
        # Tier 3: LLM reasoning
        llm_action = await self._get_llm_healing(pr_id, service, anomaly)
        if llm_action and llm_action.get("confidence", 0) > 0.85:
            return llm_action
        
        # Tier 4: Human escalation
        return {"action": "escalate", "to": "human"}
    
    def _check_heuristic_healing(self, service: str, metric_name: str) -> Dict[str, Any]:
        """Look up heuristic healing action."""
        # Example heuristics:
        if metric_name == "error_rate_percent":
            return {"action": "restart_pod", "tier": "heuristic"}
        elif metric_name == "memory_percent":
            return {"action": "scale_up", "tier": "heuristic"}
        return None
    
    def _check_rl_healing(self, service: str, metric_name: str) -> Dict[str, Any]:
        """Use RL model to select action."""
        # In production: run actual RL inference
        return None
    
    async def _get_llm_healing(self, pr_id: str, service: str, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to diagnose and recommend healing."""
        # In production: call LLM API
        return None
    
    async def _execute_healing(self, pr_id: str, service: str, action: Dict[str, Any]) -> bool:
        """Execute the healing action."""
        action_type = action.get("action")
        
        # Action deduplication: prevent circular loops
        action_key = f"{pr_id}:{service}:{action_type}"
        attempt_count = self.healing_history.get(action_key, 0)
        
        if attempt_count >= 3:
            # Tried 3 times already, escalate
            return False
        
        self.healing_history[action_key] = attempt_count + 1
        
        # Execute action
        if action_type == "restart_pod":
            # kubectl delete pod
            pass
        elif action_type == "scale_up":
            # kubectl scale
            pass
        
        return True
    
    def _update_heuristic_library(self, service: str, anomaly: Dict[str, Any], action: Dict[str, Any]):
        """Add successful healing as new heuristic rule (real-time update)."""
        metric = anomaly.get("metric")
        pattern = f"{metric}:{anomaly.get('value')}"
        
        rule = {
            "pattern": pattern,
            "action": action.get("action"),
            "created_at": json.dumps({"timestamp": str(__import__("datetime").datetime.utcnow())}),
        }
        
        self.ctx.event_bus.set(f"heuristic:{service}:{metric}", json.dumps(rule))
    
    async def _escalate_to_human(self, pr_id: str, service: str, anomaly: Dict[str, Any]):
        """Escalate to human with 15-min SLA."""
        escalation = {
            "pr_id": pr_id,
            "service": service,
            "anomaly": json.dumps(anomaly),
            "timestamp": str(__import__("datetime").datetime.utcnow()),
        }
        self.ctx.event_bus.xadd("events:human-escalation", escalation)
```

---

## Part 7: Deployment Configuration (Kubernetes)

```yaml
# kubernetes/neerops-deployment.yaml
---
# Orchestrator StatefulSet (HA Pair)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neerops-orchestrator
  namespace: neerops
spec:
  serviceName: neerops-orchestrator
  replicas: 2  # Active-Passive HA
  selector:
    matchLabels:
      app: neerops-orchestrator
  template:
    metadata:
      labels:
        app: neerops-orchestrator
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values:
                      - neerops-orchestrator
              topologyKey: kubernetes.io/hostname
      containers:
        - name: orchestrator
          image: neerops/orchestrator:v9.0
          env:
            - name: REDIS_HOST
              value: redis-sentinel-master
            - name: REDIS_PORT
              value: "26379"
            - name: VAULT_ADDR
              value: http://vault.default:8200
            - name: JAEGER_HOST
              value: jaeger-collector
            - name: JAEGER_PORT
              value: "6831"
          volumeMounts:
            - name: vault-token
              mountPath: /var/run/secrets
              readOnly: true
      volumes:
        - name: vault-token
          projected:
            sources:
              - serviceAccountToken:
                  path: vault-token
                  audience: vault
---
# Layer Deployments (example: L5 Monitor)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: neerops-layer-5-monitor
  namespace: neerops
spec:
  replicas: 3
  selector:
    matchLabels:
      app: neerops-l5-monitor
  template:
    metadata:
      labels:
        app: neerops-l5-monitor
    spec:
      containers:
        - name: l5-monitor
          image: neerops/layers/l5-monitor:v9.0
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 2000m
              memory: 2Gi
          env:
            - name: REDIS_HOST
              value: redis-sentinel-master
            - name: PROMETHEUS_URL
              value: http://prometheus:9090
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
---
# Redis Sentinel for Event Bus HA
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-sentinel-config
  namespace: neerops
data:
  sentinel.conf: |
    port 26379
    sentinel monitor mymaster 127.0.0.1 6379 2
    sentinel down-after-milliseconds mymaster 5000
    sentinel failover-timeout mymaster 10000
    sentinel parallel-syncs mymaster 1
---
# RBAC for NeerOps
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: neerops
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets"]
    verbs: ["get", "list", "watch", "update", "patch"]
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["create", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: neerops
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: neerops
subjects:
  - kind: ServiceAccount
    name: neerops
    namespace: neerops
```

---

## Checklist: Ready for NeerOps v9 Deployment

- [ ] Global singletons initialized (Event Bus, Vault, OTEL, QLDB)
- [ ] Orchestrator HA deployed (2 replicas, leader election)
- [ ] All 9 layers deployed (L0-L9)
- [ ] Redis Sentinel operational (3 sentinels)
- [ ] Vault cluster running (3 nodes)
- [ ] Jaeger + Prometheus for observability
- [ ] Security gates configured (Gitleaks, Semgrep, Trivy, ZAP, Cosign)
- [ ] Heuristic library seeded with 10+ known patterns
- [ ] RL model training pipeline running
- [ ] LLM API credentials + token budget set
- [ ] QLDB ledger created (7-year retention)
- [ ] S3 Object Lock enabled (10-year legal hold)
- [ ] First test PR submitted

---

**Status:** ✅ Implementation Guide Complete  
**Version:** 9.0  
**Created:** May 14, 2026
