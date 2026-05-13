"""
NEEROps v9.0 - Layer 7: Feedback Loop & RL Training
Collects deployment outcomes, healing traces, user signals.
Daily PPO training on 7-day rolling window.
Shadow deployment: 24h test before promotion.
Reward shaping: 3-dimensional (H1 deploy safety, H2 uptime, H3 cost).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.types import RL_TrainingExample
from core.globals import GlobalContext

logger = logging.getLogger(__name__)


class FeedbackLayer:
    """L7 - Feedback Loop & RL Training."""
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
        self._trajectory_window: List[Dict[str, Any]] = []
        self._training_window_days = 7
        self._ppo_training_schedule = "daily"
        self._shadow_deployment_days = 1
        self._kl_divergence_threshold = 0.1
    
    def collect_deployment_outcome(
        self,
        pr_id: str,
        deployment_result: Dict[str, Any],
        healing_trace: List[Dict[str, Any]],
        final_metrics: Dict[str, float],
        user_signals: Dict[str, Any] = None
    ) -> RL_TrainingExample:
        """
        Collect one deployment trajectory.
        
        Returns: RL_TrainingExample to be stored in QLDB + stored for batched training.
        """
        
        logger.info(f"[L7] Collecting outcome for PR {pr_id}")
        
        try:
            # Compute reward (3D: safety, uptime, cost)
            reward = self._compute_reward(
                deployment_result,
                healing_trace,
                final_metrics,
                user_signals
            )
            
            # Create training example
            example = RL_TrainingExample(
                pr_id=pr_id,
                trajectory_steps=[
                    {
                        "state": {"deployment_result": deployment_result},
                        "action": {"healing_actions": len(healing_trace)},
                        "reward": reward
                    }
                ],
                total_reward=reward,
                deployment_success=deployment_result.get("success", False),
                collected_at=datetime.utcnow()
            )
            
            # Store to QLDB
            self.ctx.logger.write("TrainingExample", example.dict())
            
            # Add to trajectory window
            self._trajectory_window.append(example.dict())
            
            # Trim old trajectories (keep 7-day window)
            cutoff = datetime.utcnow() - timedelta(days=self._training_window_days)
            self._trajectory_window = [
                t for t in self._trajectory_window
                if datetime.fromisoformat(t["collected_at"]) > cutoff
            ]
            
            logger.info(f"[L7] Collected outcome (reward={reward:.3f}, trajectory_size={len(self._trajectory_window)})")
            
            return example
        
        except Exception as e:
            logger.error(f"[L7] Failed to collect outcome: {e}")
            raise
    
    def _compute_reward(
        self,
        deployment_result: Dict[str, Any],
        healing_trace: List[Dict[str, Any]],
        final_metrics: Dict[str, float],
        user_signals: Dict[str, Any]
    ) -> float:
        """
        3D reward computation:
        H1 (Deploy safety): 0.5x weight - zero errors post-deploy
        H2 (Uptime): 0.3x weight - maintain >99.9% availability
        H3 (Cost): 0.2x weight - reduce LLM calls, heuristic efficiency
        """
        
        logger.debug("[L7] Computing 3D reward...")
        
        # H1: Deploy safety
        h1_score = 1.0 if deployment_result.get("success", False) else 0.0
        
        # Penalize if healing was required
        if healing_trace:
            h1_score *= 0.8  # 20% penalty for needing healing
        
        # H2: Uptime
        error_rate = final_metrics.get("error_rate", 0.01)
        h2_score = max(0, 1.0 - (error_rate * 10))  # Linear decay with error rate
        
        # H3: Cost
        # Count LLM calls (expensive) vs heuristic calls (cheap)
        llm_calls = sum(1 for h in healing_trace if h.get("tier") == "LLM_API")
        heuristic_calls = sum(1 for h in healing_trace if h.get("tier") == "HEURISTIC")
        
        if len(healing_trace) > 0:
            heuristic_ratio = heuristic_calls / len(healing_trace)
            h3_score = heuristic_ratio  # Higher ratio = lower cost
        else:
            h3_score = 1.0  # No healing = best cost
        
        # Weighted average
        reward = (h1_score * 0.5) + (h2_score * 0.3) + (h3_score * 0.2)
        
        logger.debug(f"[L7] Reward: H1={h1_score:.2f}, H2={h2_score:.2f}, H3={h3_score:.2f}, total={reward:.2f}")
        
        return reward
    
    def trigger_rl_training(self) -> bool:
        """
        Trigger RL training on trajectory window.
        
        Steps:
        1. Query QLDB for 7-day window
        2. Batch trajectories for PPO training
        3. Train model in shadow environment
        4. Evaluate KL divergence vs current model
        5. If KL < threshold: promote to production
        6. Else: keep current model, retry next day
        """
        
        logger.info(f"[L7] Triggering RL training (window size={len(self._trajectory_window)})")
        
        try:
            # Minimum training examples required
            if len(self._trajectory_window) < 10:
                logger.warning("[L7] Insufficient trajectory data for training")
                return False
            
            # Step 1: Already have trajectories in memory (mock)
            # In production: query QLDB
            
            # Step 2: Batch for PPO training
            batch_metrics = self._prepare_training_batch(self._trajectory_window)
            logger.debug(f"[L7] Prepared batch: {len(batch_metrics)} examples")
            
            # Step 3: Train in shadow
            shadow_model = self._train_rl_model(batch_metrics)
            if not shadow_model:
                logger.error("[L7] Shadow training failed")
                return False
            
            # Step 4: Evaluate KL divergence
            kl_divergence = self._evaluate_kl_divergence(shadow_model)
            logger.info(f"[L7] KL divergence: {kl_divergence:.4f}")
            
            # Step 5: Promote if meets threshold
            if kl_divergence < self._kl_divergence_threshold:
                logger.info("[L7] KL divergence acceptable - promoting shadow model")
                self._promote_shadow_model(shadow_model)
                
                self.ctx.logger.write("RLModelPromoted", {
                    "kl_divergence": kl_divergence,
                    "batch_size": len(batch_metrics),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return True
            else:
                logger.warning(f"[L7] KL divergence too high ({kl_divergence:.4f} > {self._kl_divergence_threshold})")
                return False
        
        except Exception as e:
            logger.error(f"[L7] Training failed: {e}")
            return False
    
    def _prepare_training_batch(self, trajectories: List[Dict[str, Any]]) -> List[Dict]:
        """Prepare trajectories for off-policy PPO training."""
        
        batch = []
        
        for traj in trajectories:
            batch_example = {
                "trajectory": traj["trajectory_steps"],
                "reward": traj["total_reward"],
                "success": traj["deployment_success"]
            }
            batch.append(batch_example)
        
        logger.debug(f"[L7] Prepared batch with {len(batch)} examples")
        
        return batch
    
    def _train_rl_model(self, batch: List[Dict]) -> Optional[Dict[str, Any]]:
        """Train RL model (mock PPO)."""
        
        logger.debug("[L7] Training RL model on batch...")
        
        # Mock: return trained model
        # In production: PyTorch PPO with importance sampling
        
        model = {
            "version": "shadow_" + datetime.utcnow().isoformat(),
            "policy_network_weights": "mock_weights",
            "training_loss": 0.15,
            "policy_entropy": 0.8
        }
        
        return model
    
    def _evaluate_kl_divergence(self, shadow_model: Dict[str, Any]) -> float:
        """Evaluate KL divergence vs production model."""
        
        logger.debug("[L7] Evaluating KL divergence...")
        
        # Mock: compute KL
        # In production: PolicyNetwork.compute_kl_divergence()
        
        kl = 0.05  # Mock: acceptable divergence
        
        return kl
    
    def _promote_shadow_model(self, shadow_model: Dict[str, Any]):
        """Promote shadow model to production."""
        
        logger.info("[L7] Promoting shadow model to production...")
        
        # In production:
        # 1. Update model pointer in L0 Cognition
        # 2. Switch RL solver tier to use new model
        # 3. Archive old model to S3
        # 4. Schedule RL model watchdog
        
        self.ctx.logger.write("RLModelDeployed", {
            "version": shadow_model.get("version"),
            "timestamp": datetime.utcnow().isoformat()
        })
