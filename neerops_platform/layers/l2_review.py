"""
NEEROps v9.0 - Layer 2: Code Review
Security gates: Gitleaks → Semgrep → Mutmut → Pact → Intent matching
Ordered cheapest-first. Any match is a hard block.
"""

import logging
from typing import Dict, Any, List, Tuple

from core.types import ReviewVerdict, LayerResult
from core.globals import GlobalContext

logger = logging.getLogger(__name__)


class CodeReviewLayer:
    """L2 - Automated Code Review."""
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
    
    def review_pr(
        self,
        pr_id: str,
        pr_diff: Dict[str, Any],
        kg: Dict[str, Any] = None
    ) -> Tuple[LayerResult, ReviewVerdict]:
        """
        Comprehensive PR review with ordered security gates.
        
        Pipeline:
        1. Gitleaks (5-15 sec): secrets detection - hard block
        2. Semgrep SAST (30-90 sec): code patterns - HIGH blocks
        3. Mutmut (mutation testing): coverage verification
        4. Pact (contract tests): API compatibility
        5. Intent matching: verify code matches PR intent
        
        Returns: (LayerResult, ReviewVerdict)
        """
        
        logger.info(f"[L2] Starting code review for PR {pr_id}")
        
        verdict = ReviewVerdict(
            pr_id=pr_id,
            verdict="APPROVED",
            gitleaks_passed=False,
            semgrep_passed=False,
            contract_tests_passed=False
        )
        
        try:
            # Gate 1: Gitleaks - no exceptions
            logger.info("[L2] Running Gitleaks (secrets detection)...")
            gitleaks_ok, gitleaks_report = self._run_gitleaks(pr_diff)
            if not gitleaks_ok:
                verdict.verdict = "REJECTED"
                verdict.violations.append("Gitleaks detected secrets in code")
                logger.error("[L2] Gitleaks FAILED - hard block")
                return LayerResult.SUCCESS, verdict
            
            verdict.gitleaks_passed = True
            logger.info("[L2] Gitleaks PASSED")
            
            # Gate 2: Semgrep SAST
            logger.info("[L2] Running Semgrep SAST...")
            semgrep_ok, semgrep_report = self._run_semgrep(pr_diff)
            if not semgrep_ok:
                verdict.verdict = "REJECTED"
                verdict.violations.extend(semgrep_report.get("violations", []))
                logger.error("[L2] Semgrep found HIGH severity issues")
                return LayerResult.SUCCESS, verdict
            
            verdict.semgrep_passed = True
            logger.info("[L2] Semgrep PASSED")
            
            # Gate 3: Mutmut (incremental mutation testing)
            logger.info("[L2] Running Mutmut (mutation testing)...")
            mutmut_score = self._run_mutmut(pr_diff)
            if mutmut_score < 0.80:  # 80% mutation score required
                verdict.verdict = "NEEDS_INFO"
                verdict.mutmut_score = mutmut_score
                verdict.violations.append(f"Mutation score {mutmut_score:.1%} < 80% threshold")
                logger.warning(f"[L2] Mutmut score low: {mutmut_score:.1%}")
                # Don't fail here - let human override if needed
            else:
                verdict.mutmut_score = mutmut_score
                logger.info(f"[L2] Mutmut PASSED ({mutmut_score:.1%})")
            
            # Gate 4: Pact contract tests
            logger.info("[L2] Running Pact contract tests...")
            pact_ok, pact_report = self._run_pact_tests(pr_diff)
            if not pact_ok:
                verdict.verdict = "REJECTED"
                verdict.violations.append("Pact contract tests failed")
                logger.error("[L2] Pact contract tests FAILED")
                return LayerResult.SUCCESS, verdict
            
            verdict.contract_tests_passed = True
            logger.info("[L2] Pact PASSED")
            
            # Gate 5: Intent verification
            logger.info("[L2] Verifying PR intent...")
            intent_ok = self._verify_intent(pr_diff)
            if not intent_ok:
                verdict.verdict = "NEEDS_INFO"
                verdict.violations.append("Code changes do not match PR intent")
            
            if verdict.verdict == "APPROVED":
                logger.info(f"[L2] Review APPROVED for {pr_id}")
            
            return LayerResult.SUCCESS, verdict
        
        except Exception as e:
            logger.error(f"[L2] Review failed: {e}")
            verdict.verdict = "REJECTED"
            verdict.violations.append(f"Review error: {str(e)}")
            return LayerResult.FAILED, verdict
    
    def _run_gitleaks(self, pr_diff: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Run Gitleaks - scan for secrets in commit history.
        This is a hard gate - any match means REJECTED.
        
        In production:
        subprocess.run(['gitleaks', 'detect', '--source', 'github', '--config', ...])
        """
        
        logger.debug("[L2] Gitleaks: scanning commit history for secrets...")
        
        # Mock implementation
        changed_files = pr_diff.get("changed_files", [])
        commit_messages = pr_diff.get("commit_messages", [])
        
        secrets_found = []
        
        # Check for common secret patterns
        secret_patterns = [
            "password=", "secret=", "key=", "token=",
            "api_key", "aws_secret", "private_key"
        ]
        
        for pattern in secret_patterns:
            for commit_msg in commit_messages:
                if pattern in commit_msg.lower():
                    secrets_found.append({
                        "pattern": pattern,
                        "message": commit_msg
                    })
        
        if secrets_found:
            logger.error(f"[L2] Gitleaks found {len(secrets_found)} potential secrets")
            return False, {"violations": secrets_found}
        
        return True, {"violations": []}
    
    def _run_semgrep(self, pr_diff: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Run Semgrep SAST - detect code vulnerabilities.
        HIGH severity findings block the PR.
        
        In production:
        subprocess.run(['semgrep', '--config=p/security-audit', '--json', ...])
        """
        
        logger.debug("[L2] Semgrep: scanning for code vulnerabilities...")
        
        violations = []
        
        # Mock: simulate finding SQL injection vulnerability if PR contains "concat" in SQL
        changed_files = pr_diff.get("changed_files", [])
        for file_path in changed_files:
            if ".py" in file_path or ".sql" in file_path:
                # Simulate detection
                if "sql" in file_path.lower():
                    violations.append({
                        "severity": "MEDIUM",
                        "message": "Potential SQL injection",
                        "file": file_path
                    })
        
        has_high = any(v.get("severity") == "HIGH" for v in violations)
        
        if has_high:
            return False, {"violations": violations}
        
        return True, {"violations": violations}
    
    def _run_mutmut(self, pr_diff: Dict[str, Any]) -> float:
        """
        Run incremental mutation testing.
        Mutates only changed lines (not full suite).
        
        In production:
        mutmut run --paths-to-mutate=<changed_files> --tests-dir=tests/
        """
        
        logger.debug("[L2] Mutmut: running incremental mutation testing...")
        
        # Mock: return score based on file complexity
        changed_files = pr_diff.get("changed_files", [])
        
        # Base score - assume reasonable test coverage
        score = 0.85
        
        # Adjust based on file types
        for file_path in changed_files:
            if "test" in file_path.lower():
                score += 0.05  # Tests are heavily tested
            elif "core" in file_path.lower() or "critical" in file_path.lower():
                score -= 0.10  # Critical paths need better coverage
        
        # Cap between 0 and 1
        return min(1.0, max(0.0, score))
    
    def _run_pact_tests(self, pr_diff: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Run Pact consumer-driven contract tests.
        Verify that API contracts with downstream services are maintained.
        
        In production:
        pytest tests/pact/ --broker-publish-results
        """
        
        logger.debug("[L2] Pact: running contract tests...")
        
        # Mock: contract tests pass
        return True, {"violations": []}
    
    def _verify_intent(self, pr_diff: Dict[str, Any]) -> bool:
        """
        Verify that code changes match the PR intent/title.
        Uses simple pattern matching and semantic analysis.
        """
        
        logger.debug("[L2] Verifying PR intent...")
        
        pr_title = pr_diff.get("title", "").lower()
        commit_messages = pr_diff.get("commit_messages", [])
        
        # Mock: always pass for now
        # In production: use L0 Cognition LLM to verify intent
        
        return True
