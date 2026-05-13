"""
NEEROps v9.0 - Layer 6: Healing Pipeline
5-tier escalation: Heuristic → RL → Embedding Cache → Local Model → LLM → Human
Each tier has: action dedup check, dry-run validation, execution, verification.
On success: emit NewHeuristicRule.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from core.types import HealingAction, HealingOutcomeEvent, NewHeuristicRuleEvent
from core.globals import GlobalContext

logger = logging.getLogger(__name__)


class HealingLayer:
    """L6 - Autonomous Healing."""
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
        self._action_history: Dict[str, list] = {}  # Track actions per anomaly
        self._max_retries_per_action = 2  # S7: circular loop detection
    
    def handle_anomaly(
        self,
        anomaly_id: str,
        anomaly_context: Dict[str, Any],
        pre_computed_plans: list = None
    ) -> Tuple[bool, HealingOutcomeEvent]:
        """
        Main healing orchestration.
        
        Steps:
        1. Check action dedup (S7 safety constraint)
        2. Try Heuristic tier
        3. Try RL tier
        4. Try Embedding Cache semantic lookup
        5. Try Local Model
        6. Try Full LLM API
        7. Escalate to Human
        
        Returns: (success, outcome_event)
        """
        
        logger.info(f"[L6] Handling anomaly {anomaly_id}: {anomaly_context.get('anomaly_type')}")
        
        outcome = HealingOutcomeEvent(
            event_type="HealingOutcome",
            pr_id=anomaly_context.get("service"),
            action_taken=HealingAction.RESTART_POD,
            success=False
        )
        
        try:
            # Initialize action history for this anomaly
            if anomaly_id not in self._action_history:
                self._action_history[anomaly_id] = []
            
            # TIER 1: Heuristic lookup
            logger.info("[L6] TIER 1: Attempting heuristic resolution...")
            success, action = self._heal_with_heuristic(anomaly_id, anomaly_context)
            if success:
                outcome.action_taken = action
                outcome.success = True
                outcome.execution_time_ms = 5000  # ~5 seconds
                
                # Emit new heuristic rule
                self._emit_new_heuristic_rule(anomaly_id, anomaly_context, action, "HEURISTIC_ESCALATED")
                
                self.ctx.logger.write("HealingSuccess", {
                    "anomaly_id": anomaly_id,
                    "tier": "HEURISTIC",
                    "action": action.value
                })
                return True, outcome
            
            # TIER 2: RL Model
            logger.info("[L6] TIER 2: Attempting RL model resolution...")
            success, action, confidence = self._heal_with_rl(anomaly_id, anomaly_context)
            if success and confidence >= 0.7:
                # Check action dedup (S7)
                if self._check_action_dedup(anomaly_id, action):
                    logger.warning(f"[L6] S7 action dedup triggered - escalating (action={action})")
                    return False, outcome
                
                outcome.action_taken = action
                outcome.success = True
                outcome.execution_time_ms = 15000  # ~15 seconds
                
                self.ctx.logger.write("HealingSuccess", {
                    "anomaly_id": anomaly_id,
                    "tier": "RL_MODEL",
                    "action": action.value,
                    "confidence": confidence
                })
                return True, outcome
            
            # TIER 2b: Embedding Cache semantic lookup
            logger.info("[L6] TIER 2b: Attempting embedding cache...")
            success, cached_resolution = self._heal_with_embedding_cache(anomaly_id, anomaly_context)
            if success:
                outcome.action_taken = HealingAction.SCALE_REPLICAS
                outcome.success = True
                outcome.execution_time_ms = 8000  # ~8 seconds
                
                self.ctx.logger.write("HealingSuccess", {
                    "anomaly_id": anomaly_id,
                    "tier": "EMBEDDING_CACHE",
                    "cached_resolution": cached_resolution
                })
                return True, outcome
            
            # TIER 3: Local Model (in-cluster)
            logger.info("[L6] TIER 3: Attempting local model...")
            success, action, confidence = self._heal_with_local_model(anomaly_id, anomaly_context)
            if success and confidence >= 0.8:
                # Dry-run validation
                if not self._dry_run_validation(action, anomaly_context):
                    logger.warning("[L6] Dry-run validation failed - escalating to LLM")
                else:
                    outcome.action_taken = action
                    outcome.success = True
                    outcome.execution_time_ms = 10000  # ~10 seconds
                    
                    # Promote to heuristic if successful
                    self._emit_new_heuristic_rule(anomaly_id, anomaly_context, action, "LOCAL_MODEL_PROMOTED")
                    
                    self.ctx.logger.write("HealingSuccess", {
                        "anomaly_id": anomaly_id,
                        "tier": "LOCAL_MODEL",
                        "action": action.value,
                        "confidence": confidence
                    })
                    return True, outcome
            
            # TIER 4: Full LLM API
            logger.info("[L6] TIER 4: Attempting full LLM API...")
            
            # Pre-flight checks
            severity = anomaly_context.get("severity", "MEDIUM")
            if severity not in ["HIGH", "CRITICAL"]:
                logger.info("[L6] Severity too low for LLM - escalating to human")
                return False, outcome
            
            success, action, confidence = self._heal_with_llm(anomaly_id, anomaly_context)
            if success and confidence >= 0.85:
                # Dry-run validation (critical before LLM actions)
                if not self._dry_run_validation(action, anomaly_context):
                    logger.warning("[L6] LLM dry-run validation failed - escalating to human")
                    return False, outcome
                
                # Execute and verify
                verified = self._verify_healing_outcome(anomaly_id, action)
                
                if verified:
                    outcome.action_taken = action
                    outcome.success = True
                    outcome.verification_result = True
                    outcome.execution_time_ms = 45000  # ~45 seconds
                    
                    # Emit new heuristic rule (LLM-derived rules are the most valuable)
                    self._emit_new_heuristic_rule(anomaly_id, anomaly_context, action, "LLM_DERIVED")
                    
                    self.ctx.logger.write("HealingSuccess", {
                        "anomaly_id": anomaly_id,
                        "tier": "LLM_API",
                        "action": action.value,
                        "confidence": confidence
                    })
                    return True, outcome
            
            # TIER 5: Human escalation
            logger.warning(f"[L6] All automated tiers failed - escalating to human")
            self.ctx.logger.write("HealingEscalation", {
                "anomaly_id": anomaly_id,
                "context": anomaly_context,
                "reason": "all_tiers_failed"
            })
            
            return False, outcome
        
        except Exception as e:
            logger.error(f"[L6] Healing failed with exception: {e}")
            return False, outcome
    
    def _heal_with_heuristic(self, anomaly_id: str, context: Dict[str, Any]) -> Tuple[bool, HealingAction]:
        """TIER 1: Heuristic lookup and execution."""
        
        anomaly_type = context.get("anomaly_type", "")
        
        # Mock: simple pattern matching
        if "OOMKill" in anomaly_type or "OOM" in anomaly_type:
            return True, HealingAction.INCREASE_MEMORY
        elif "CrashLoop" in anomaly_type:
            return True, HealingAction.RESTART_POD
        elif "HighLatency" in anomaly_type:
            return True, HealingAction.SCALE_REPLICAS
        elif "HighCPU" in anomaly_type:
            return True, HealingAction.INCREASE_CPU
        
        return False, HealingAction.RESTART_POD
    
    def _heal_with_rl(self, anomaly_id: str, context: Dict[str, Any]) -> Tuple[bool, HealingAction, float]:
        """TIER 2: RL model prediction."""
        
        # Mock: return RL prediction
        return False, HealingAction.SCALE_REPLICAS, 0.65
    
    def _heal_with_embedding_cache(self, anomaly_id: str, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """TIER 2b: Semantic similarity search in embedding cache."""
        
        # Mock: no exact semantic match
        return False, {}
    
    def _heal_with_local_model(self, anomaly_id: str, context: Dict[str, Any]) -> Tuple[bool, HealingAction, float]:
        """TIER 3: Local model (Ollama) inference."""
        
        # Mock: local model returns action with moderate confidence
        return False, HealingAction.SCALE_REPLICAS, 0.75
    
    def _heal_with_llm(self, anomaly_id: str, context: Dict[str, Any]) -> Tuple[bool, HealingAction, float]:
        """TIER 4: Full LLM API (with rate limiting and budget checks)."""
        
        logger.debug("[L6] Calling LLM API for diagnosis...")
        
        # Pre-flight: check LLM rate limit and budget
        if not self._check_llm_budget():
            logger.warning("[L6] LLM budget exhausted - cannot call")
            return False, HealingAction.RESTART_POD, 0.0
        
        # Mock: LLM returns diagnosis
        return False, HealingAction.SCALE_REPLICAS, 0.88
    
    def _check_llm_budget(self) -> bool:
        """Check if LLM API budget is available."""
        # In production: check daily token budget
        # For now: always available
        return True
    
    def _dry_run_validation(self, action: HealingAction, context: Dict[str, Any]) -> bool:
        """Dry-run validate action before execution."""
        
        logger.debug(f"[L6] Dry-run validation for action: {action}")
        
        # Mock: validation always passes
        return True
    
    def _verify_healing_outcome(self, anomaly_id: str, action: HealingAction) -> bool:
        """Verify that healing action resolved the anomaly."""
        
        logger.debug(f"[L6] Verifying healing outcome for {anomaly_id}...")
        
        # Mock: healing verified
        return True
    
    def _check_action_dedup(self, anomaly_id: str, action: HealingAction) -> bool:
        """
        S7: Circular loop detection.
        If same action attempted 3x for same anomaly, escalate.
        """
        
        action_history = self._action_history.get(anomaly_id, [])
        recent_actions = [a for a in action_history if a == action]
        
        if len(recent_actions) >= self._max_retries_per_action:
            logger.warning(f"[L6] S7 violation: action {action} repeated {len(recent_actions)} times")
            return True  # Trigger escalation
        
        # Record action
        self._action_history[anomaly_id].append(action)
        
        return False
    
    def _emit_new_heuristic_rule(
        self,
        anomaly_id: str,
        context: Dict[str, Any],
        action: HealingAction,
        source: str
    ):
        """Emit NewHeuristicRule event to be stored in Heuristic Library."""
        
        rule_event = NewHeuristicRuleEvent(
            event_type="NewHeuristicRule",
            anomaly_signature=context,
            action=action,
            confidence=0.75,
            source=source
        )
        
        self.ctx.event_bus.publish("heuristics:new_rules", rule_event.dict())
        
        logger.info(f"[L6] Emitted new heuristic rule (source={source}, action={action})")
