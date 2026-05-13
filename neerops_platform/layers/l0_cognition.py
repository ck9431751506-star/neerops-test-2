"""
NEEROps v9.0 - Layer 0: Cognition
Solver Selection - Heuristic vs RL vs LLM vs Human
L0 selects which solver tier to use based on problem type, risk score, and confidence thresholds.
"""

import logging
from typing import Dict, Any, Tuple
from enum import Enum

from core.types import SolverType, LayerResult
from core.globals import GlobalContext

logger = logging.getLogger(__name__)


class CognitionSolver:
    """L0 Cognition - Autonomous solver selection."""
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
        self._solver_scores = {
            SolverType.HEURISTIC: 0.0,
            SolverType.RL_MODEL: 0.0,
            SolverType.LOCAL_MODEL: 0.0,
            SolverType.LLM_API: 0.0,
            SolverType.HUMAN: 0.0,
        }
    
    def select_solver(
        self,
        problem_type: str,
        context: Dict[str, Any],
        risk_score: float = 0.5,
        novelty_score: float = 0.0
    ) -> Tuple[SolverType, float]:
        """
        Select appropriate solver based on problem characteristics.
        
        Decision tree (deterministic first):
        1. If heuristic match score >= 0.5 -> use HEURISTIC
        2. Else if RL confidence >= 0.7 -> use RL_MODEL
        3. Else if local model confidence >= 0.8 -> use LOCAL_MODEL
        4. Else if severity >= HIGH AND novelty > 0.6 -> use LLM_API
        5. Else -> HUMAN
        
        Returns: (solver_type, confidence_score)
        """
        
        logger.info(f"[L0 Cognition] Selecting solver for {problem_type} (risk={risk_score}, novelty={novelty_score})")
        
        # TIER 1: Heuristic lookup
        heuristic_score = self._score_heuristic(problem_type, context)
        if heuristic_score >= 0.5:
            logger.info(f"[L0] Selected HEURISTIC (score={heuristic_score})")
            self.ctx.logger.write("CognitionDecision", {
                "problem_type": problem_type,
                "selected_solver": "HEURISTIC",
                "confidence": heuristic_score
            })
            return SolverType.HEURISTIC, heuristic_score
        
        # TIER 2: RL Model
        rl_score = self._score_rl_model(problem_type, context)
        if rl_score >= 0.7:
            logger.info(f"[L0] Selected RL_MODEL (score={rl_score})")
            self.ctx.logger.write("CognitionDecision", {
                "problem_type": problem_type,
                "selected_solver": "RL_MODEL",
                "confidence": rl_score
            })
            return SolverType.RL_MODEL, rl_score
        
        # TIER 2b: Embedding Cache (semantic lookup)
        embedding_score = self._score_embedding_cache(problem_type, context)
        if embedding_score >= 0.92:
            logger.info(f"[L0] Selected EMBEDDING_CACHE via semantic match (score={embedding_score})")
            return SolverType.RL_MODEL, embedding_score  # Treat as RL tier
        
        # TIER 3: Local Model
        local_model_score = self._score_local_model(problem_type, context)
        if local_model_score >= 0.8:
            logger.info(f"[L0] Selected LOCAL_MODEL (score={local_model_score})")
            return SolverType.LOCAL_MODEL, local_model_score
        
        # TIER 4: Full LLM API (only if conditions met)
        severity = context.get("severity", "MEDIUM")
        if severity in ["HIGH", "CRITICAL"] or novelty_score > 0.6:
            llm_score = self._score_llm(problem_type, context)
            if llm_score > 0.5:
                logger.info(f"[L0] Selected LLM_API (score={llm_score})")
                self.ctx.logger.write("CognitionDecision", {
                    "problem_type": problem_type,
                    "selected_solver": "LLM_API",
                    "confidence": llm_score,
                    "severity": severity,
                    "novelty": novelty_score
                })
                return SolverType.LLM_API, llm_score
        
        # TIER 5: Human escalation
        logger.warning(f"[L0] Escalating to HUMAN for {problem_type}")
        self.ctx.logger.write("CognitionDecision", {
            "problem_type": problem_type,
            "selected_solver": "HUMAN",
            "reason": "all_tiers_failed"
        })
        return SolverType.HUMAN, 0.0
    
    def _score_heuristic(self, problem_type: str, context: Dict[str, Any]) -> float:
        """
        Score match against Heuristic Library.
        In production: query PostgreSQL heuristics table with semantic embedding.
        Mock: return based on problem type patterns.
        """
        # Mock scoring based on known patterns
        if "OOMKill" in problem_type:
            return 0.95
        elif "CrashLoop" in problem_type:
            return 0.90
        elif "HighLatency" in problem_type:
            return 0.75
        elif "HighCPU" in problem_type:
            return 0.80
        
        return 0.3  # Low confidence for unknown patterns
    
    def _score_rl_model(self, problem_type: str, context: Dict[str, Any]) -> float:
        """
        Score RL model confidence.
        In production: load trained PPO model and evaluate.
        Mock: return based on problem familiarity.
        """
        # Mock RL scoring - variations of known patterns
        if "OOMKill" in problem_type or "HighMemory" in problem_type:
            return 0.75
        elif "HighCPU" in problem_type:
            return 0.72
        elif "HighLatency" in problem_type:
            return 0.70
        
        return 0.45
    
    def _score_embedding_cache(self, problem_type: str, context: Dict[str, Any]) -> float:
        """
        Score semantic similarity to cached resolutions.
        Mock: return based on exact match likelihood.
        """
        # In production: use pgvector cosine similarity
        if "OOMKill" in problem_type:
            return 0.93  # Very similar to cached incident
        
        return 0.5
    
    def _score_local_model(self, problem_type: str, context: Dict[str, Any]) -> float:
        """
        Score local model (small 7B quantized model).
        Mock: return moderate confidence for complex problems.
        """
        # Local model handles medium-complexity incidents
        return 0.65
    
    def _score_llm(self, problem_type: str, context: Dict[str, Any]) -> float:
        """
        Score LLM appropriateness.
        Mock: return high score for novel/complex problems.
        """
        # Only invoke LLM for genuinely novel problems
        if "novel" in problem_type.lower() or "unknown" in problem_type.lower():
            return 0.88
        
        return 0.45
    
    def execute_heuristic(self, rule_data: Dict[str, Any]) -> bool:
        """Execute heuristic rule action."""
        logger.info(f"[L0] Executing heuristic rule: {rule_data}")
        self.ctx.logger.write("HeuristicExecution", rule_data)
        return True
    
    def execute_rl_action(self, action: str, params: Dict[str, Any]) -> bool:
        """Execute RL-selected action."""
        logger.info(f"[L0] Executing RL action: {action} with params {params}")
        self.ctx.logger.write("RLExecution", {"action": action, "params": params})
        return True
    
    def execute_llm_diagnosis(self, problem_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM diagnosis and get action plan."""
        logger.info(f"[L0] Executing LLM diagnosis...")
        
        # In production: call LLM API with rate limiting and budget checks
        plan = {
            "diagnosis": "Simulated LLM diagnosis",
            "recommended_action": "scale_replicas",
            "action_params": {"increment": 2},
            "confidence": 0.87
        }
        
        self.ctx.logger.write("LLMDiagnosis", plan)
        return plan
