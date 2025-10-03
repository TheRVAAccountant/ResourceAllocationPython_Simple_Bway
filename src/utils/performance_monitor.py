"""Performance monitoring utility for tracking and reporting performance metrics."""

import time
import functools
import psutil
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger
import json
from pathlib import Path


@dataclass
class PerformanceMetric:
    """Container for a single performance measurement."""
    
    operation: str
    start_time: float
    end_time: float
    duration: float
    memory_before: float
    memory_after: float
    memory_delta: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def memory_mb(self) -> float:
        """Get memory delta in MB."""
        return self.memory_delta / (1024 * 1024)
    
    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds."""
        return self.duration * 1000


class PerformanceMonitor:
    """Monitor and track performance metrics for the application.
    
    Features:
    - Function execution timing
    - Memory usage tracking
    - Operation profiling
    - Performance reports
    - Real-time monitoring
    """
    
    def __init__(self, enable_memory_tracking: bool = True):
        """Initialize the performance monitor.
        
        Args:
            enable_memory_tracking: Whether to track memory usage.
        """
        self.enable_memory_tracking = enable_memory_tracking
        self.metrics: List[PerformanceMetric] = []
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
        self.active_operations: Dict[int, Dict] = {}
        self.process = psutil.Process()
        self._lock = threading.Lock()
        
        # Performance thresholds
        self.thresholds = {
            'allocation_time': 30.0,  # seconds
            'excel_load_time': 10.0,  # seconds
            'memory_peak': 2048,      # MB
            'gui_response': 0.1       # seconds
        }
    
    def track_operation(self, operation_name: str):
        """Decorator to track operation performance.
        
        Usage:
            @monitor.track_operation("allocation_process")
            def allocate_vehicles():
                # ... operation code ...
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.measure_operation(operation_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def measure_operation(self, operation_name: str, metadata: Optional[Dict] = None):
        """Context manager for measuring operation performance.
        
        Usage:
            with monitor.measure_operation("excel_write", {"rows": 1000}):
                # ... operation code ...
        """
        return OperationContext(self, operation_name, metadata or {})
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric."""
        with self._lock:
            self.metrics.append(metric)
            self.operation_stats[metric.operation].append(metric.duration)
            
            # Check thresholds
            self._check_thresholds(metric)
    
    def _check_thresholds(self, metric: PerformanceMetric):
        """Check if metric exceeds any thresholds."""
        # Check time threshold
        for op_pattern, threshold in self.thresholds.items():
            if op_pattern in metric.operation and metric.duration > threshold:
                logger.warning(
                    f"Performance threshold exceeded: {metric.operation} "
                    f"took {metric.duration:.2f}s (threshold: {threshold}s)"
                )
        
        # Check memory threshold
        if metric.memory_mb > self.thresholds.get('memory_peak', float('inf')):
            logger.warning(
                f"Memory threshold exceeded: {metric.operation} "
                f"used {metric.memory_mb:.2f}MB"
            )
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in bytes."""
        if not self.enable_memory_tracking:
            return 0.0
        
        try:
            return self.process.memory_info().rss
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0
    
    def get_summary(self, operation_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary statistics.
        
        Args:
            operation_filter: Optional filter for specific operations.
            
        Returns:
            Dictionary with performance statistics.
        """
        with self._lock:
            if operation_filter:
                filtered_metrics = [
                    m for m in self.metrics 
                    if operation_filter in m.operation
                ]
            else:
                filtered_metrics = self.metrics.copy()
        
        if not filtered_metrics:
            return {"message": "No metrics recorded"}
        
        # Calculate statistics
        durations = [m.duration for m in filtered_metrics]
        memory_deltas = [m.memory_mb for m in filtered_metrics]
        
        summary = {
            "total_operations": len(filtered_metrics),
            "total_time": sum(durations),
            "average_time": sum(durations) / len(durations),
            "min_time": min(durations),
            "max_time": max(durations),
            "total_memory_mb": sum(memory_deltas),
            "average_memory_mb": sum(memory_deltas) / len(memory_deltas),
            "operations_by_type": self._get_operation_breakdown(filtered_metrics)
        }
        
        return summary
    
    def _get_operation_breakdown(self, metrics: List[PerformanceMetric]) -> Dict[str, Dict]:
        """Get breakdown by operation type."""
        breakdown = defaultdict(lambda: {"count": 0, "total_time": 0, "total_memory_mb": 0})
        
        for metric in metrics:
            op_type = metric.operation.split("_")[0]  # Get operation prefix
            breakdown[op_type]["count"] += 1
            breakdown[op_type]["total_time"] += metric.duration
            breakdown[op_type]["total_memory_mb"] += metric.memory_mb
        
        # Calculate averages
        for op_type, stats in breakdown.items():
            if stats["count"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["count"]
                stats["avg_memory_mb"] = stats["total_memory_mb"] / stats["count"]
        
        return dict(breakdown)
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate a detailed performance report.
        
        Args:
            output_path: Optional path to save the report.
            
        Returns:
            Report content as string.
        """
        report_lines = [
            "# Performance Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            json.dumps(self.get_summary(), indent=2),
            "",
            "## Top 10 Slowest Operations"
        ]
        
        # Get slowest operations
        with self._lock:
            sorted_metrics = sorted(self.metrics, key=lambda m: m.duration, reverse=True)[:10]
        
        for i, metric in enumerate(sorted_metrics, 1):
            report_lines.extend([
                f"\n### {i}. {metric.operation}",
                f"- Duration: {metric.duration:.3f}s ({metric.duration_ms:.1f}ms)",
                f"- Memory: {metric.memory_mb:.2f}MB",
                f"- Time: {datetime.fromtimestamp(metric.start_time).isoformat()}",
                f"- Metadata: {json.dumps(metric.metadata, indent=2)}"
            ])
        
        report_lines.extend([
            "",
            "## Memory Usage Pattern",
            self._generate_memory_pattern()
        ])
        
        report_content = "\n".join(report_lines)
        
        if output_path:
            Path(output_path).write_text(report_content)
            logger.info(f"Performance report saved to {output_path}")
        
        return report_content
    
    def _generate_memory_pattern(self) -> str:
        """Generate memory usage pattern visualization."""
        with self._lock:
            if not self.metrics:
                return "No data available"
            
            # Create simple ASCII chart
            max_memory = max(m.memory_after for m in self.metrics)
            scale = 50 / (max_memory / (1024 * 1024))  # 50 chars width
            
            lines = ["Memory Usage Over Time (MB):"]
            for metric in self.metrics[-20:]:  # Last 20 operations
                memory_mb = metric.memory_after / (1024 * 1024)
                bar_length = int(memory_mb * scale)
                bar = "█" * bar_length
                lines.append(f"{metric.operation[:20]:20} {bar} {memory_mb:.1f}")
        
        return "\n".join(lines)
    
    def reset(self):
        """Reset all collected metrics."""
        with self._lock:
            self.metrics.clear()
            self.operation_stats.clear()
            self.active_operations.clear()
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file."""
        with self._lock:
            metrics_data = [
                {
                    "operation": m.operation,
                    "duration": m.duration,
                    "memory_mb": m.memory_mb,
                    "timestamp": m.start_time,
                    "metadata": m.metadata
                }
                for m in self.metrics
            ]
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        logger.info(f"Exported {len(metrics_data)} metrics to {filepath}")


class OperationContext:
    """Context manager for tracking individual operations."""
    
    def __init__(self, monitor: PerformanceMonitor, operation: str, metadata: Dict):
        self.monitor = monitor
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
        self.memory_before = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.memory_before = self.monitor.get_memory_usage()
        
        # Track active operation
        thread_id = threading.get_ident()
        self.monitor.active_operations[thread_id] = {
            'operation': self.operation,
            'start_time': self.start_time
        }
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        memory_after = self.monitor.get_memory_usage()
        
        # Remove from active operations
        thread_id = threading.get_ident()
        self.monitor.active_operations.pop(thread_id, None)
        
        # Create metric
        metric = PerformanceMetric(
            operation=self.operation,
            start_time=self.start_time,
            end_time=end_time,
            duration=end_time - self.start_time,
            memory_before=self.memory_before,
            memory_after=memory_after,
            memory_delta=memory_after - self.memory_before,
            metadata=self.metadata
        )
        
        self.monitor.record_metric(metric)
        
        # Log if operation was slow
        if metric.duration > 1.0:  # More than 1 second
            logger.info(
                f"Slow operation: {self.operation} took {metric.duration:.2f}s "
                f"(memory: {metric.memory_mb:.1f}MB)"
            )


# Global instance for easy access
_global_monitor = None


def get_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


# Convenient decorator
def track_performance(operation_name: str):
    """Convenient decorator using global monitor."""
    return get_monitor().track_operation(operation_name)