"""
NEEROps v9.0 - Layer 5: Continuous Monitor
Collect metrics, run 3-tier anomaly detection, publish to L4/L6/L8.
Tiers: static threshold → 3σ moving average → Bayesian ML prediction
"""

import logging
import math
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from collections import deque

from core.types import AnomalyEvent, AnomalySeverity, SystemMetric
from core.globals import GlobalContext

logger = logging.getLogger(__name__)


class MonitorLayer:
    """L5 - Continuous Monitoring and Anomaly Detection."""
    
    def __init__(self, ctx: GlobalContext):
        self.ctx = ctx
        self._metric_windows: Dict[str, deque] = {}
        self._baseline_thresholds = {
            "error_rate": 0.01,  # 1%
            "latency_p99_ms": 1000,  # 1 second
            "cpu_percent": 0.80,  # 80%
            "memory_percent": 0.85,  # 85%
        }
    
    def monitor_system(
        self,
        service_name: str,
        namespace: str,
        region: str = "us-east-1"
    ) -> List[AnomalyEvent]:
        """
        Main monitoring loop.
        Collect metrics, detect anomalies, publish events.
        
        Returns list of anomalies detected.
        """
        
        logger.debug(f"[L5] Monitoring {service_name} in {namespace}/{region}")
        
        anomalies = []
        
        # Collect current metrics
        metrics = self._collect_metrics(service_name, namespace, region)
        
        for metric_name, metric_value in metrics.items():
            # Tier 1: Static threshold
            if self._static_threshold_check(metric_name, metric_value):
                anomaly = self._create_anomaly_event(
                    metric_name, metric_value,
                    severity=AnomalySeverity.CRITICAL,
                    service_name=service_name,
                    namespace=namespace,
                    region=region
                )
                anomalies.append(anomaly)
                continue
            
            # Tier 2: 3-sigma moving average
            window = self._get_metric_window(metric_name, window_size=20)
            if len(window) >= 10:  # Need at least 10 samples
                if self._three_sigma_check(metric_name, metric_value, window):
                    anomaly = self._create_anomaly_event(
                        metric_name, metric_value,
                        severity=AnomalySeverity.HIGH,
                        service_name=service_name,
                        namespace=namespace,
                        region=region
                    )
                    anomalies.append(anomaly)
                    continue
            
            # Tier 3: Bayesian prediction
            if len(window) >= 20:
                if self._bayesian_anomaly_check(metric_name, metric_value, window):
                    anomaly = self._create_anomaly_event(
                        metric_name, metric_value,
                        severity=AnomalySeverity.MEDIUM,
                        service_name=service_name,
                        namespace=namespace,
                        region=region
                    )
                    anomalies.append(anomaly)
            
            # Add current metric to window
            window.append(metric_value)
        
        # Publish anomalies
        for anomaly in anomalies:
            self.ctx.event_bus.publish("anomalies:detected", anomaly.dict())
        
        if anomalies:
            logger.warning(f"[L5] Detected {len(anomalies)} anomalies for {service_name}")
        
        return anomalies
    
    def _collect_metrics(self, service_name: str, namespace: str, region: str) -> Dict[str, float]:
        """
        Collect current system metrics from Prometheus/CloudWatch.
        
        Mock implementation - in production: query Prometheus or CloudWatch API.
        """
        
        metrics = {
            "error_rate": 0.005,  # 0.5% - normal
            "latency_p99_ms": 450,  # 450ms - normal
            "cpu_percent": 0.45,  # 45% - normal
            "memory_percent": 0.52,  # 52% - normal
            "pod_restarts": 0,  # No restarts - normal
            "queue_depth": 25,  # Queue normal
        }
        
        # Simulate occasional anomalies for demo
        import random
        if random.random() < 0.1:  # 10% chance of anomaly
            metrics["cpu_percent"] = 0.92  # Spike to 92%
        
        return metrics
    
    def _static_threshold_check(self, metric_name: str, value: float) -> bool:
        """Tier 1: Check against static threshold."""
        threshold = self._baseline_thresholds.get(metric_name)
        if threshold and value > threshold:
            return True
        return False
    
    def _three_sigma_check(self, metric_name: str, current_value: float, window: deque) -> bool:
        """
        Tier 2: 3-sigma moving average detection.
        Alert if value is > 3 standard deviations from mean.
        """
        
        if len(window) < 3:
            return False
        
        values = list(window)
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        # 3-sigma threshold
        upper_bound = mean + (3 * std_dev)
        
        if current_value > upper_bound:
            logger.debug(f"[L5] 3-sigma anomaly: {metric_name}={current_value} > {upper_bound:.2f}")
            return True
        
        return False
    
    def _bayesian_anomaly_check(self, metric_name: str, current_value: float, window: deque) -> bool:
        """
        Tier 3: Bayesian probabilistic anomaly detection.
        Estimate P(current_value is anomalous | historical_distribution).
        """
        
        if len(window) < 10:
            return False
        
        values = list(window)
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        # Gaussian likelihood (simplified Bayesian)
        if std_dev == 0:
            return False
        
        z_score = abs((current_value - mean) / std_dev)
        
        # P(anomaly) increases with z_score
        # z_score=2 -> P(anomaly)~0.05, z_score=3 -> P(anomaly)~0.003, etc.
        # Trigger if z_score > 2.5 (roughly 1% tail probability)
        
        if z_score > 2.5:
            logger.debug(f"[L5] Bayesian anomaly: {metric_name}={current_value} (z={z_score:.2f})")
            return True
        
        return False
    
    def _create_anomaly_event(
        self,
        metric_name: str,
        metric_value: float,
        severity: AnomalySeverity,
        service_name: str,
        namespace: str,
        region: str
    ) -> AnomalyEvent:
        """Create anomaly event."""
        
        # Estimate baseline (simple mock)
        baseline = self._baseline_thresholds.get(metric_name, metric_value * 0.8)
        
        return AnomalyEvent(
            event_type="AnomalyDetected",
            severity=severity,
            anomaly_type=f"{metric_name}_spike",
            metric_name=metric_name,
            metric_value=metric_value,
            baseline_value=baseline,
            context={
                "service": service_name,
                "namespace": namespace,
                "region": region,
                "deviation_percent": ((metric_value - baseline) / baseline * 100) if baseline else 0
            }
        )
    
    def _get_metric_window(self, metric_name: str, window_size: int = 20) -> deque:
        """Get or create metric window (rolling buffer)."""
        if metric_name not in self._metric_windows:
            self._metric_windows[metric_name] = deque(maxlen=window_size)
        return self._metric_windows[metric_name]
    
    def get_current_metrics(self, service_name: str, namespace: str) -> Dict[str, float]:
        """Get current metrics for service."""
        return self._collect_metrics(service_name, namespace, "us-east-1")
    
    def get_metric_history(self, metric_name: str) -> List[float]:
        """Get historical metric values."""
        window = self._metric_windows.get(metric_name)
        if window:
            return list(window)
        return []
    
    def is_healthy(self) -> bool:
        """Check if L5 monitor itself is healthy."""
        # In production: check heartbeat, process status, etc.
        return True
