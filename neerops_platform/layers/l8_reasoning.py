"""
NEEROps v9.0 - Layer 8: Autonomous Reasoning Engine
World Model: Bayesian causal graph over system metrics.
Goal Engine: Multi-objective reward function (H1: deploy safely, H2: uptime, H3: cost).
Monte Carlo simulation to estimate P(failure), pre-compute healing plans.
"""

import logging
import random
from typing import Dict, Any, List
from datetime import datetime

from core.types import RiskEnvelope
from core.globals import GlobalContext

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """L8 - Autonomous Reasoning Engine."""
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
        self._world_model_cache: Dict[str, RiskEnvelope] = {}
        self._monte_carlo_samples = 500
    
    def assess_deployment_risk(
        self,
        pr_id: str,
        kg: Dict[str, Any],
        live_metrics: Dict[str, float],
        trajectory_store: List[Dict] = None
    ) -> RiskEnvelope:
        """
        Comprehensive risk assessment for deployment.
        
        Steps:
        1. Build Bayesian causal graph from KG + metrics
        2. Run Monte Carlo simulation (500 trajectories)
        3. Compute P(failure), P(SLA breach), P(cost overrun)
        4. Score PR against goals (H1, H2, H3)
        5. Pre-compute top-3 healing plans
        6. Adjust canary gate weight based on risk
        
        Returns: RiskEnvelope with risk scores and healing plans
        """
        
        logger.info(f"[L8] Assessing risk for PR {pr_id}")
        
        try:
            # Check cache first
            if pr_id in self._world_model_cache:
                logger.debug(f"[L8] Using cached risk envelope for {pr_id}")
                return self._world_model_cache[pr_id]
            
            # Build risk scores via Monte Carlo
            risk_scores = self._monte_carlo_simulation(kg, live_metrics)
            
            # Compute goal alignment
            goal_score = self._score_goals(kg, live_metrics)
            
            # Pre-compute healing plans
            healing_plans = self._precompute_healing_plans(kg, risk_scores)
            
            # Compute canary gate adjustment
            gate_adjustment = self._compute_gate_adjustment(risk_scores)
            
            risk_envelope = RiskEnvelope(
                pr_id=pr_id,
                goal_alignment_score=goal_score,
                risk_score=risk_scores.get("overall_risk", 0.5),
                p_failure=risk_scores.get("p_failure", 0.1),
                p_sla_breach=risk_scores.get("p_sla_breach", 0.05),
                p_cost_overrun=risk_scores.get("p_cost_overrun", 0.0),
                pre_computed_healing_plans=healing_plans,
                canary_gate_weight_adjustment=gate_adjustment
            )
            
            # Cache the envelope
            self._world_model_cache[pr_id] = risk_envelope
            
            logger.info(f"[L8] Risk assessment complete: P(failure)={risk_scores.get('p_failure', 0):.2%}")
            
            self.ctx.logger.write("RiskEnvelopeGenerated", {
                "pr_id": pr_id,
                "goal_alignment": goal_score,
                "risk_score": risk_envelope.risk_score,
                "p_failure": risk_scores.get("p_failure", 0),
                "gate_adjustment": gate_adjustment
            })
            
            return risk_envelope
        
        except Exception as e:
            logger.error(f"[L8] Risk assessment failed: {e}")
            # Return neutral risk envelope
            return RiskEnvelope(
                pr_id=pr_id,
                goal_alignment_score=0.5,
                risk_score=0.5
            )
    
    def _monte_carlo_simulation(
        self,
        kg: Dict[str, Any],
        live_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Run Monte Carlo simulation over Bayesian causal graph.
        Sample 500 trajectories to estimate failure probabilities.
        """
        
        logger.debug("[L8] Running Monte Carlo simulation...")
        
        failure_count = 0
        sla_breach_count = 0
        
        for _ in range(self._monte_carlo_samples):
            # Simulate a trajectory
            trajectory = self._simulate_trajectory(kg, live_metrics)
            
            if trajectory.get("failed", False):
                failure_count += 1
            
            if trajectory.get("sla_breach", False):
                sla_breach_count += 1
        
        p_failure = failure_count / self._monte_carlo_samples
        p_sla_breach = sla_breach_count / self._monte_carlo_samples
        
        return {
            "p_failure": p_failure,
            "p_sla_breach": p_sla_breach,
            "p_cost_overrun": 0.02,  # Mock: low cost risk
            "overall_risk": (p_failure * 0.6) + (p_sla_breach * 0.3) + 0.02  # Weighted average
        }
    
    def _simulate_trajectory(self, kg: Dict[str, Any], metrics: Dict[str, float]) -> Dict[str, Any]:
        """Simulate a single deployment trajectory."""
        
        # Mock: randomly determine outcome based on metrics
        error_rate = metrics.get("error_rate", 0.01)
        latency = metrics.get("latency_p99_ms", 500)
        
        # Higher existing error rate = higher failure probability
        base_failure_prob = min(error_rate * 10, 0.5)
        
        trajectory = {
            "failed": random.random() < base_failure_prob,
            "sla_breach": latency > 1000 or error_rate > 0.01
        }
        
        return trajectory
    
    def _score_goals(self, kg: Dict[str, Any], metrics: Dict[str, float]) -> float:
        """
        Score PR against goals:
        H1: Deploy safely (no bugs, security)
        H2: Maintain uptime >= 99.9%
        H3: Reduce LLM cost
        """
        
        # Mock: compute goal score (0-1)
        # In production: compute based on actual risk factors
        
        goal_scores = {
            "H1_safe_deploy": 0.85,  # Based on test coverage, security scans
            "H2_uptime": 0.92,  # Based on baseline metrics
            "H3_llm_cost": 0.95  # Based on heuristic hit rate
        }
        
        # Weighted average
        overall_score = (
            goal_scores["H1_safe_deploy"] * 0.5 +
            goal_scores["H2_uptime"] * 0.3 +
            goal_scores["H3_llm_cost"] * 0.2
        )
        
        return overall_score
    
    def _precompute_healing_plans(
        self,
        kg: Dict[str, Any],
        risk_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Pre-compute top-3 most likely healing actions for probable failure modes."""
        
        plans = [
            {
                "rank": 1,
                "failure_mode": "OOMKill",
                "healing_action": "increase_memory_limit",
                "priority": 1
            },
            {
                "rank": 2,
                "failure_mode": "HighLatency",
                "healing_action": "scale_replicas",
                "priority": 2
            },
            {
                "rank": 3,
                "failure_mode": "CrashLoop",
                "healing_action": "restart_pod",
                "priority": 3
            }
        ]
        
        return plans
    
    def _compute_gate_adjustment(self, risk_scores: Dict[str, float]) -> float:
        """
        Compute canary gate weight adjustment.
        Higher risk = higher P(advance) threshold.
        
        Default gate: P(new >= baseline) >= 0.95
        Adjusted: P >= 0.95 + adjustment
        """
        
        overall_risk = risk_scores.get("overall_risk", 0.5)
        
        # Map risk to gate adjustment
        # 0.0 risk -> 0.0 adjustment (lower threshold)
        # 0.5 risk -> 0.02 adjustment
        # 1.0 risk -> 0.10 adjustment
        
        adjustment = overall_risk * 0.10
        
        return adjustment
