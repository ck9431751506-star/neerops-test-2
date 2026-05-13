"""
NEEROps v9.0 - Main Entry Point
Initializes all components and provides main execution loop.
Listens for GitHub PR webhooks and orchestrates end-to-end flow.
"""

import logging
import sys
from typing import Dict, Any

# Import all layers
from core.globals import GlobalContext
from core.orchestrator import Orchestrator
from core.types import Event, PRState, LayerCommand

from layers.l0_cognition import CognitionLayer
from layers.l1_understanding import UnderstandingLayer
from layers.l2_review import ReviewLayer
from layers.l3_build import BuildLayer
from layers.l4_deploy import DeploymentLayer
from layers.l5_monitor import MonitoringLayer
from layers.l6_healing import HealingLayer
from layers.l7_feedback import FeedbackLayer
from layers.l8_reasoning import ReasoningEngine
from layers.l9_metalearning import MetaLearningLayer

from ml.heuristic_library import HeuristicLibrary
from ml.embedding_cache import EmbeddingCache

from security.security_pipeline import SecurityPipeline

from supervisor.autonomy_supervisor import AutonomySupervisor

logger = logging.getLogger(__name__)


class NEEROpsV9:
    """NEEROps v9.0 Autonomous DevOps Platform."""
    
    def __init__(self):
        """Initialize NEEROps platform with all components."""
        
        logger.info("=" * 80)
        logger.info("NEEROps v9.0 - Goal-Centric Autonomous DevOps Platform")
        logger.info("=" * 80)
        
        # Initialize global context (singletons)
        self.ctx = GlobalContext()
        
        # Initialize orchestrator
        self.orchestrator = Orchestrator(self.ctx)
        
        # Initialize all layers
        self.l0_cognition = CognitionLayer(self.ctx)
        self.l1_understanding = UnderstandingLayer(self.ctx)
        self.l2_review = ReviewLayer(self.ctx)
        self.l3_build = BuildLayer(self.ctx)
        self.l4_deploy = DeploymentLayer(self.ctx)
        self.l5_monitor = MonitoringLayer(self.ctx)
        self.l6_healing = HealingLayer(self.ctx)
        self.l7_feedback = FeedbackLayer(self.ctx)
        self.l8_reasoning = ReasoningEngine(self.ctx)
        self.l9_metalearning = MetaLearningLayer(self.ctx)
        
        # Initialize ML components
        self.heuristic_library = HeuristicLibrary(self.ctx)
        self.embedding_cache = EmbeddingCache(self.ctx)
        
        # Initialize security
        self.security_pipeline = SecurityPipeline(self.ctx)
        
        # Initialize supervisor
        self.supervisor = AutonomySupervisor(self.ctx)
        
        logger.info("[NEEROps] All components initialized")
        logger.info(f"[NEEROps] Heuristic library: {self.heuristic_library.get_stats()}")
    
    def start(self):
        """Start the NEEROps platform."""
        
        logger.info("[NEEROps] Starting platform...")
        
        # Start autonomy supervisor
        self.supervisor.start()
        
        # Start monitoring
        # self.l5_monitor.start_monitoring()  # Would run continuously
        
        logger.info("[NEEROps] Platform ready to accept PRs")
    
    def handle_pr_webhook(self, webhook_payload: Dict[str, Any]) -> bool:
        """
        Handle incoming PR webhook from GitHub/Bitbucket.
        
        E2E Flow (§04):
        Step 1: Create PR context (lock, tracing)
        Step 2: L0 Cognition: Solver selection
        Step 3: L1 Understanding: Build KG
        Step 4: L2 Review: Security gates
        Step 5: L3 Build: Container build
        Step 6: L8 Reasoning: Risk assessment + healing plans
        Step 7: L4 Deploy: Bayesian canary
        Step 8: L5 Monitor: Real-time anomalies
        Step 9: L6 Healing: Autonomous recovery
        Step 10: L7 Feedback: Collect outcomes
        Step 11: L9 Meta-Learning: System evolution
        """
        
        pr_id = webhook_payload.get("pull_request", {}).get("id", "unknown")
        
        logger.info(f"[NEEROps] Received PR webhook: {pr_id}")
        
        try:
            # ─────────────────────────────────────────────────────────────
            # Step 1: Create PR context (Orchestrator)
            # ─────────────────────────────────────────────────────────────
            
            pr_context = self.orchestrator.create_pr_context(
                pr_id=pr_id,
                pr_title=webhook_payload.get("pull_request", {}).get("title", ""),
                pr_description=webhook_payload.get("pull_request", {}).get("body", ""),
                target_branch=webhook_payload.get("pull_request", {}).get("base", {}).get("ref", "main")
            )
            
            if not pr_context:
                logger.error(f"[NEEROps] Failed to create PR context")
                return False
            
            # ─────────────────────────────────────────────────────────────
            # Step 2: L0 Cognition - Solver Selection
            # ─────────────────────────────────────────────────────────────
            
            solver_type = self.l0_cognition.select_solver(pr_context)
            logger.info(f"[NEEROps] Selected solver: {solver_type}")
            
            # ─────────────────────────────────────────────────────────────
            # Step 3: L1 Understanding - Knowledge Graph
            # ─────────────────────────────────────────────────────────────
            
            kg = self.l1_understanding.build_knowledge_graph(pr_context)
            logger.info(f"[NEEROps] Built KG with {len(kg.get('nodes', {}))} nodes")
            
            # ─────────────────────────────────────────────────────────────
            # Step 4: L2 Review - Security Gates
            # ─────────────────────────────────────────────────────────────
            
            verdict = self.l2_review.review_pr(pr_context)
            if verdict.verdict == "REJECTED":
                logger.error(f"[NEEROps] PR rejected at review: {verdict.violations}")
                self.orchestrator.transition_state(pr_id, PRState.FAILED, "review_rejected")
                return False
            
            logger.info(f"[NEEROps] Review verdict: {verdict.verdict}")
            
            # ─────────────────────────────────────────────────────────────
            # Step 5: L3 Build - Container Build
            # ─────────────────────────────────────────────────────────────
            
            build_result = self.l3_build.execute_build(pr_context)
            if not build_result:
                logger.error(f"[NEEROps] Build failed")
                self.orchestrator.transition_state(pr_id, PRState.FAILED, "build_failed")
                return False
            
            logger.info(f"[NEEROps] Build successful: {build_result.image_uri}")
            
            # ─────────────────────────────────────────────────────────────
            # Step 6: L8 Reasoning - Risk Assessment
            # ─────────────────────────────────────────────────────────────
            
            live_metrics = self.l5_monitor.collect_metrics_snapshot()
            risk_envelope = self.l8_reasoning.assess_deployment_risk(
                pr_id=pr_id,
                kg=kg,
                live_metrics=live_metrics
            )
            
            logger.info(f"[NEEROps] Risk assessment: {risk_envelope.risk_score:.2f}")
            
            # ─────────────────────────────────────────────────────────────
            # Step 7: L4 Deploy - Bayesian Canary
            # ─────────────────────────────────────────────────────────────
            
            deploy_success, deploy_result = self.l4_deploy.execute_deployment(
                pr_id=pr_id,
                image_uri=build_result.image_uri,
                live_baseline_metrics=live_metrics,
                risk_envelope=risk_envelope.dict()
            )
            
            if not deploy_success:
                logger.error(f"[NEEROps] Deployment failed: {deploy_result.get('rollback_reason')}")
                self.orchestrator.transition_state(pr_id, PRState.ROLLED_BACK, "deploy_failed")
                return False
            
            logger.info(f"[NEEROps] Deployment successful")
            
            # ─────────────────────────────────────────────────────────────
            # Step 8: L5 Monitor - Real-time Anomalies
            # ─────────────────────────────────────────────────────────────
            
            # L5 would run continuously in background monitoring
            # Anomalies feed into L6 Healing
            
            # ─────────────────────────────────────────────────────────────
            # Step 9: L6 Healing - Autonomous Recovery
            # ─────────────────────────────────────────────────────────────
            
            # Would be triggered on anomaly detection from L5
            
            # ─────────────────────────────────────────────────────────────
            # Step 10: L7 Feedback - Collect Outcomes
            # ─────────────────────────────────────────────────────────────
            
            final_metrics = self.l5_monitor.collect_metrics_snapshot()
            training_example = self.l7_feedback.collect_deployment_outcome(
                pr_id=pr_id,
                deployment_result=deploy_result,
                healing_trace=[],  # Would collect from L6
                final_metrics=final_metrics
            )
            
            logger.info(f"[NEEROps] Collected training example with reward: {training_example.total_reward:.3f}")
            
            # ─────────────────────────────────────────────────────────────
            # Step 11: L9 Meta-Learning - System Evolution
            # ─────────────────────────────────────────────────────────────
            
            # Scheduled: prompt evolution, LLM release evaluation, threshold optimization
            
            # ─────────────────────────────────────────────────────────────
            # Final: Mark PR as merged
            # ─────────────────────────────────────────────────────────────
            
            self.orchestrator.transition_state(pr_id, PRState.MERGED, "deployment_successful")
            
            logger.info(f"[NEEROps] PR {pr_id} completed successfully")
            
            self.ctx.logger.write("PRCompleted", {
                "pr_id": pr_id,
                "timestamp": str(__import__('datetime').datetime.utcnow())
            })
            
            return True
        
        except Exception as e:
            logger.error(f"[NEEROps] E2E flow failed: {e}")
            self.orchestrator.transition_state(pr_id, PRState.FAILED, f"exception: {str(e)}")
            return False
    
    def scheduled_tasks(self):
        """
        Run scheduled maintenance tasks.
        
        - Daily: L7 RL training
        - Weekly: L9 prompt evolution, LLM benchmarking
        - Monthly: L9 architecture proposals
        - Hourly: Closed-loop feedback aggregation
        """
        
        logger.info("[NEEROps] Running scheduled tasks...")
        
        # Daily: RL training
        self.l7_feedback.trigger_rl_training()
        
        # Weekly: Prompt evolution
        self.l9_metalearning.promote_best_prompt()
        self.l9_metalearning.evaluate_new_llm_releases()
        
        # Monthly: Architecture proposals
        self.l9_metalearning.propose_architecture_changes()
        
        # Threshold optimization
        self.l9_metalearning.optimize_decision_thresholds()
        
        # Heuristic library maintenance
        self.heuristic_library.invalidate_stale_rules(stale_days=30)
        
        logger.info("[NEEROps] Scheduled tasks completed")


def main():
    """Main entry point."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    
    # Initialize platform
    platform = NEEROpsV9()
    
    # Start background processes
    platform.start()
    
    # Example: handle test PR
    test_webhook = {
        "pull_request": {
            "id": "test-pr-001",
            "title": "Add new feature",
            "body": "Adds caching layer to improve performance",
            "base": {
                "ref": "main"
            }
        }
    }
    
    logger.info("[Main] Processing test PR...")
    result = platform.handle_pr_webhook(test_webhook)
    
    if result:
        logger.info("[Main] Test PR processed successfully")
    else:
        logger.error("[Main] Test PR processing failed")
    
    # Run scheduled tasks
    platform.scheduled_tasks()
    
    logger.info("[Main] NEEROps v9.0 demo complete")


if __name__ == "__main__":
    main()
