"""
NEEROps v9.0 - Layer 1: Code & Infra Understanding
Build Knowledge Graph (KG), detect IaC drift, compute risk level.
KG is used by L8 World Model for risk assessment and L6 for pre-computed healing plans.
"""

import logging
from typing import Dict, Any, List, Tuple, Set
from datetime import datetime

from core.types import KnowledgeGraph, LayerResult
from core.globals import GlobalContext

logger = logging.getLogger(__name__)


class CodeUnderstandingLayer:
    """L1 - Code & Infrastructure Understanding."""
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
        self._kg_cache: Dict[str, KnowledgeGraph] = {}
    
    def build_knowledge_graph(
        self,
        pr_id: str,
        pr_diff: Dict[str, Any],
        prev_kg: Dict[str, Any] = None
    ) -> Tuple[LayerResult, KnowledgeGraph]:
        """
        Build or update Knowledge Graph.
        
        Steps:
        1. Fetch PR diff from git API
        2. Determine if incremental or full rebuild
        3. Scan changed files, parse intent
        4. Detect IaC drift (Terraform)
        5. Build KG with nodes (files/services/infra) and edges (dependencies)
        6. Compute risk level from complexity
        
        Returns: (LayerResult, KnowledgeGraph)
        """
        
        logger.info(f"[L1] Building KG for PR {pr_id}")
        
        try:
            # Check if incremental rebuild is warranted
            changed_files = pr_diff.get("changed_files", [])
            delta_ratio = len(changed_files) / max(100, 1)  # Assume ~100 total files
            
            if delta_ratio > 0.20:
                logger.info(f"[L1] Large delta ({delta_ratio*100}%) - full KG rebuild")
                kg = self._build_full_kg(pr_id, pr_diff)
            else:
                logger.info(f"[L1] Small delta ({delta_ratio*100}%) - incremental KG build")
                kg = self._build_incremental_kg(pr_id, pr_diff, prev_kg)
            
            # Cache the KG
            self._kg_cache[pr_id] = kg
            
            logger.info(f"[L1] KG complete: {len(kg.nodes)} nodes, {len(kg.edges)} edges, risk={kg.risk_level}")
            
            self.ctx.logger.write("KGBuilt", {
                "pr_id": pr_id,
                "nodes": len(kg.nodes),
                "edges": len(kg.edges),
                "risk_level": kg.risk_level,
                "iac_drift": kg.iac_drift_detected,
                "incremental": kg.incremental
            })
            
            return LayerResult.SUCCESS, kg
        
        except Exception as e:
            logger.error(f"[L1] KG build failed: {e}")
            # Return partial KG on error
            partial_kg = KnowledgeGraph(
                pr_id=pr_id,
                nodes={},
                edges=[],
                risk_level="CRITICAL",
                partial=True
            )
            return LayerResult.PARTIAL, partial_kg
    
    def _build_full_kg(self, pr_id: str, pr_diff: Dict[str, Any]) -> KnowledgeGraph:
        """Full Knowledge Graph rebuild."""
        kg = KnowledgeGraph(
            pr_id=pr_id,
            nodes={},
            edges=[],
            risk_level="MEDIUM"
        )
        
        # Scan changed files
        changed_files = pr_diff.get("changed_files", [])
        for file_path in changed_files:
            node_id = f"file:{file_path}"
            kg.nodes[node_id] = {
                "type": "file",
                "path": file_path,
                "language": self._detect_language(file_path),
                "complexity": self._estimate_complexity(file_path)
            }
        
        # Detect Helm chart dependencies
        helm_charts = pr_diff.get("helm_charts", [])
        for chart in helm_charts:
            node_id = f"helm:{chart}"
            kg.nodes[node_id] = {
                "type": "helm_chart",
                "name": chart,
                "replicas": 3
            }
            
            # Add edges from files to charts
            for file_path in changed_files:
                if f"{chart}" in file_path:
                    kg.edges.append((f"file:{file_path}", node_id))
        
        # Detect Terraform resources
        tf_resources = pr_diff.get("terraform_resources", [])
        for resource in tf_resources:
            node_id = f"tf:{resource}"
            kg.nodes[node_id] = {
                "type": "terraform",
                "resource": resource,
                "impact": "infrastructure"
            }
        
        # Compute risk level based on complexity and changes
        kg.risk_level = self._compute_risk_level(kg)
        kg.total_node_count = len(kg.nodes)
        kg.incremental = False
        
        # Detect IaC drift
        kg.iac_drift_detected = pr_diff.get("iac_drift_detected", False)
        
        return kg
    
    def _build_incremental_kg(
        self,
        pr_id: str,
        pr_diff: Dict[str, Any],
        prev_kg: Dict[str, Any] = None
    ) -> KnowledgeGraph:
        """Incremental Knowledge Graph build - only update affected subgraph."""
        
        # Start with previous KG or create new
        if prev_kg:
            kg = KnowledgeGraph(**prev_kg)
        else:
            kg = KnowledgeGraph(pr_id=pr_id, nodes={}, edges=[])
        
        # Find affected nodes (reachable from changed files)
        changed_files = pr_diff.get("changed_files", [])
        affected_node_ids = self._find_affected_subgraph(kg, changed_files)
        
        logger.info(f"[L1] Incremental update: {len(affected_node_ids)} nodes affected")
        
        # Remove old affected nodes
        for node_id in affected_node_ids:
            if node_id in kg.nodes:
                del kg.nodes[node_id]
        
        # Remove edges involving affected nodes
        kg.edges = [
            edge for edge in kg.edges
            if edge[0] not in affected_node_ids and edge[1] not in affected_node_ids
        ]
        
        # Re-evaluate affected subgraph
        for file_path in changed_files:
            node_id = f"file:{file_path}"
            kg.nodes[node_id] = {
                "type": "file",
                "path": file_path,
                "language": self._detect_language(file_path),
                "complexity": self._estimate_complexity(file_path)
            }
        
        kg.risk_level = self._compute_risk_level(kg)
        kg.total_node_count = len(kg.nodes)
        kg.delta_node_count = len(affected_node_ids)
        kg.incremental = True
        kg.iac_drift_detected = pr_diff.get("iac_drift_detected", False)
        
        return kg
    
    def _find_affected_subgraph(self, kg: KnowledgeGraph, changed_files: List[str]) -> Set[str]:
        """Find all nodes affected by changed files via dependency edges."""
        affected = set()
        
        # Add directly changed nodes
        for file_path in changed_files:
            node_id = f"file:{file_path}"
            affected.add(node_id)
        
        # Add dependent nodes (BFS on edges)
        queue = list(affected)
        visited = set()
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            # Find edges starting from this node
            for src, dst in kg.edges:
                if src == node_id and dst not in visited:
                    affected.add(dst)
                    queue.append(dst)
        
        return affected
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        if file_path.endswith(".py"):
            return "python"
        elif file_path.endswith(".go"):
            return "golang"
        elif file_path.endswith(".js") or file_path.endswith(".ts"):
            return "typescript"
        elif file_path.endswith(".yaml") or file_path.endswith(".yml"):
            return "yaml"
        elif file_path.endswith(".tf"):
            return "terraform"
        return "unknown"
    
    def _estimate_complexity(self, file_path: str) -> str:
        """Estimate file complexity."""
        # Mock: base on file name patterns
        if "core" in file_path or "main" in file_path:
            return "HIGH"
        elif "test" in file_path or "mock" in file_path:
            return "LOW"
        else:
            return "MEDIUM"
    
    def _compute_risk_level(self, kg: KnowledgeGraph) -> str:
        """Compute PR risk level from KG."""
        num_nodes = len(kg.nodes)
        num_edges = len(kg.edges)
        
        # Higher complexity = higher risk
        complexity_score = num_nodes + (num_edges * 0.5)
        
        if complexity_score > 100:
            return "CRITICAL"
        elif complexity_score > 50:
            return "HIGH"
        elif complexity_score > 20:
            return "MEDIUM"
        else:
            return "LOW"
    
    def detect_iac_drift(self, service_name: str) -> bool:
        """Detect Infrastructure as Code drift from Terraform plan."""
        # Mock: run terraform plan and check for unexpected changes
        logger.info(f"[L1] Checking IaC drift for {service_name}")
        
        # In production: execute terraform plan and parse for drift
        has_drift = False  # Mock result
        
        if has_drift:
            self.ctx.logger.write("IaCDriftDetected", {"service": service_name})
        
        return has_drift
    
    def get_cached_kg(self, pr_id: str) -> KnowledgeGraph:
        """Retrieve cached KG."""
        return self._kg_cache.get(pr_id)
    
    def invalidate_kg_cache(self, pr_id: str):
        """Invalidate KG cache (e.g., on infra change event)."""
        if pr_id in self._kg_cache:
            del self._kg_cache[pr_id]
            logger.info(f"[L1] Invalidated KG cache for {pr_id}")
