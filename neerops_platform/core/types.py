"""
NEEROps v9.0 - Core Type Definitions and Data Models
Core types used across all layers, Orchestrator, and supporting systems.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────
# ENUMERATIONS
# ─────────────────────────────────────────────────────────────────

class PRState(str, Enum):
    """Orchestrator FSM states for PR lifecycle."""
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


class LayerResult(str, Enum):
    """Terminal states a layer can report."""
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"


class SolverType(str, Enum):
    """L0 Cognition solver selection."""
    HEURISTIC = "HEURISTIC"
    RL_MODEL = "RL_MODEL"
    LOCAL_MODEL = "LOCAL_MODEL"
    LLM_API = "LLM_API"
    HUMAN = "HUMAN"


class HealingAction(str, Enum):
    """L6 Healing action types."""
    RESTART_POD = "restart_pod"
    SCALE_REPLICAS = "scale_replicas"
    INCREASE_MEMORY = "increase_memory"
    INCREASE_CPU = "increase_cpu"
    ROLLBACK_VERSION = "rollback_version"
    LOG_CLEANUP = "log_cleanup"
    SCALE_OUT_HPA = "scale_out_hpa"
    RESTART_PLAYWRIGHT = "restart_playwright"
    RETRY_IMAGE_PULL = "retry_image_pull"


class AnomalySeverity(str, Enum):
    """L5 Monitor anomaly severity."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SecurityScanTool(str, Enum):
    """L2 Security scan tools."""
    GITLEAKS = "gitleaks"
    SEMGREP = "semgrep"
    TRIVY = "trivy"
    COSIGN = "cosign"
    ZAP = "zap"
    FALCO = "falco"


class SafetyConstraint(str, Enum):
    """S1-S8 Hard safety constraints."""
    S1_SIGNED_IMAGES = "S1"
    S2_NO_SECRETS_IN_IMAGES = "S2"
    S3_PROMPT_HASH_LOCK = "S3"
    S4_ARCH_CHANGES_REQUIRE_REVIEW = "S4"
    S5_ROLLBACK_ALWAYS_POSSIBLE = "S5"
    S6_VAULT_ROTATION_LOCK = "S6"
    S7_CIRCULAR_LOOP_DETECTION = "S7"
    S8_QLDB_APPEND_ONLY = "S8"


# ─────────────────────────────────────────────────────────────────
# GLOBAL EVENT TYPES
# ─────────────────────────────────────────────────────────────────

class Event(BaseModel):
    """Base event class for Event Bus."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pr_id: Optional[str] = None
    trace_id: Optional[str] = None
    source_layer: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class LayerResultEvent(Event):
    """Result event published by each layer."""
    layer_name: str
    result_status: LayerResult
    output: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


class AnomalyEvent(Event):
    """L5 Monitor publishes anomalies."""
    severity: AnomalySeverity
    anomaly_type: str
    metric_name: str
    metric_value: float
    baseline_value: float
    context: Dict[str, Any] = Field(default_factory=dict)


class HealingOutcomeEvent(Event):
    """L6 Healing reports outcome."""
    action_taken: HealingAction
    success: bool
    verification_result: Optional[bool] = None
    execution_time_ms: float = 0.0


class NewHeuristicRuleEvent(Event):
    """L6/L7 emits new heuristic rule."""
    anomaly_signature: Dict[str, Any]
    action: HealingAction
    confidence: float
    source: str  # LLM_DERIVED, HUMAN_DERIVED, RL_PROMOTED, MANUAL


# ─────────────────────────────────────────────────────────────────
# PR AND DEPLOYMENT MODELS
# ─────────────────────────────────────────────────────────────────

class PRMetadata(BaseModel):
    """Pull Request metadata."""
    pr_id: str
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str
    namespace: str
    author: str
    title: str
    description: str
    source_branch: str
    target_branch: str = "main"
    commit_sha: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    current_state: PRState = PRState.DETECTED
    last_state_change: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeGraph(BaseModel):
    """L1 Understanding - Knowledge Graph."""
    kg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pr_id: str
    nodes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    edges: List[Tuple[str, str]] = Field(default_factory=list)
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    iac_drift_detected: bool = False
    partial: bool = False
    incremental: bool = False
    delta_node_count: int = 0
    total_node_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ttl_seconds: int = 300
    stale_kg: bool = False


class ReviewVerdict(BaseModel):
    """L2 Review - Code review result."""
    pr_id: str
    verdict: str  # APPROVED, REJECTED, NEEDS_INFO
    gitleaks_passed: bool
    semgrep_passed: bool
    mutmut_score: Optional[float] = None
    contract_tests_passed: bool = False
    reasoning: str = ""
    violations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BuildResult(BaseModel):
    """L3 Build - Build output."""
    pr_id: str
    image_uri: str
    image_digest: str
    cosign_signature: str
    trivy_report: Dict[str, Any] = Field(default_factory=dict)
    critical_cves: int = 0
    test_results: Dict[str, Any] = Field(default_factory=dict)
    build_duration_seconds: float = 0.0
    success: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CanaryMetrics(BaseModel):
    """L4/L5 - Canary phase metrics."""
    phase: str  # "staging", "canary_5", "canary_50", "rolling_100"
    region: str
    timestamp: datetime
    error_rate: float
    latency_p99_ms: float
    cpu_percent: float
    memory_percent: float
    pod_restarts: int
    requests_total: int
    errors_total: int


class RiskEnvelope(BaseModel):
    """L8 World Model output."""
    pr_id: str
    goal_alignment_score: float  # 0.0-1.0
    risk_score: float  # 0.0-1.0
    p_failure: float
    p_sla_breach: float
    p_cost_overrun: float
    pre_computed_healing_plans: List[Dict[str, Any]] = Field(default_factory=list)
    canary_gate_weight_adjustment: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HeuristicRule(BaseModel):
    """ML - Heuristic Library rule."""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    anomaly_signature: Dict[str, Any]
    action: HealingAction
    action_params: Dict[str, Any] = Field(default_factory=dict)
    confidence: float  # 0.0-1.0
    success_count: int = 0
    total_count: int = 0
    source: str  # LLM_DERIVED, HUMAN_DERIVED, RL_PROMOTED, MANUAL
    last_validated_at: datetime = Field(default_factory=datetime.utcnow)
    safety_constraint: Optional[str] = None
    embedding: Optional[List[float]] = None  # 1536-dim
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RL_TrainingExample(BaseModel):
    """L7 Feedback - Training example for RL."""
    state: Dict[str, Any]  # metrics + risk + context
    action: str  # "ADVANCE", "HOLD", "ROLLBACK", "ESCALATE"
    reward: float
    is_weight: float = 1.0  # Importance sampling weight
    outcome_labels: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────
# ORCHESTRATOR MODELS
# ─────────────────────────────────────────────────────────────────

class OrchestratorState(BaseModel):
    """Orchestrator FSM state."""
    pr_id: str
    current_state: PRState
    state_history: List[Tuple[PRState, datetime]] = Field(default_factory=list)
    last_known_good_image: Optional[str] = None
    active_canary_region: Optional[str] = None
    vault_lease_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CircuitBreakerState(BaseModel):
    """Circuit breaker for layer reliability."""
    layer_name: str
    state: str  # CLOSED, OPEN, HALF_OPEN
    failure_count: int = 0
    failure_threshold: int = 3
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    open_since: Optional[datetime] = None
    timeout_seconds: int = 60


# ─────────────────────────────────────────────────────────────────
# MONITORING AND METRICS
# ─────────────────────────────────────────────────────────────────

class SystemMetric(BaseModel):
    """L5 Monitor - System metric."""
    metric_name: str
    metric_value: float
    timestamp: datetime
    service: str
    namespace: str
    region: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)


class AnomalyDetectionResult(BaseModel):
    """L5 Monitor - Anomaly detection output."""
    anomaly_detected: bool
    severity: AnomalySeverity
    metric_name: str
    current_value: float
    baseline_value: float
    zscore: Optional[float] = None
    bayesian_probability: Optional[float] = None
    suggested_action: Optional[HealingAction] = None


@dataclass
class LayerResult_DataClass:
    """Internal layer result tracking."""
    layer_name: str
    status: LayerResult
    output: Dict[str, Any]
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
