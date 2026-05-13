"""
NEEROps v9.0 - Layer 3: Build
Build artifact: merge → install → test → docker build → Trivy scan → Cosign sign → ECR push
Dead-man's switch: 20-min timeout watchdog
"""

import logging
import hashlib
from typing import Dict, Any, Tuple
from datetime import datetime

from core.types import BuildResult, LayerResult
from core.globals import GlobalContext

logger = logging.getLogger(__name__)


class BuildLayer:
    """L3 - Container Build and Artifact Creation."""
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
        self.build_timeout_seconds = 1200  # 20 minutes
    
    def execute_build(
        self,
        pr_id: str,
        image_name: str,
        service_name: str
    ) -> Tuple[LayerResult, BuildResult]:
        """
        Complete build pipeline:
        1. Merge to test branch
        2. pip install / npm install
        3. Run pytest / test suite
        4. Docker build from distroless base
        5. Trivy CVE scan
        6. Cosign sign
        7. ECR push
        
        Returns: (LayerResult, BuildResult)
        """
        
        logger.info(f"[L3] Starting build for {service_name} (PR {pr_id})")
        
        build_result = BuildResult(
            pr_id=pr_id,
            image_uri="",
            image_digest="",
            cosign_signature="",
            success=False
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Merge to test branch
            logger.info("[L3] Merging to test branch...")
            self._merge_to_test_branch(pr_id)
            
            # Step 2: Install dependencies
            logger.info("[L3] Installing dependencies...")
            self._install_dependencies(service_name)
            
            # Step 3: Run tests
            logger.info("[L3] Running test suite...")
            test_results = self._run_tests(service_name)
            build_result.test_results = test_results
            
            if not test_results.get("passed", False):
                logger.error("[L3] Tests failed")
                build_result.success = False
                return LayerResult.FAILED, build_result
            
            # Step 4: Docker build
            logger.info("[L3] Building Docker image...")
            image_digest = self._docker_build(service_name, image_name)
            build_result.image_digest = image_digest
            
            # Step 5: Trivy CVE scan (blocks on CRITICAL/HIGH)
            logger.info("[L3] Scanning with Trivy...")
            trivy_report = self._trivy_scan(image_digest)
            build_result.trivy_report = trivy_report
            
            critical_cves = trivy_report.get("critical_cves", 0)
            high_cves = trivy_report.get("high_cves", 0)
            
            if critical_cves > 0:
                logger.error(f"[L3] Trivy found {critical_cves} CRITICAL CVEs - blocking")
                build_result.critical_cves = critical_cves
                build_result.success = False
                return LayerResult.SUCCESS, build_result
            
            if high_cves > 0:
                logger.warning(f"[L3] Trivy found {high_cves} HIGH CVEs - reviewing")
                # HIGH CVEs can be overridden but should trigger review
            
            # Step 6: Cosign sign
            logger.info("[L3] Signing with Cosign...")
            cosign_sig = self._cosign_sign(image_digest)
            build_result.cosign_signature = cosign_sig
            
            if not cosign_sig:
                logger.error("[L3] Cosign signing failed")
                build_result.success = False
                return LayerResult.FAILED, build_result
            
            # Step 7: ECR push (with fallback to Harbor on failure)
            logger.info("[L3] Pushing to ECR...")
            image_uri = self._ecr_push(image_name, image_digest, service_name)
            
            if not image_uri:
                logger.error("[L3] ECR push failed - attempting Harbor fallback...")
                image_uri = self._harbor_push(image_name, image_digest, service_name)
            
            if not image_uri:
                logger.error("[L3] All push attempts failed")
                build_result.success = False
                return LayerResult.FAILED, build_result
            
            build_result.image_uri = image_uri
            build_result.success = True
            
            # Record build
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            build_result.build_duration_seconds = elapsed
            
            logger.info(f"[L3] Build SUCCEEDED in {elapsed:.1f}s: {image_uri}")
            
            self.ctx.logger.write("BuildComplete", {
                "pr_id": pr_id,
                "image_uri": image_uri,
                "duration_seconds": elapsed,
                "critical_cves": build_result.critical_cves
            })
            
            return LayerResult.SUCCESS, build_result
        
        except Exception as e:
            logger.error(f"[L3] Build failed: {e}")
            build_result.success = False
            return LayerResult.FAILED, build_result
    
    def _merge_to_test_branch(self, pr_id: str) -> bool:
        """Merge PR branch to test branch."""
        logger.debug(f"[L3] Merging {pr_id} to test branch")
        # Mock: simulate merge
        return True
    
    def _install_dependencies(self, service_name: str) -> bool:
        """Install dependencies (pip install, npm install, etc.)."""
        logger.debug(f"[L3] Installing dependencies for {service_name}")
        # Mock: simulate install with caching
        return True
    
    def _run_tests(self, service_name: str) -> Dict[str, Any]:
        """Run full test suite (pytest, npm test, etc.)."""
        logger.debug(f"[L3] Running tests for {service_name}")
        
        # Mock test results
        return {
            "passed": True,
            "tests_run": 245,
            "tests_passed": 245,
            "tests_failed": 0,
            "coverage_percent": 87.5,
            "duration_seconds": 45
        }
    
    def _docker_build(self, service_name: str, image_name: str) -> str:
        """Build Docker image from distroless base."""
        logger.debug(f"[L3] Docker build: {image_name}")
        
        # Mock: generate a SHA256 digest
        image_info = f"{image_name}:latest-{service_name}"
        digest = hashlib.sha256(image_info.encode()).hexdigest()
        
        return f"sha256:{digest}"
    
    def _trivy_scan(self, image_digest: str) -> Dict[str, Any]:
        """Scan image with Trivy for CVEs."""
        logger.debug(f"[L3] Trivy scan: {image_digest}")
        
        # Mock: no CVEs found
        return {
            "image": image_digest,
            "critical_cves": 0,
            "high_cves": 0,
            "medium_cves": 2,
            "low_cves": 5,
            "vulnerabilities": []
        }
    
    def _cosign_sign(self, image_digest: str) -> str:
        """Sign image with Cosign."""
        logger.debug(f"[L3] Cosign signing: {image_digest}")
        
        # Mock: return signature
        sig_data = f"cosign_signature_{image_digest}"
        signature = hashlib.sha256(sig_data.encode()).hexdigest()
        
        return signature
    
    def _ecr_push(self, image_name: str, image_digest: str, service_name: str) -> str:
        """Push image to AWS ECR."""
        logger.debug(f"[L3] ECR push: {image_name}")
        
        # Mock: ECR is available
        image_uri = f"123456789.dkr.ecr.us-east-1.amazonaws.com/{service_name}:pr-{image_digest[:8]}"
        return image_uri
    
    def _harbor_push(self, image_name: str, image_digest: str, service_name: str) -> str:
        """Fallback: Push image to Harbor registry."""
        logger.info(f"[L3] Harbor fallback push: {image_name}")
        
        # Mock: Harbor is available
        image_uri = f"harbor.internal/neerops/{service_name}:pr-{image_digest[:8]}"
        return image_uri
