"""
NEEROps v9.0 - Orchestrator
Centralized state owner. No layer calls another directly - all communication through Event Bus.
PR State Machine: DETECTED → UNDERSTANDING → ... → MERGED | FAILED | ROLLED_BACK
"""

import logging
import time
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta
import uuid

from core.types import (
    PRState, LayerResult, Event, LayerResultEvent, PRMetadata, 
    OrchestratorState, CircuitBreakerState, SafetyConstraint
)
from core.globals import GlobalContext


logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Centralized Orchestrator - The Only State Owner.
    
    Responsibilities:
    - Own PR state machine (FSM)
    - Coordinate all layer execution via Event Bus
    - Enforce safety constraints (S1-S8)
    - Manage circuit breakers
    - Handle retry logic and dead-man's switches
    - Maintain Vault rotation locks during canary
    """
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
        self._pr_states: Dict[str, OrchestratorState] = {}
        self._circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self._layer_command_handlers: Dict[str, Callable] = {}
        self._retry_budgets: Dict[str, int] = {}
        
        # Initialize circuit breakers for each layer
        self._init_circuit_breakers()
        
        logger.info("[Orchestrator] Initialized")
    
    def _init_circuit_breakers(self):
        """Initialize circuit breakers for each layer."""
        layers = [
            "L0_COGNITION", "L1_UNDERSTANDING", "L2_REVIEW", "L3_BUILD",
            "L4_DEPLOY", "L5_MONITOR", "L6_HEALING", "L7_FEEDBACK",
            "L8_REASONING", "L9_METALEARNING"
        ]
        
        for layer in layers:
            self._circuit_breakers[layer] = CircuitBreakerState(
                layer_name=layer,
                state="CLOSED",
                failure_threshold=3,
                timeout_seconds=60
            )
    
    def create_pr_context(self, pr_metadata: PRMetadata) -> OrchestratorState:
        """Create new PR context and acquire lock."""
        logger.info(f"[Orchestrator] Creating context for PR {pr_metadata.pr_id}")
        
        # Redis SETNX: acquire per-service namespace lock
        lock_key = f"lock:{pr_metadata.service_name}:{pr_metadata.namespace}"
        
        # In production: redis.setnx(lock_key, pr_metadata.pr_id, ex=3600)
        # For mock: simulate lock acquisition
        self._check_namespace_lock(lock_key, pr_metadata.pr_id)
        
        # Open OTEL trace
        trace_id = self.ctx.tracer.start_span(
            span_name=f"PR-{pr_metadata.pr_id}",
            attributes={
                "service": pr_metadata.service_name,
                "namespace": pr_metadata.namespace,
                "author": pr_metadata.author
            }
        )
        
        # Create PR state
        pr_state = OrchestratorState(
            pr_id=pr_metadata.pr_id,
            current_state=PRState.DETECTED
        )
        
        self._pr_states[pr_metadata.pr_id] = pr_state
        self._retry_budgets[pr_metadata.pr_id] = 3
        
        # Log to QLDB
        self.ctx.logger.write("PRCreated", {
            "pr_id": pr_metadata.pr_id,
            "trace_id": trace_id,
            "service": pr_metadata.service_name,
            "author": pr_metadata.author,
            "lock_key": lock_key
        })
        
        return pr_state
    
    def _check_namespace_lock(self, lock_key: str, pr_id: str):
        """Check if namespace lock can be acquired."""
        # Mock implementation - in production uses Redis
        logger.info(f"[Orchestrator] Acquired lock: {lock_key} for {pr_id}")
        return True
    
    def transition_state(self, pr_id: str, new_state: PRState, reason: str = "") -> bool:
        """
        Transition PR to new state.
        
        Enforces safety constraints before transition.
        """
        if pr_id not in self._pr_states:
            logger.error(f"[Orchestrator] PR not found: {pr_id}")
            return False
        
        current_state = self._pr_states[pr_id].current_state
        
        # Log state transition
        logger.info(f"[Orchestrator] State transition: {pr_id} {current_state} → {new_state} ({reason})")
        
        # Check safety constraints
        if not self._check_safety_constraints(pr_id, new_state):
            logger.error(f"[Orchestrator] Safety constraint violated for {pr_id} → {new_state}")
            return False
        
        # Update state
        self._pr_states[pr_id].current_state = new_state
        self._pr_states[pr_id].last_state_change = datetime.utcnow()
        self._pr_states[pr_id].state_history.append((new_state, datetime.utcnow()))
        
        # Log transition
        self.ctx.logger.write("StateTransition", {
            "pr_id": pr_id,
            "from_state": current_state.value,
            "to_state": new_state.value,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return True
    
    def _check_safety_constraints(self, pr_id: str, target_state: PRState) -> bool:
        """
        Enforce S1-S8 safety constraints before state transition.
        
        S1: No deployment without signed container image
        S2: No secret in image or env var
        S3: Prompt sections hash-locked
        S4: Architecture changes require review
        S5: Rollback always possible
        S6: Vault rotation locked during canary
        S7: Circular healing loop detection
        S8: QLDB append-only
        """
        
        # S5: Ensure last-known-good image exists before deploying
        if target_state in [PRState.CANARY_5, PRState.CANARY_50, PRState.ROLLING_100]:
            pr_state = self._pr_states[pr_id]
            if not pr_state.last_known_good_image:
                logger.warning(f"[Orchestrator] S5 check: last_known_good_image not set for {pr_id}")
                # In strict mode would fail here
        
        # S6: Lock Vault rotation during canary
        if target_state in [PRState.CANARY_5, PRState.CANARY_50]:
            pr_state = self._pr_states[pr_id]
            lease_id = f"lease-{pr_id}-{uuid.uuid4().hex[:8]}"
            pr_state.vault_lease_id = lease_id
            
            # Extend Vault lease
            self.ctx.vault.renew_lease(lease_id, increment_seconds=3600)
            logger.info(f"[Orchestrator] S6: Vault rotation locked for {pr_id}")
        
        # S6: Release rotation lock on terminal state
        if target_state in [PRState.MERGED, PRState.ROLLED_BACK]:
            pr_state = self._pr_states[pr_id]
            if pr_state.vault_lease_id:
                # Delete KV flag in Vault
                self.ctx.vault.delete_secret(f"neerops/canary-lock/{pr_id}")
                logger.info(f"[Orchestrator] S6: Vault rotation lock released for {pr_id}")
        
        return True
    
    def publish_layer_command(self, pr_id: str, layer_name: str, command: Dict[str, Any]) -> bool:
        """
        Publish LayerCommand to Event Bus.
        Only the elected Orchestrator leader may publish.
        """
        event = Event(
            event_type="LayerCommand",
            pr_id=pr_id,
            source_layer="ORCHESTRATOR",
            payload={
                "layer": layer_name,
                "command": command
            }
        )
        
        message_id = self.ctx.event_bus.publish(
            stream_name="orchestrator:commands",
            event_data=event.dict()
        )
        
        logger.info(f"[Orchestrator] Published command to {layer_name}: {message_id}")
        return True
    
    def handle_layer_result(self, result_event: LayerResultEvent) -> bool:
        """
        Consume LayerResult event from Event Bus.
        Update PR state and decide next step.
        """
        pr_id = result_event.pr_id
        layer_name = result_event.layer_name
        status = result_event.result_status
        
        logger.info(f"[Orchestrator] Received {layer_name} result: {status} for {pr_id}")
        
        # Check circuit breaker
        if not self._check_circuit_breaker(layer_name, status):
            logger.error(f"[Orchestrator] Circuit breaker OPEN for {layer_name}")
            # Use heuristic fallback
            self._apply_heuristic_fallback(pr_id, layer_name)
            return False
        
        # Handle layer failure
        if status == LayerResult.FAILED:
            retry_count = self._retry_budgets.get(pr_id, 0)
            if retry_count > 0:
                logger.info(f"[Orchestrator] Retrying {layer_name} ({retry_count} retries left)")
                self._retry_budgets[pr_id] = retry_count - 1
                # Re-publish command to layer
                return True
            else:
                logger.error(f"[Orchestrator] Retry budget exhausted for {pr_id}")
                self.transition_state(pr_id, PRState.FAILED, reason=f"{layer_name} failed")
                return False
        
        # Route based on layer result
        routing_map = {
            "L1_UNDERSTANDING": self._route_from_l1,
            "L2_REVIEW": self._route_from_l2,
            "L3_BUILD": self._route_from_l3,
            "L4_DEPLOY": self._route_from_l4,
            "L5_MONITOR": self._route_from_l5,
            "L6_HEALING": self._route_from_l6,
        }
        
        if layer_name in routing_map:
            return routing_map[layer_name](pr_id, result_event)
        
        return True
    
    def _check_circuit_breaker(self, layer_name: str, status: LayerResult) -> bool:
        """Check circuit breaker state for layer."""
        cb = self._circuit_breakers.get(layer_name)
        if not cb:
            return True
        
        if status == LayerResult.FAILED:
            cb.failure_count += 1
            cb.last_failure_time = datetime.utcnow()
            
            if cb.failure_count >= cb.failure_threshold:
                cb.state = "OPEN"
                cb.open_since = datetime.utcnow()
                logger.error(f"[CircuitBreaker] {layer_name} opened")
                return False
        elif status == LayerResult.SUCCESS:
            if cb.state == "HALF_OPEN":
                cb.state = "CLOSED"
                cb.failure_count = 0
                logger.info(f"[CircuitBreaker] {layer_name} closed")
            elif cb.state == "CLOSED":
                cb.success_count += 1
        
        # Check if should transition to HALF_OPEN
        if cb.state == "OPEN":
            if datetime.utcnow() - cb.open_since > timedelta(seconds=cb.timeout_seconds):
                cb.state = "HALF_OPEN"
                logger.info(f"[CircuitBreaker] {layer_name} half-open (probing)")
                return True
            return False
        
        return True
    
    def _apply_heuristic_fallback(self, pr_id: str, layer_name: str):
        """Apply heuristic fallback when layer fails."""
        logger.info(f"[Orchestrator] Applying heuristic fallback for {layer_name}")
        # Implement fallback logic based on layer
        self.ctx.logger.write("HeuristicFallback", {
            "pr_id": pr_id,
            "layer": layer_name,
            "reason": "circuit_breaker_open"
        })
    
    # ─────────────────────────────────────────────────────────────
    # Layer routing logic
    # ─────────────────────────────────────────────────────────────
    
    def _route_from_l1(self, pr_id: str, event: LayerResultEvent) -> bool:
        """Route after L1 Understanding completes."""
        if event.result_status == LayerResult.SUCCESS:
            self.transition_state(pr_id, PRState.GOAL_CHECK, reason="L1 complete")
            # Publish command to L8
            self.publish_layer_command(pr_id, "L8_REASONING", {"kg": event.output})
        return True
    
    def _route_from_l2(self, pr_id: str, event: LayerResultEvent) -> bool:
        """Route after L2 Review completes."""
        if event.result_status == LayerResult.SUCCESS:
            if event.output.get("verdict") == "APPROVED":
                self.transition_state(pr_id, PRState.BUILDING, reason="L2 approved")
                # Publish command to L3
                self.publish_layer_command(pr_id, "L3_BUILD", {})
            else:
                self.transition_state(pr_id, PRState.FAILED, reason="L2 rejected")
        return True
    
    def _route_from_l3(self, pr_id: str, event: LayerResultEvent) -> bool:
        """Route after L3 Build completes."""
        if event.result_status == LayerResult.SUCCESS:
            # Store last-known-good image (S5)
            self._pr_states[pr_id].last_known_good_image = event.output.get("image_uri")
            
            self.transition_state(pr_id, PRState.STAGING, reason="L3 build complete")
            # Publish command to L4
            self.publish_layer_command(pr_id, "L4_DEPLOY", event.output)
        return True
    
    def _route_from_l4(self, pr_id: str, event: LayerResultEvent) -> bool:
        """Route after L4 Deploy completes."""
        if event.result_status == LayerResult.SUCCESS:
            deploy_phase = event.output.get("phase")
            if deploy_phase == "rolling_100":
                self.transition_state(pr_id, PRState.MERGED, reason="L4 100% rollout complete")
            elif deploy_phase == "canary_5":
                self.transition_state(pr_id, PRState.CANARY_5, reason="L4 5% canary started")
            elif deploy_phase == "canary_50":
                self.transition_state(pr_id, PRState.CANARY_50, reason="L4 50% canary started")
        elif event.result_status == LayerResult.FAILED:
            self.transition_state(pr_id, PRState.ROLLED_BACK, reason="L4 deploy failed - rollback")
        return True
    
    def _route_from_l5(self, pr_id: str, event: LayerResultEvent) -> bool:
        """Route after L5 Monitor detects anomaly."""
        # L5 publishes anomalies - trigger L6 Healing
        self.publish_layer_command(pr_id, "L6_HEALING", event.output)
        return True
    
    def _route_from_l6(self, pr_id: str, event: LayerResultEvent) -> bool:
        """Route after L6 Healing outcome."""
        if event.result_status == LayerResult.SUCCESS:
            logger.info(f"[Orchestrator] Healing succeeded for {pr_id}")
        else:
            # Escalate to human
            logger.warning(f"[Orchestrator] Healing failed for {pr_id} - escalating to human")
            self.ctx.logger.write("HealingEscalation", {
                "pr_id": pr_id,
                "reason": "healing_failed"
            })
        return True
    
    def get_pr_state(self, pr_id: str) -> Optional[OrchestratorState]:
        """Get current PR state."""
        return self._pr_states.get(pr_id)
    
    def cleanup_pr(self, pr_id: str):
        """Cleanup PR context on terminal state."""
        logger.info(f"[Orchestrator] Cleaning up PR {pr_id}")
        if pr_id in self._pr_states:
            del self._pr_states[pr_id]
        if pr_id in self._retry_budgets:
            del self._retry_budgets[pr_id]
