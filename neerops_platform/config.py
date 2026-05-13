"""
NEEROps v9.0 - Configuration Management
Environment-specific settings, secrets management, feature flags.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Config:
    """Configuration management for NEEROps platform."""
    
    # Application
    APP_NAME = "neerops"
    APP_VERSION = "9.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Event Bus
    EVENT_BUS_TYPE = os.getenv("EVENT_BUS_TYPE", "mock")  # mock | redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # Vault
    VAULT_TYPE = os.getenv("VAULT_TYPE", "mock")  # mock | hashicorp
    VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
    VAULT_TOKEN = os.getenv("VAULT_TOKEN", "")
    VAULT_KV_PATH = os.getenv("VAULT_KV_PATH", "secret/neerops")
    
    # Observability
    OTEL_TYPE = os.getenv("OTEL_TYPE", "mock")  # mock | jaeger
    JAEGER_HOST = os.getenv("JAEGER_HOST", "localhost")
    JAEGER_PORT = int(os.getenv("JAEGER_PORT", "6831"))
    JAEGER_SERVICE = os.getenv("JAEGER_SERVICE", "neerops")
    
    # Audit
    QLDB_TYPE = os.getenv("QLDB_TYPE", "mock")  # mock | aws
    QLDB_LEDGER_NAME = os.getenv("QLDB_LEDGER_NAME", "neerops-ledger")
    QLDB_LOG_FILE = os.getenv("QLDB_LOG_FILE", "/var/log/neerops/qldb.jsonl")
    
    # Container Registry
    REGISTRY_TYPE = os.getenv("REGISTRY_TYPE", "mock")  # mock | ecr | harbor
    ECR_REGISTRY = os.getenv("ECR_REGISTRY", "")
    ECR_REGION = os.getenv("ECR_REGION", "us-east-1")
    HARBOR_REGISTRY = os.getenv("HARBOR_REGISTRY", "http://localhost:8080")
    HARBOR_USERNAME = os.getenv("HARBOR_USERNAME", "")
    HARBOR_PASSWORD = os.getenv("HARBOR_PASSWORD", "")
    
    # Kubernetes
    K8S_ENABLED = os.getenv("K8S_ENABLED", "False").lower() == "true"
    K8S_NAMESPACE = os.getenv("K8S_NAMESPACE", "default")
    K8S_CONTEXT = os.getenv("K8S_CONTEXT", "")
    
    # Deployment
    CANARY_TIMEOUT_MINUTES = int(os.getenv("CANARY_TIMEOUT_MINUTES", "45"))
    CANARY_5_PERCENT_DURATION = int(os.getenv("CANARY_5_PERCENT_DURATION", "5"))
    CANARY_50_PERCENT_DURATION = int(os.getenv("CANARY_50_PERCENT_DURATION", "5"))
    GATE_P_SUCCESS_MIN = float(os.getenv("GATE_P_SUCCESS_MIN", "0.95"))
    GATE_P_ROLLBACK_MAX = float(os.getenv("GATE_P_ROLLBACK_MAX", "0.90"))
    
    # Healing
    HEALING_HEURISTIC_MIN = float(os.getenv("HEALING_HEURISTIC_MIN", "0.5"))
    HEALING_RL_MIN = float(os.getenv("HEALING_RL_MIN", "0.7"))
    HEALING_EMBEDDING_MIN = float(os.getenv("HEALING_EMBEDDING_MIN", "0.92"))
    HEALING_LOCAL_MIN = float(os.getenv("HEALING_LOCAL_MIN", "0.8"))
    HEALING_LLM_MIN = float(os.getenv("HEALING_LLM_MIN", "0.85"))
    
    # RL Training
    RL_TRAINING_WINDOW_DAYS = int(os.getenv("RL_TRAINING_WINDOW_DAYS", "7"))
    RL_KL_DIVERGENCE_THRESHOLD = float(os.getenv("RL_KL_DIVERGENCE_THRESHOLD", "0.1"))
    RL_SHADOW_DEPLOYMENT_HOURS = int(os.getenv("RL_SHADOW_DEPLOYMENT_HOURS", "24"))
    
    # LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")  # mock | openai | claude
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-opus")
    LLM_RATE_LIMIT_PER_MINUTE = int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", "3"))
    
    # Monitoring
    MONITOR_METRICS_WINDOW = int(os.getenv("MONITOR_METRICS_WINDOW", "20"))
    ANOMALY_DETECTION_ENABLED = os.getenv("ANOMALY_DETECTION_ENABLED", "True").lower() == "true"
    
    # Supervisor
    SUPERVISOR_ENABLED = os.getenv("SUPERVISOR_ENABLED", "True").lower() == "true"
    SUPERVISOR_CHECK_INTERVAL = int(os.getenv("SUPERVISOR_CHECK_INTERVAL", "5"))
    SUPERVISOR_L5_HEARTBEAT_TIMEOUT = int(os.getenv("SUPERVISOR_L5_HEARTBEAT_TIMEOUT", "30"))
    
    # GitHub / VCS
    VCS_TYPE = os.getenv("VCS_TYPE", "mock")  # mock | github | bitbucket
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME", "")
    BITBUCKET_PASSWORD = os.getenv("BITBUCKET_PASSWORD", "")
    
    # Alerting
    ALERT_CHANNELS = os.getenv("ALERT_CHANNELS", "log").split(",")  # log | slack | pagerduty
    SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
    PAGERDUTY_TOKEN = os.getenv("PAGERDUTY_TOKEN", "")
    
    # Feature Flags
    FEATURE_PROMPT_EVOLUTION = os.getenv("FEATURE_PROMPT_EVOLUTION", "True").lower() == "true"
    FEATURE_RL_TRAINING = os.getenv("FEATURE_RL_TRAINING", "True").lower() == "true"
    FEATURE_META_LEARNING = os.getenv("FEATURE_META_LEARNING", "True").lower() == "true"
    FEATURE_ASYNC_MONITORING = os.getenv("FEATURE_ASYNC_MONITORING", "True").lower() == "true"
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return {
            k: v for k, v in cls.__dict__.items()
            if not k.startswith('_') and k.isupper()
        }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        errors = []
        
        # Validate Event Bus
        if cls.EVENT_BUS_TYPE not in ["mock", "redis"]:
            errors.append(f"Invalid EVENT_BUS_TYPE: {cls.EVENT_BUS_TYPE}")
        
        # Validate Vault
        if cls.VAULT_TYPE not in ["mock", "hashicorp"]:
            errors.append(f"Invalid VAULT_TYPE: {cls.VAULT_TYPE}")
        
        # Validate thresholds
        if not (0 <= cls.GATE_P_SUCCESS_MIN <= 1):
            errors.append(f"GATE_P_SUCCESS_MIN must be 0-1: {cls.GATE_P_SUCCESS_MIN}")
        
        if errors:
            for error in errors:
                logger.error(f"[Config] {error}")
            return False
        
        logger.info("[Config] Configuration validated successfully")
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (mask secrets)."""
        config_dict = cls.get_config_dict()
        
        logger.info("[Config] Current Configuration:")
        logger.info("=" * 80)
        
        for key, value in sorted(config_dict.items()):
            # Mask secrets
            if any(secret in key.upper() for secret in ["TOKEN", "KEY", "PASSWORD", "SECRET"]):
                display_value = "***MASKED***"
            else:
                display_value = value
            
            logger.info(f"  {key:40} = {display_value}")
        
        logger.info("=" * 80)


def load_env_file(env_file: str = ".env"):
    """Load environment variables from .env file."""
    if not os.path.exists(env_file):
        logger.debug(f"[Config] No {env_file} found")
        return
    
    logger.info(f"[Config] Loading from {env_file}")
    
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            
            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()
    
    logger.info(f"[Config] Loaded environment from {env_file}")
