"""
NEEROps v9.0 - Heuristic Library
Stores heuristic rules with PostgreSQL backend + pgvector for semantic search.
Rules updated on every healing success and human override.
Meta-Cognition invalidates stale rules not validated in 30 days.
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid

from core.types import HeuristicRule, HealingAction
from core.globals import GlobalContext

logger = logging.getLogger(__name__)


class HeuristicLibrary:
    """Heuristic rule storage and semantic search."""
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
        # Mock: in-memory rule store
        self._rules: Dict[str, HeuristicRule] = {}
        self._rules_by_signature: Dict[str, HeuristicRule] = {}
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize with default heuristic rules."""
        
        default_rules = [
            {
                "anomaly_signature": {"type": "OOMKill", "pattern": "*"},
                "action": HealingAction.INCREASE_MEMORY,
                "action_params": {"multiplier": 2.0},
                "confidence": 0.95,
                "source": "MANUAL"
            },
            {
                "anomaly_signature": {"type": "CrashLoopBackOff", "pattern": "*"},
                "action": HealingAction.RESTART_POD,
                "action_params": {},
                "confidence": 0.90,
                "source": "MANUAL"
            },
            {
                "anomaly_signature": {"type": "HighCPU", "threshold": 0.80},
                "action": HealingAction.INCREASE_CPU,
                "action_params": {"multiplier": 2.0},
                "confidence": 0.80,
                "source": "MANUAL"
            },
            {
                "anomaly_signature": {"type": "HighLatency", "threshold": 1000},
                "action": HealingAction.SCALE_REPLICAS,
                "action_params": {"increment": 2},
                "confidence": 0.75,
                "source": "MANUAL"
            },
        ]
        
        for rule_data in default_rules:
            rule = HeuristicRule(
                anomaly_signature=rule_data["anomaly_signature"],
                action=rule_data["action"],
                action_params=rule_data["action_params"],
                confidence=rule_data["confidence"],
                source=rule_data["source"],
                last_validated_at=datetime.utcnow()
            )
            
            self._rules[rule.rule_id] = rule
            
            # Index by signature hash
            sig_hash = self._hash_signature(rule.anomaly_signature)
            self._rules_by_signature[sig_hash] = rule
    
    def lookup_rule(self, anomaly_signature: Dict[str, Any]) -> Optional[HeuristicRule]:
        """
        Lookup heuristic rule for anomaly.
        
        Steps:
        1. Compute signature hash
        2. Check exact match (fast path)
        3. Check semantic embedding similarity (slow path)
        4. Return best match or None
        """
        
        # Exact signature match (fastest)
        sig_hash = self._hash_signature(anomaly_signature)
        if sig_hash in self._rules_by_signature:
            rule = self._rules_by_signature[sig_hash]
            
            # Update last_validated
            rule.last_validated_at = datetime.utcnow()
            rule.total_count += 1
            
            logger.debug(f"[Heuristic] Exact match found: {rule.rule_id}")
            return rule
        
        # Semantic similarity search (would use pgvector in production)
        # For mock: do simple pattern matching
        for rule_id, rule in self._rules.items():
            if self._matches_pattern(rule.anomaly_signature, anomaly_signature):
                # Update stats
                rule.total_count += 1
                rule.last_validated_at = datetime.utcnow()
                
                logger.debug(f"[Heuristic] Pattern match found: {rule_id}")
                return rule
        
        logger.debug("[Heuristic] No rule found for signature")
        return None
    
    def record_rule_success(self, rule_id: str):
        """Record successful execution of a rule."""
        if rule_id in self._rules:
            rule = self._rules[rule_id]
            rule.success_count += 1
            rule.last_validated_at = datetime.utcnow()
            
            # Update confidence based on success rate
            if rule.total_count > 0:
                success_rate = rule.success_count / rule.total_count
                rule.confidence = min(0.99, 0.5 + (success_rate * 0.49))
            
            logger.debug(f"[Heuristic] Recorded success: {rule_id} (rate={rule.success_count}/{rule.total_count})")
    
    def record_rule_failure(self, rule_id: str):
        """Record failed execution of a rule."""
        if rule_id in self._rules:
            rule = self._rules[rule_id]
            rule.total_count += 1
            
            # Decrease confidence on failure
            rule.confidence = max(0.1, rule.confidence * 0.95)
            
            logger.debug(f"[Heuristic] Recorded failure: {rule_id} (confidence now {rule.confidence:.2f})")
    
    def add_rule(
        self,
        anomaly_signature: Dict[str, Any],
        action: HealingAction,
        action_params: Dict[str, Any] = None,
        confidence: float = 0.75,
        source: str = "LLM_DERIVED"
    ) -> HeuristicRule:
        """Add new rule to library."""
        
        rule = HeuristicRule(
            anomaly_signature=anomaly_signature,
            action=action,
            action_params=action_params or {},
            confidence=confidence,
            source=source,
            last_validated_at=datetime.utcnow()
        )
        
        # Store in memory
        self._rules[rule.rule_id] = rule
        
        # Index by signature hash
        sig_hash = self._hash_signature(anomaly_signature)
        self._rules_by_signature[sig_hash] = rule
        
        # Persist to QLDB
        self.ctx.logger.write("HeuristicRuleAdded", {
            "rule_id": rule.rule_id,
            "source": source,
            "action": action.value,
            "confidence": confidence
        })
        
        logger.info(f"[Heuristic] Added new rule: {rule.rule_id} (source={source}, action={action})")
        
        return rule
    
    def invalidate_stale_rules(self, stale_days: int = 30):
        """Meta-Cognition: invalidate rules not validated in N days."""
        
        cutoff = datetime.utcnow() - timedelta(days=stale_days)
        stale_rules = []
        
        for rule_id, rule in self._rules.items():
            if rule.last_validated_at < cutoff:
                stale_rules.append(rule_id)
        
        for rule_id in stale_rules:
            del self._rules[rule_id]
            logger.info(f"[Heuristic] Invalidated stale rule: {rule_id}")
        
        if stale_rules:
            self.ctx.logger.write("StaleRulesInvalidated", {
                "count": len(stale_rules),
                "rule_ids": stale_rules
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        
        total_rules = len(self._rules)
        avg_confidence = sum(r.confidence for r in self._rules.values()) / total_rules if total_rules > 0 else 0
        
        return {
            "total_rules": total_rules,
            "avg_confidence": avg_confidence,
            "manual_rules": sum(1 for r in self._rules.values() if r.source == "MANUAL"),
            "llm_derived_rules": sum(1 for r in self._rules.values() if r.source == "LLM_DERIVED"),
            "human_derived_rules": sum(1 for r in self._rules.values() if r.source == "HUMAN_DERIVED"),
        }
    
    # ─────────────────────────────────────────────────────────────
    # Helper methods
    # ─────────────────────────────────────────────────────────────
    
    def _hash_signature(self, signature: Dict[str, Any]) -> str:
        """Hash anomaly signature for fast lookup."""
        sig_json = json.dumps(signature, sort_keys=True)
        return hashlib.sha256(sig_json.encode()).hexdigest()[:16]
    
    def _matches_pattern(self, rule_sig: Dict[str, Any], anomaly_sig: Dict[str, Any]) -> bool:
        """Check if anomaly matches rule pattern."""
        
        # Simple pattern matching mock
        rule_type = rule_sig.get("type", "")
        anomaly_type = anomaly_sig.get("type", "")
        
        # Exact match or wildcard
        if rule_type == anomaly_type or rule_sig.get("pattern") == "*":
            return True
        
        return False
