"""
Monitoring dashboard tab for the Resource Management System GUI.
Provides real-time monitoring, alerts, and performance metrics visualization.
"""

from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import customtkinter as ctk

from src.services.monitoring_service import get_monitoring_service
from src.utils.performance_monitor import PerformanceMonitor


class MonitoringTab(ctk.CTkFrame):
    """
    Monitoring dashboard tab for real-time system monitoring.

    Provides:
    - System health overview
    - Performance metrics
    - Active alerts
    - Historical data
    - Alert management
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.monitoring_service = get_monitoring_service()
        self.performance_monitor = PerformanceMonitor()

        # Auto-refresh settings
        self.auto_refresh = True
        self.refresh_interval = 30000  # 30 seconds
        self.refresh_job = None

        # Data caching
        self.last_health_check = None
        self.last_performance_summary = None
        self.last_alert_summary = None

        self._create_widgets()
        self._start_auto_refresh()

    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main container with scrollable content
        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Header section
        self._create_header()

        # Control panel
        self._create_control_panel()

        # System health section
        self._create_health_section()

        # Performance metrics section
        self._create_performance_section()

        # Alerts section
        self._create_alerts_section()

        # Business metrics section
        self._create_business_metrics_section()

        # Initial data load
        self.refresh_all_data()

    def _create_header(self):
        """Create header section with title and status."""
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.pack(fill="x", pady=(0, 20))

        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="System Monitoring Dashboard",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.pack(side="left", padx=20, pady=15)

        # Status indicator
        self.status_frame = ctk.CTkFrame(header_frame)
        self.status_frame.pack(side="right", padx=20, pady=15)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="System Status: Loading...",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.status_label.pack(padx=15, pady=8)

        # Last updated timestamp
        self.last_updated_label = ctk.CTkLabel(
            header_frame, text="Last Updated: --", font=ctk.CTkFont(size=12), text_color="gray"
        )
        self.last_updated_label.pack(side="right", padx=(0, 20), pady=15)

    def _create_control_panel(self):
        """Create control panel with refresh and settings."""
        control_frame = ctk.CTkFrame(self.main_container)
        control_frame.pack(fill="x", pady=(0, 20))

        # Refresh controls
        refresh_frame = ctk.CTkFrame(control_frame)
        refresh_frame.pack(side="left", padx=20, pady=15)

        self.refresh_button = ctk.CTkButton(
            refresh_frame, text="Refresh Now", command=self.refresh_all_data, width=120
        )
        self.refresh_button.pack(side="left", padx=10, pady=8)

        self.auto_refresh_switch = ctk.CTkSwitch(
            refresh_frame, text="Auto Refresh", command=self._toggle_auto_refresh
        )
        self.auto_refresh_switch.pack(side="left", padx=10, pady=8)
        self.auto_refresh_switch.select()

        # Export controls
        export_frame = ctk.CTkFrame(control_frame)
        export_frame.pack(side="right", padx=20, pady=15)

        self.export_button = ctk.CTkButton(
            export_frame, text="Export Metrics", command=self._export_metrics, width=120
        )
        self.export_button.pack(side="left", padx=10, pady=8)

        self.clear_alerts_button = ctk.CTkButton(
            export_frame,
            text="Clear Resolved Alerts",
            command=self._clear_resolved_alerts,
            width=150,
        )
        self.clear_alerts_button.pack(side="left", padx=10, pady=8)

    def _create_health_section(self):
        """Create system health monitoring section."""
        health_frame = ctk.CTkFrame(self.main_container)
        health_frame.pack(fill="x", pady=(0, 20))

        # Section header
        health_header = ctk.CTkLabel(
            health_frame, text="System Health", font=ctk.CTkFont(size=18, weight="bold")
        )
        health_header.pack(anchor="w", padx=20, pady=(15, 10))

        # Health indicators grid
        self.health_grid = ctk.CTkFrame(health_frame)
        self.health_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Health check items
        self.health_items = {}
        health_checks = [
            ("Overall Status", "overall_status"),
            ("Memory Usage", "memory"),
            ("CPU Usage", "cpu"),
            ("Disk Usage", "disk"),
            ("Application", "application"),
            ("Excel Connectivity", "excel"),
            ("File System", "filesystem"),
        ]

        for i, (label, key) in enumerate(health_checks):
            row = i // 3
            col = i % 3

            item_frame = ctk.CTkFrame(self.health_grid)
            item_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

            title_label = ctk.CTkLabel(
                item_frame, text=label, font=ctk.CTkFont(size=12, weight="bold")
            )
            title_label.pack(anchor="w", padx=15, pady=(10, 5))

            status_label = ctk.CTkLabel(item_frame, text="Unknown", font=ctk.CTkFont(size=14))
            status_label.pack(anchor="w", padx=15, pady=(0, 10))

            self.health_items[key] = status_label

        # Configure grid weights
        for i in range(3):
            self.health_grid.columnconfigure(i, weight=1)

    def _create_performance_section(self):
        """Create performance metrics section."""
        perf_frame = ctk.CTkFrame(self.main_container)
        perf_frame.pack(fill="x", pady=(0, 20))

        # Section header
        perf_header = ctk.CTkLabel(
            perf_frame,
            text="Performance Metrics (Last 24 Hours)",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        perf_header.pack(anchor="w", padx=20, pady=(15, 10))

        # Performance metrics table
        self.perf_tree = ttk.Treeview(
            perf_frame,
            columns=("metric", "avg", "min", "max", "latest", "unit"),
            show="headings",
            height=8,
        )

        # Configure columns
        columns = [
            ("metric", "Metric", 200),
            ("avg", "Average", 100),
            ("min", "Minimum", 100),
            ("max", "Maximum", 100),
            ("latest", "Latest", 100),
            ("unit", "Unit", 80),
        ]

        for col_id, heading, width in columns:
            self.perf_tree.heading(col_id, text=heading)
            self.perf_tree.column(col_id, width=width, anchor="center")

        # Scrollbar for performance table
        perf_scrollbar = ttk.Scrollbar(perf_frame, orient="vertical", command=self.perf_tree.yview)
        self.perf_tree.configure(yscrollcommand=perf_scrollbar.set)

        # Pack performance widgets
        perf_container = ctk.CTkFrame(perf_frame)
        perf_container.pack(fill="x", padx=20, pady=(0, 15))

        self.perf_tree.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        perf_scrollbar.pack(side="right", fill="y", pady=15)

    def _create_alerts_section(self):
        """Create active alerts section."""
        alerts_frame = ctk.CTkFrame(self.main_container)
        alerts_frame.pack(fill="x", pady=(0, 20))

        # Section header
        alerts_header_frame = ctk.CTkFrame(alerts_frame)
        alerts_header_frame.pack(fill="x", padx=20, pady=(15, 10))

        alerts_header = ctk.CTkLabel(
            alerts_header_frame, text="Active Alerts", font=ctk.CTkFont(size=18, weight="bold")
        )
        alerts_header.pack(side="left")

        self.alert_count_label = ctk.CTkLabel(
            alerts_header_frame, text="(0 active)", font=ctk.CTkFont(size=14), text_color="gray"
        )
        self.alert_count_label.pack(side="left", padx=(10, 0))

        # Alerts list
        self.alerts_container = ctk.CTkScrollableFrame(alerts_frame, height=200)
        self.alerts_container.pack(fill="x", padx=20, pady=(0, 15))

        # No alerts message (initially shown)
        self.no_alerts_label = ctk.CTkLabel(
            self.alerts_container,
            text="No active alerts",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        self.no_alerts_label.pack(pady=20)

    def _create_business_metrics_section(self):
        """Create business metrics section."""
        business_frame = ctk.CTkFrame(self.main_container)
        business_frame.pack(fill="x", pady=(0, 20))

        # Section header
        business_header = ctk.CTkLabel(
            business_frame, text="Business Metrics", font=ctk.CTkFont(size=18, weight="bold")
        )
        business_header.pack(anchor="w", padx=20, pady=(15, 10))

        # Business metrics grid
        self.business_grid = ctk.CTkFrame(business_frame)
        self.business_grid.pack(fill="x", padx=20, pady=(0, 15))

        # Business metric items
        self.business_items = {}
        business_metrics = [
            ("Allocations Today", "allocations_today", "count"),
            ("Duplicates Detected", "duplicates_detected", "count"),
            ("Unassigned Vehicles", "unassigned_vehicles", "count"),
            ("Success Rate", "success_rate", "%"),
            ("Avg Processing Time", "avg_processing_time", "sec"),
            ("Feature Adoption", "feature_adoption", "%"),
        ]

        for i, (label, key, unit) in enumerate(business_metrics):
            row = i // 3
            col = i % 3

            item_frame = ctk.CTkFrame(self.business_grid)
            item_frame.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

            title_label = ctk.CTkLabel(
                item_frame, text=label, font=ctk.CTkFont(size=12, weight="bold")
            )
            title_label.pack(anchor="w", padx=15, pady=(10, 5))

            value_label = ctk.CTkLabel(
                item_frame, text=f"-- {unit}", font=ctk.CTkFont(size=16, weight="bold")
            )
            value_label.pack(anchor="w", padx=15, pady=(0, 10))

            self.business_items[key] = value_label

        # Configure grid weights
        for i in range(3):
            self.business_grid.columnconfigure(i, weight=1)

    def _toggle_auto_refresh(self):
        """Toggle auto-refresh functionality."""
        self.auto_refresh = self.auto_refresh_switch.get()
        if self.auto_refresh:
            self._start_auto_refresh()
        else:
            self._stop_auto_refresh()

    def _start_auto_refresh(self):
        """Start auto-refresh timer."""
        if self.auto_refresh and not self.refresh_job:
            self.refresh_job = self.after(self.refresh_interval, self._auto_refresh_callback)

    def _stop_auto_refresh(self):
        """Stop auto-refresh timer."""
        if self.refresh_job:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None

    def _auto_refresh_callback(self):
        """Auto-refresh callback."""
        if self.auto_refresh:
            self.refresh_all_data()
            self.refresh_job = self.after(self.refresh_interval, self._auto_refresh_callback)

    def refresh_all_data(self):
        """Refresh all monitoring data."""
        try:
            # Update timestamp
            self.last_updated_label.configure(
                text=f"Last Updated: {datetime.now().strftime('%H:%M:%S')}"
            )

            # Refresh health data
            self._refresh_health_data()

            # Refresh performance data
            self._refresh_performance_data()

            # Refresh alerts data
            self._refresh_alerts_data()

            # Refresh business metrics
            self._refresh_business_metrics()

        except Exception as e:
            messagebox.showerror("Monitoring Error", f"Failed to refresh data: {str(e)}")

    def _refresh_health_data(self):
        """Refresh system health data."""
        try:
            health_data = self.monitoring_service.check_system_health()
            self.last_health_check = health_data

            # Update overall status
            overall_status = health_data.get("overall_status", "unknown")
            status_colors = {
                "healthy": "green",
                "warning": "orange",
                "critical": "red",
                "unknown": "gray",
            }

            self.status_label.configure(
                text=f"System Status: {overall_status.title()}",
                text_color=status_colors.get(overall_status, "gray"),
            )

            # Update individual health items
            if "checks" in health_data:
                for key, item_label in self.health_items.items():
                    if key == "overall_status":
                        status_text = overall_status.title()
                        color = status_colors.get(overall_status, "gray")
                    elif key in health_data["checks"]:
                        check_data = health_data["checks"][key]
                        status = check_data.get("status", "unknown")

                        if isinstance(check_data, dict):
                            if "usage_percent" in check_data:
                                status_text = (
                                    f"{status.title()} ({check_data['usage_percent']:.1f}%)"
                                )
                            else:
                                status_text = status.title()
                        else:
                            status_text = str(check_data)

                        color = status_colors.get(status, "gray")
                    else:
                        status_text = "Unknown"
                        color = "gray"

                    item_label.configure(text=status_text, text_color=color)

        except Exception as e:
            print(f"Error refreshing health data: {e}")

    def _refresh_performance_data(self):
        """Refresh performance metrics data."""
        try:
            perf_data = self.monitoring_service.get_performance_summary(24)
            self.last_performance_summary = perf_data

            # Clear existing items
            for item in self.perf_tree.get_children():
                self.perf_tree.delete(item)

            # Add performance metrics
            if "metrics" in perf_data:
                for name, data in perf_data["metrics"].items():
                    display_name = name.replace("_", " ").title()
                    avg_val = f"{data['avg']:.2f}" if data["avg"] is not None else "--"
                    min_val = f"{data['min']:.2f}" if data["min"] is not None else "--"
                    max_val = f"{data['max']:.2f}" if data["max"] is not None else "--"
                    latest_val = f"{data['latest']:.2f}" if data["latest"] is not None else "--"
                    unit = data.get("unit", "")

                    self.perf_tree.insert(
                        "",
                        "end",
                        values=(display_name, avg_val, min_val, max_val, latest_val, unit),
                    )

        except Exception as e:
            print(f"Error refreshing performance data: {e}")

    def _refresh_alerts_data(self):
        """Refresh alerts data."""
        try:
            alert_summary = self.monitoring_service.get_alert_summary()
            self.last_alert_summary = alert_summary

            active_count = alert_summary.get("active_alerts", 0)
            self.alert_count_label.configure(text=f"({active_count} active)")

            # Clear existing alert widgets
            for widget in self.alerts_container.winfo_children():
                widget.destroy()

            # Get active alerts
            active_alerts = [
                alert
                for alert in self.monitoring_service.active_alerts.values()
                if not alert.resolved
            ]

            if not active_alerts:
                self.no_alerts_label = ctk.CTkLabel(
                    self.alerts_container,
                    text="No active alerts",
                    font=ctk.CTkFont(size=14),
                    text_color="gray",
                )
                self.no_alerts_label.pack(pady=20)
            else:
                for alert in active_alerts:
                    self._create_alert_widget(alert)

        except Exception as e:
            print(f"Error refreshing alerts data: {e}")

    def _create_alert_widget(self, alert):
        """Create a widget for displaying an alert."""
        severity_colors = {"info": "blue", "warning": "orange", "critical": "red"}

        alert_frame = ctk.CTkFrame(self.alerts_container)
        alert_frame.pack(fill="x", padx=10, pady=5)

        # Alert header
        header_frame = ctk.CTkFrame(alert_frame)
        header_frame.pack(fill="x", padx=15, pady=(15, 5))

        severity_label = ctk.CTkLabel(
            header_frame,
            text=alert.severity.upper(),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=severity_colors.get(alert.severity, "gray"),
        )
        severity_label.pack(side="left")

        timestamp_label = ctk.CTkLabel(
            header_frame,
            text=alert.timestamp.strftime("%H:%M:%S"),
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        timestamp_label.pack(side="right")

        # Alert title
        title_label = ctk.CTkLabel(
            alert_frame, text=alert.title, font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(anchor="w", padx=15, pady=(0, 5))

        # Alert message
        message_label = ctk.CTkLabel(
            alert_frame, text=alert.message, font=ctk.CTkFont(size=12), wraplength=500
        )
        message_label.pack(anchor="w", padx=15, pady=(0, 15))

    def _refresh_business_metrics(self):
        """Refresh business metrics data."""
        try:
            # These would be calculated from actual application data
            # For now, showing placeholder data
            metrics = {
                "allocations_today": (25, "count"),
                "duplicates_detected": (3, "count"),
                "unassigned_vehicles": (8, "count"),
                "success_rate": (94.2, "%"),
                "avg_processing_time": (12.5, "sec"),
                "feature_adoption": (78.0, "%"),
            }

            for key, (value, unit) in metrics.items():
                if key in self.business_items:
                    display_value = f"{value:.1f}" if isinstance(value, float) else str(value)
                    self.business_items[key].configure(text=f"{display_value} {unit}")

        except Exception as e:
            print(f"Error refreshing business metrics: {e}")

    def _export_metrics(self):
        """Export metrics data to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"outputs/monitoring_export_{timestamp}.json")

            self.monitoring_service.export_metrics(output_path, "json")
            messagebox.showinfo("Export Complete", f"Metrics exported to {output_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export metrics: {str(e)}")

    def _clear_resolved_alerts(self):
        """Clear all resolved alerts from history."""
        try:
            # Remove resolved alerts from history
            self.monitoring_service.alert_history = [
                alert for alert in self.monitoring_service.alert_history if not alert.resolved
            ]

            # Remove resolved alerts from active alerts
            resolved_keys = [
                key
                for key, alert in self.monitoring_service.active_alerts.items()
                if alert.resolved
            ]

            for key in resolved_keys:
                del self.monitoring_service.active_alerts[key]

            self._refresh_alerts_data()
            messagebox.showinfo("Alerts Cleared", "Resolved alerts have been cleared from history.")

        except Exception as e:
            messagebox.showerror("Clear Error", f"Failed to clear alerts: {str(e)}")

    def destroy(self):
        """Clean up when tab is destroyed."""
        self._stop_auto_refresh()
        super().destroy()
