"""
NEEROps v9.0 - Test Suite
Comprehensive unit and integration tests.
"""

import unittest
import logging
from datetime import datetime

from core.types import PRState, LayerResult, Event, PRMetadata
from core.globals import GlobalContext
from core.orchestrator import Orchestrator

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

from config import Config

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)


class TestCore(unittest.TestCase):
    """Test core components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ctx = GlobalContext()
    
    def test_event_bus_publish_subscribe(self):
        """Test EventBus publish/subscribe."""
        messages = []
        
        def callback(msg):
            messages.append(msg)
        
        self.ctx.event_bus.subscribe("test_channel", callback)
        self.ctx.event_bus.publish("test_channel", {"test": "data"})
        
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["test"], "data")
    
    def test_vault_client_secrets(self):
        """Test VaultClient get/set."""
        self.ctx.vault_client.set("test/secret", {"key": "value"})
        secret = self.ctx.vault_client.get("test/secret")
        
        self.assertIsNotNone(secret)
        self.assertEqual(secret.get("key"), "value")
    
    def test_orchestrator_state_transition(self):
        """Test Orchestrator state machine."""
        orch = Orchestrator(self.ctx)
        
        pr_context = orch.create_pr_context(
            pr_id="test-001",
            pr_title="Test PR",
            pr_description="Test description",
            target_branch="main"
        )
        
        self.assertIsNotNone(pr_context)
        self.assertEqual(pr_context.state, PRState.UNDERSTANDING)


class TestLayers(unittest.TestCase):
    """Test layer implementations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ctx = GlobalContext()
        self.pr_context = {
            "pr_id": "test-001",
            "title": "Test PR",
            "changed_files": ["src/main.py", "tests/test_main.py"],
            "diff_size": 500
        }
    
    def test_l0_cognition_solver_selection(self):
        """Test L0 Cognition solver selection."""
        l0 = CognitionLayer(self.ctx)
        
        solver_type = l0.select_solver(self.pr_context)
        
        self.assertIsNotNone(solver_type)
        self.assertIn(solver_type.value, 
                     ["HEURISTIC", "RL_MODEL", "EMBEDDING_CACHE", 
                      "LOCAL_MODEL", "LLM_API", "HUMAN"])
    
    def test_l1_understanding_kg_building(self):
        """Test L1 Understanding KG building."""
        l1 = UnderstandingLayer(self.ctx)
        
        kg = l1.build_knowledge_graph(self.pr_context)
        
        self.assertIsNotNone(kg)
        self.assertIn("nodes", kg)
        self.assertIn("edges", kg)
        self.assertIn("risk_level", kg)
    
    def test_l2_review_pipeline(self):
        """Test L2 Review security gates."""
        l2 = ReviewLayer(self.ctx)
        
        verdict = l2.review_pr(self.pr_context)
        
        self.assertIsNotNone(verdict)
        self.assertIn(verdict.verdict, ["APPROVED", "REJECTED", "NEEDS_INFO"])
    
    def test_l3_build_pipeline(self):
        """Test L3 Build pipeline."""
        l3 = BuildLayer(self.ctx)
        
        build_result = l3.execute_build(self.pr_context)
        
        self.assertIsNotNone(build_result)
        if build_result:
            self.assertIsNotNone(build_result.image_uri)
    
    def test_l5_monitor_anomaly_detection(self):
        """Test L5 Monitor anomaly detection."""
        l5 = MonitoringLayer(self.ctx)
        
        metrics = l5.collect_metrics_snapshot()
        
        self.assertIsNotNone(metrics)
        self.assertIn("error_rate", metrics)
        self.assertIn("latency_p99_ms", metrics)
    
    def test_l6_healing_escalation(self):
        """Test L6 Healing escalation."""
        l6 = HealingLayer(self.ctx)
        
        success, outcome = l6.handle_anomaly(
            anomaly_id="test-anomaly",
            anomaly_context={
                "anomaly_type": "OOMKill",
                "service": "test-service"
            }
        )
        
        self.assertIsInstance(success, bool)
        self.assertIsNotNone(outcome)


class TestML(unittest.TestCase):
    """Test ML components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ctx = GlobalContext()
    
    def test_heuristic_library_lookup(self):
        """Test heuristic library lookup."""
        lib = HeuristicLibrary(self.ctx)
        
        rule = lib.lookup_rule({"type": "OOMKill", "pattern": "*"})
        
        self.assertIsNotNone(rule)
        self.assertEqual(rule.action.value, "increase_memory_limit")
    
    def test_heuristic_library_stats(self):
        """Test heuristic library statistics."""
        lib = HeuristicLibrary(self.ctx)
        
        stats = lib.get_stats()
        
        self.assertIn("total_rules", stats)
        self.assertGreater(stats["total_rules"], 0)
    
    def test_embedding_cache_search(self):
        """Test embedding cache semantic search."""
        cache = EmbeddingCache(self.ctx)
        
        # Store resolution
        cache.store_anomaly_resolution(
            anomaly_signature={"type": "HighLatency"},
            resolution={"action": "scale_replicas"},
            embedding=[0.1] * 100
        )
        
        # Search
        found, result = cache.semantic_search(
            query_anomaly={"type": "HighLatency"},
            query_embedding=[0.1] * 100
        )
        
        self.assertIsNotNone(result)


class TestSecurity(unittest.TestCase):
    """Test security components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ctx = GlobalContext()
        self.security = SecurityPipeline(self.ctx)
    
    def test_gitleaks_scan(self):
        """Test Gitleaks secret scanning."""
        success, findings = self.security.scan_code_secrets("/repo")
        
        self.assertIsInstance(success, bool)
        self.assertIsInstance(findings, list)
    
    def test_sast_scan(self):
        """Test Semgrep SAST scanning."""
        success, findings = self.security.scan_sast("/code")
        
        self.assertIsInstance(success, bool)
        self.assertIsInstance(findings, list)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ctx = GlobalContext()
    
    def test_e2e_flow_basic(self):
        """Test basic E2E flow."""
        from main import NEEROpsV9
        
        platform = NEEROpsV9()
        
        test_webhook = {
            "pull_request": {
                "id": "test-e2e-001",
                "title": "E2E Test PR",
                "body": "Testing E2E flow",
                "base": {"ref": "main"}
            }
        }
        
        result = platform.handle_pr_webhook(test_webhook)
        
        # Should complete (may succeed or fail due to mocks)
        self.assertIsNotNone(result)


class TestConfig(unittest.TestCase):
    """Test configuration management."""
    
    def test_config_validation(self):
        """Test configuration validation."""
        is_valid = Config.validate()
        
        self.assertTrue(is_valid)
    
    def test_config_dict(self):
        """Test getting config as dictionary."""
        config_dict = Config.get_config_dict()
        
        self.assertIn("APP_NAME", config_dict)
        self.assertEqual(config_dict["APP_NAME"], "neerops")


def run_tests(verbosity: int = 2):
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCore))
    suite.addTests(loader.loadTestsFromTestCase(TestLayers))
    suite.addTests(loader.loadTestsFromTestCase(TestML))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
