"""
Monitoring and alerting service for the Resource Management System.
Provides real-time monitoring, performance tracking, and automated alerting.
"""

import asyncio
import json
import logging
import os
import smtplib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import psutil
from cachetools import TTLCache

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""

    name: str
    value: float
    timestamp: datetime
    unit: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert data structure."""

    severity: str  # 'info', 'warning', 'critical'
    title: str
    message: str
    timestamp: datetime
    metric_name: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    resolved: bool = False
    acknowledgement: Optional[str] = None


class MonitoringService:
    """
    Production monitoring and alerting service.

    Provides real-time monitoring of application health, performance metrics,
    and automated alerting for production operations.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize monitoring service.

        Args:
            config_path: Path to monitoring configuration file
        """
        self.config_path = config_path or Path("config/monitoring.json")
        self.config = self._load_config()

        # Metrics storage (in-memory with TTL cache)
        self.metrics_cache = TTLCache(maxsize=10000, ttl=3600)  # 1 hour TTL
        self.alerts_cache = TTLCache(maxsize=1000, ttl=86400)  # 24 hour TTL

        # Performance thresholds
        self.thresholds = {
            "allocation_time": {"warning": 25.0, "critical": 40.0},  # seconds
            "memory_usage": {"warning": 1024.0, "critical": 2048.0},  # MB
            "excel_processing_time": {"warning": 8.0, "critical": 15.0},  # seconds
            "error_rate": {"warning": 0.05, "critical": 0.10},  # percentage
            "gui_response_time": {"warning": 0.5, "critical": 2.0},  # seconds
            "duplicate_detection_rate": {"warning": 0.95, "critical": 0.90},  # percentage
        }

        # Alert state tracking
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Monitoring state
        self.monitoring_active = False
        self.last_health_check = None
        self.start_time = datetime.now()

        logger.info("Monitoring service initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        default_config = {
            "monitoring_interval": 300,  # 5 minutes
            "health_check_interval": 60,  # 1 minute
            "alert_cooldown": 900,  # 15 minutes
            "email_enabled": False,
            "email_smtp_host": "localhost",
            "email_smtp_port": 587,
            "email_from": "monitoring@resourceallocation.com",
            "email_to": ["admin@resourceallocation.com"],
            "email_username": "",
            "email_password": "",
            "metrics_retention_hours": 24,
            "enable_performance_tracking": True,
            "enable_error_tracking": True,
            "enable_business_metrics": True,
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                # Merge with defaults
                default_config.update(config)
                logger.info(f"Loaded monitoring configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config, using defaults: {e}")

        return default_config

    def record_metric(
        self, name: str, value: float, unit: str = "count", tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a performance metric.

        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement
            tags: Additional tags for the metric
        """
        tags = tags or {}
        threshold_warning = self.thresholds.get(name, {}).get("warning")
        threshold_critical = self.thresholds.get(name, {}).get("critical")

        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            unit=unit,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            tags=tags,
        )

        # Store metric
        cache_key = f"{name}_{int(time.time())}"
        self.metrics_cache[cache_key] = metric

        # Check for threshold violations
        self._check_thresholds(metric)

        logger.debug(f"Recorded metric: {name}={value} {unit}")

    def _check_thresholds(self, metric: PerformanceMetric) -> None:
        """Check if metric violates thresholds and create alerts."""
        if not metric.threshold_warning and not metric.threshold_critical:
            return

        alert_severity = None
        threshold = None

        # Check critical threshold first
        if metric.threshold_critical and metric.value >= metric.threshold_critical:
            alert_severity = "critical"
            threshold = metric.threshold_critical
        elif metric.threshold_warning and metric.value >= metric.threshold_warning:
            alert_severity = "warning"
            threshold = metric.threshold_warning

        if alert_severity:
            alert_id = f"{metric.name}_{alert_severity}"

            # Check if alert already exists and is not resolved
            if alert_id in self.active_alerts and not self.active_alerts[alert_id].resolved:
                return  # Avoid duplicate alerts

            alert = Alert(
                severity=alert_severity,
                title=f"{metric.name.replace('_', ' ').title()} Threshold Exceeded",
                message=f"{metric.name} is {metric.value} {metric.unit}, "
                f"exceeding {alert_severity} threshold of {threshold} {metric.unit}",
                timestamp=metric.timestamp,
                metric_name=metric.name,
                current_value=metric.value,
                threshold=threshold,
            )

            self._create_alert(alert)

    def _create_alert(self, alert: Alert) -> None:
        """Create and process a new alert."""
        alert_id = f"{alert.metric_name}_{alert.severity}"
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        logger.warning(f"Alert created: {alert.title} - {alert.message}")

        # Send notifications
        if self.config.get("email_enabled"):
            self._send_email_alert(alert)

    def _send_email_alert(self, alert: Alert) -> None:
        """Send email notification for alert."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.config["email_from"]
            msg["To"] = ", ".join(self.config["email_to"])
            msg["Subject"] = f"[{alert.severity.upper()}] Resource Allocation Alert: {alert.title}"

            body = f"""
Resource Management System Alert

Severity: {alert.severity.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Title: {alert.title}

Details:
{alert.message}

Current Value: {alert.current_value} ({alert.metric_name})
Threshold: {alert.threshold}

System Information:
- Uptime: {datetime.now() - self.start_time}
- Last Health Check: {self.last_health_check}
- Active Alerts: {len(self.active_alerts)}

Please investigate and take appropriate action.

Resource Allocation Monitoring System
"""

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(self.config["email_smtp_host"], self.config["email_smtp_port"])
            server.starttls()
            if self.config["email_username"]:
                server.login(self.config["email_username"], self.config["email_password"])

            server.send_message(msg)
            server.quit()

            logger.info(f"Alert email sent for: {alert.title}")

        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")

    def check_system_health(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check.

        Returns:
            Dictionary containing system health information
        """
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "alerts": len(self.active_alerts),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
        }

        try:
            # System resource checks
            memory = psutil.virtual_memory()
            health_status["checks"]["memory"] = {
                "status": "healthy" if memory.percent < 80 else "warning",
                "usage_percent": memory.percent,
                "available_mb": memory.available / 1024 / 1024,
            }

            disk = psutil.disk_usage("/")
            health_status["checks"]["disk"] = {
                "status": "healthy" if disk.percent < 90 else "warning",
                "usage_percent": disk.percent,
                "free_gb": disk.free / 1024 / 1024 / 1024,
            }

            cpu_percent = psutil.cpu_percent(interval=1)
            health_status["checks"]["cpu"] = {
                "status": "healthy" if cpu_percent < 80 else "warning",
                "usage_percent": cpu_percent,
            }

            # Application-specific checks
            health_status["checks"]["application"] = self._check_application_health()

            # Excel connectivity check
            health_status["checks"]["excel"] = self._check_excel_connectivity()

            # File system checks
            health_status["checks"]["filesystem"] = self._check_filesystem_health()

            # Determine overall status
            warning_checks = [
                check
                for check in health_status["checks"].values()
                if check.get("status") == "warning"
            ]
            critical_checks = [
                check
                for check in health_status["checks"].values()
                if check.get("status") == "critical"
            ]

            if critical_checks:
                health_status["overall_status"] = "critical"
            elif warning_checks:
                health_status["overall_status"] = "warning"

            self.last_health_check = datetime.now()

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["overall_status"] = "critical"
            health_status["error"] = str(e)

        return health_status

    def _check_application_health(self) -> Dict[str, Any]:
        """Check application-specific health indicators."""
        try:
            from src.core.gas_compatible_allocator import GASCompatibleAllocator
            from src.services.excel_service import ExcelService

            # Test core services
            allocator = GASCompatibleAllocator()
            excel_service = ExcelService()

            return {
                "status": "healthy",
                "core_allocator": "operational",
                "excel_service": "operational",
                "services_loaded": True,
            }
        except Exception as e:
            return {"status": "critical", "error": str(e), "services_loaded": False}

    def _check_excel_connectivity(self) -> Dict[str, Any]:
        """Check Excel application connectivity."""
        try:
            import xlwings as xw

            # Try to connect to Excel
            app = xw.App(visible=False)
            app.quit()

            return {"status": "healthy", "excel_available": True, "xlwings_version": xw.__version__}
        except Exception as e:
            return {"status": "warning", "excel_available": False, "error": str(e)}

    def _check_filesystem_health(self) -> Dict[str, Any]:
        """Check filesystem health and accessibility."""
        check_paths = [Path("data"), Path("outputs"), Path("logs"), Path("config")]

        status = "healthy"
        path_statuses = {}

        for path in check_paths:
            try:
                if path.exists() and path.is_dir():
                    # Check read/write permissions
                    test_file = path / ".health_check"
                    test_file.write_text("health check")
                    test_file.unlink()
                    path_statuses[str(path)] = "accessible"
                else:
                    path_statuses[str(path)] = "missing"
                    status = "warning"
            except Exception as e:
                path_statuses[str(path)] = f"error: {e}"
                status = "critical"

        return {"status": status, "paths": path_statuses}

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for the specified time period.

        Args:
            hours: Number of hours to include in summary

        Returns:
            Performance summary data
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter metrics by time
        recent_metrics = [
            metric for metric in self.metrics_cache.values() if metric.timestamp >= cutoff_time
        ]

        # Group metrics by name
        metrics_by_name = {}
        for metric in recent_metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric)

        # Calculate summary statistics
        summary = {
            "period_hours": hours,
            "total_metrics": len(recent_metrics),
            "metric_types": len(metrics_by_name),
            "metrics": {},
        }

        for name, metrics in metrics_by_name.items():
            values = [m.value for m in metrics]
            summary["metrics"][name] = {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1] if values else None,
                "unit": metrics[0].unit if metrics else "unknown",
            }

        return summary

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alerts and alert history."""
        active_by_severity = {}
        for alert in self.active_alerts.values():
            if not alert.resolved:
                if alert.severity not in active_by_severity:
                    active_by_severity[alert.severity] = 0
                active_by_severity[alert.severity] += 1

        return {
            "active_alerts": len([a for a in self.active_alerts.values() if not a.resolved]),
            "total_alerts_today": len(
                [a for a in self.alert_history if a.timestamp.date() == datetime.now().date()]
            ),
            "active_by_severity": active_by_severity,
            "latest_alert": self.alert_history[-1].timestamp.isoformat()
            if self.alert_history
            else None,
        }

    async def start_monitoring(self) -> None:
        """Start the monitoring service in background."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        logger.info("Starting monitoring service")

        try:
            while self.monitoring_active:
                # Perform health check
                health_status = self.check_system_health()

                # Record system metrics
                self.record_metric(
                    "system_memory_percent", psutil.virtual_memory().percent, "percent"
                )
                self.record_metric("system_cpu_percent", psutil.cpu_percent(), "percent")
                self.record_metric("system_disk_percent", psutil.disk_usage("/").percent, "percent")

                # Sleep until next check
                await asyncio.sleep(self.config["health_check_interval"])

        except Exception as e:
            logger.error(f"Monitoring service error: {e}")
        finally:
            self.monitoring_active = False
            logger.info("Monitoring service stopped")

    def stop_monitoring(self) -> None:
        """Stop the monitoring service."""
        self.monitoring_active = False
        logger.info("Monitoring service stop requested")

    def acknowledge_alert(self, alert_id: str, acknowledgement: str) -> bool:
        """
        Acknowledge an active alert.

        Args:
            alert_id: ID of the alert to acknowledge
            acknowledgement: Acknowledgement message

        Returns:
            True if alert was acknowledged, False if not found
        """
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledgement = acknowledgement
            logger.info(f"Alert acknowledged: {alert_id} - {acknowledgement}")
            return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an active alert.

        Args:
            alert_id: ID of the alert to resolve

        Returns:
            True if alert was resolved, False if not found
        """
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False

    def export_metrics(self, output_path: Path, format: str = "json") -> None:
        """
        Export metrics data to file.

        Args:
            output_path: Path to output file
            format: Export format ('json' or 'csv')
        """
        try:
            if format == "json":
                data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "metrics": [
                        {
                            "name": m.name,
                            "value": m.value,
                            "timestamp": m.timestamp.isoformat(),
                            "unit": m.unit,
                            "tags": m.tags,
                        }
                        for m in self.metrics_cache.values()
                    ],
                    "alerts": [
                        {
                            "severity": a.severity,
                            "title": a.title,
                            "message": a.message,
                            "timestamp": a.timestamp.isoformat(),
                            "resolved": a.resolved,
                        }
                        for a in self.alert_history
                    ],
                }

                with open(output_path, "w") as f:
                    json.dump(data, f, indent=2)

            elif format == "csv":
                import pandas as pd

                metrics_data = [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "name": m.name,
                        "value": m.value,
                        "unit": m.unit,
                        **m.tags,
                    }
                    for m in self.metrics_cache.values()
                ]

                df = pd.DataFrame(metrics_data)
                df.to_csv(output_path, index=False)

            logger.info(f"Metrics exported to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")


# Singleton instance for global access
_monitoring_service = None


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


# Convenience functions for easy access
def record_metric(
    name: str, value: float, unit: str = "count", tags: Optional[Dict[str, str]] = None
) -> None:
    """Record a performance metric."""
    get_monitoring_service().record_metric(name, value, unit, tags)


def check_health() -> Dict[str, Any]:
    """Perform system health check."""
    return get_monitoring_service().check_system_health()


# Context manager for performance timing
class performance_timer:
    """Context manager for timing operations and recording metrics."""

    def __init__(self, metric_name: str, tags: Optional[Dict[str, str]] = None):
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            record_metric(self.metric_name, duration, "seconds", self.tags)
