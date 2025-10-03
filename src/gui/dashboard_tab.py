"""Dashboard tab for Resource Allocation GUI."""

import threading
from datetime import datetime, timedelta
from typing import Callable, Optional

import customtkinter as ctk
from loguru import logger


class MetricCard(ctk.CTkFrame):
    """Individual metric card widget."""

    def __init__(
        self, parent, title: str, value: str = "0", subtitle: str = "", color: str = "blue"
    ):
        """Initialize metric card.

        Args:
            parent: Parent widget.
            title: Card title.
            value: Main value to display.
            subtitle: Additional information.
            color: Accent color.
        """
        super().__init__(parent, corner_radius=10)

        self.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=14), text_color=("gray60", "gray40")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # Value
        self.value_label = ctk.CTkLabel(
            self, text=value, font=ctk.CTkFont(size=32, weight="bold"), text_color=color
        )
        self.value_label.grid(row=1, column=0, sticky="w", padx=15, pady=5)

        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self, text=subtitle, font=ctk.CTkFont(size=12), text_color=("gray50", "gray50")
        )
        self.subtitle_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5, 15))

    def update_value(self, value: str, subtitle: str = None):
        """Update card values.

        Args:
            value: New value to display.
            subtitle: New subtitle (optional).
        """
        self.value_label.configure(text=value)
        if subtitle is not None:
            self.subtitle_label.configure(text=subtitle)


class DashboardTab:
    """Dashboard tab implementation."""

    def __init__(
        self,
        parent,
        allocation_engine,
        dashboard_data_service=None,
        daily_summary_path_getter: Optional[Callable[[], Optional[str]]] = None,
    ):
        """Initialize dashboard tab.

        Args:
            parent: Parent widget.
            allocation_engine: Reference to allocation engine.
        """
        self.parent = parent
        self.allocation_engine = allocation_engine
        self.dashboard_data_service = dashboard_data_service
        self._daily_summary_path_getter = daily_summary_path_getter
        self._daily_routes_path_getter: Optional[Callable[[], Optional[str]]] = None

        # Configure grid
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        # Create UI elements
        self.setup_ui()

        # Load initial data
        self.update_metrics()

    def set_daily_summary_path_getter(self, getter: Callable[[], Optional[str]]):
        """Wire a callable that returns the selected Daily Summary path."""
        self._daily_summary_path_getter = getter

    def _resolve_daily_summary_path(self) -> Optional[str]:
        """Resolve Daily Summary path from getter or service defaults."""
        try:
            if self._daily_summary_path_getter:
                path = self._daily_summary_path_getter()
                if path:
                    return path
        except Exception:
            pass
        if self.dashboard_data_service:
            return self.dashboard_data_service.resolve_daily_summary_path(None)
        return None

    def set_daily_routes_path_getter(self, getter: Callable[[], Optional[str]]):
        """Wire a callable that returns the selected Daily Routes path."""
        self._daily_routes_path_getter = getter

    def _resolve_daily_routes_path(self) -> Optional[str]:
        try:
            if self._daily_routes_path_getter:
                path = self._daily_routes_path_getter()
                if path:
                    return path
        except Exception:
            pass
        return None

    def setup_ui(self):
        """Setup dashboard UI."""
        # Header with refresh button
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        header_label = ctk.CTkLabel(
            header_frame, text="System Overview", font=ctk.CTkFont(size=24, weight="bold")
        )
        header_label.grid(row=0, column=0, sticky="w")

        refresh_button = ctk.CTkButton(
            header_frame, text="🔄 Refresh", width=100, command=self.refresh_dashboard
        )
        refresh_button.grid(row=0, column=1, sticky="e", padx=10)

        # Metrics container
        metrics_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        metrics_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Configure grid for metrics
        for i in range(4):
            metrics_frame.grid_columnconfigure(i, weight=1)
        metrics_frame.grid_rowconfigure(0, weight=0)
        metrics_frame.grid_rowconfigure(1, weight=0)
        metrics_frame.grid_rowconfigure(2, weight=1)

        # Create metric cards - Row 1
        self.total_vehicles_card = MetricCard(
            metrics_frame, "Total Vehicles", "0", "Available for allocation", "blue"
        )
        self.total_vehicles_card.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.total_drivers_card = MetricCard(
            metrics_frame, "Total Drivers", "0", "Active drivers", "green"
        )
        self.total_drivers_card.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        self.allocated_card = MetricCard(
            metrics_frame, "Allocated", "0", "Vehicles assigned", "orange"
        )
        self.allocated_card.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        self.allocation_rate_card = MetricCard(
            metrics_frame, "Allocation Rate", "0%", "Success rate", "purple"
        )
        self.allocation_rate_card.grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        # Create metric cards - Row 2
        self.unallocated_card = MetricCard(
            metrics_frame, "Unallocated", "0", "Pending assignment", "red"
        )
        self.unallocated_card.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.avg_per_driver_card = MetricCard(
            metrics_frame, "Avg per Driver", "0.0", "Vehicles per driver", "cyan"
        )
        self.avg_per_driver_card.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self.processing_time_card = MetricCard(
            metrics_frame, "Processing Time", "0.0s", "Last allocation", "gray"
        )
        self.processing_time_card.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        self.last_run_card = MetricCard(
            metrics_frame, "Last Run", "Never", "Time since last allocation", "pink"
        )
        self.last_run_card.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        # Recent Activity Section
        activity_frame = ctk.CTkFrame(metrics_frame)
        activity_frame.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=5, pady=(20, 5))
        activity_frame.grid_columnconfigure(0, weight=1)
        activity_frame.grid_rowconfigure(1, weight=1)

        activity_label = ctk.CTkLabel(
            activity_frame,
            text="Recent Allocation History",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        activity_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)

        # Activity list
        self.activity_text = ctk.CTkTextbox(
            activity_frame, corner_radius=5, font=ctk.CTkFont(family="Courier", size=12)
        )
        self.activity_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        # System Status Section
        status_frame = ctk.CTkFrame(self.parent)
        status_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        status_frame.grid_columnconfigure(1, weight=1)

        status_title = ctk.CTkLabel(
            status_frame, text="System Status", font=ctk.CTkFont(size=16, weight="bold")
        )
        status_title.grid(row=0, column=0, sticky="w", padx=15, pady=10)

        # Status indicators
        indicators_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        indicators_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 10))

        # Service statuses
        services = [
            ("Allocation Engine", self.check_allocation_engine_status()),
            ("Excel Service", self.check_excel_service_status()),
            ("Email Service", "Disabled"),
            ("Cache Service", "Active"),
        ]

        for i, (service, status) in enumerate(services):
            self.create_status_indicator(indicators_frame, service, status, row=0, column=i)

    def create_status_indicator(self, parent, label: str, status: str, row: int, column: int):
        """Create a status indicator widget.

        Args:
            parent: Parent widget.
            label: Service label.
            status: Service status.
            row: Grid row.
            column: Grid column.
        """
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=column, padx=10, pady=5)

        # Status dot
        color = "green" if status == "Active" else "orange" if status == "Disabled" else "red"
        dot_label = ctk.CTkLabel(frame, text="●", font=ctk.CTkFont(size=12), text_color=color)
        dot_label.grid(row=0, column=0, padx=(0, 5))

        # Service name
        name_label = ctk.CTkLabel(frame, text=f"{label}:", font=ctk.CTkFont(size=12))
        name_label.grid(row=0, column=1)

        # Status text
        status_label = ctk.CTkLabel(
            frame, text=status, font=ctk.CTkFont(size=12, weight="bold"), text_color=color
        )
        status_label.grid(row=0, column=2, padx=(5, 0))

    def update_metrics(self):
        """Update dashboard metrics."""
        try:
            # Prefer live read from Vehicle Status for Total Vehicles
            total_vehicles_from_file = None
            if self.dashboard_data_service:
                ds_path = self._resolve_daily_summary_path()
                try:
                    total_vehicles_from_file = (
                        self.dashboard_data_service.total_operational_vehicles(ds_path)
                    )
                except Exception as e:
                    logger.debug(f"Dashboard total vehicles read failed: {e}")

            if self.allocation_engine:
                metrics = self.allocation_engine.get_metrics()

                # Update metric cards
                if total_vehicles_from_file is not None:
                    self.total_vehicles_card.update_value(
                        str(total_vehicles_from_file), "Available for allocation"
                    )
                else:
                    self.total_vehicles_card.update_value(
                        str(metrics.total_vehicles), "Available for allocation"
                    )

                # Prefer driver count from Daily Routes if available
                total_drivers_from_file = None
                if self.dashboard_data_service:
                    dr_path = self._resolve_daily_routes_path()
                    try:
                        total_drivers_from_file = self.dashboard_data_service.total_drivers(dr_path)
                    except Exception as e:
                        logger.debug(f"Dashboard total drivers read failed: {e}")

                if total_drivers_from_file is not None:
                    self.total_drivers_card.update_value(
                        str(total_drivers_from_file), f"{metrics.active_drivers} active"
                    )
                else:
                    self.total_drivers_card.update_value(
                        str(metrics.total_drivers), f"{metrics.active_drivers} active"
                    )

                self.allocated_card.update_value(
                    str(metrics.allocated_vehicles), "Vehicles assigned"
                )

                rate_percent = float(metrics.allocation_rate) * 100
                self.allocation_rate_card.update_value(f"{rate_percent:.1f}%", "Success rate")

                self.unallocated_card.update_value(
                    str(metrics.unallocated_vehicles), "Pending assignment"
                )

                avg_per_driver = float(metrics.average_vehicles_per_driver)
                self.avg_per_driver_card.update_value(
                    f"{avg_per_driver:.1f}", "Vehicles per driver"
                )

                self.processing_time_card.update_value(
                    f"{metrics.processing_time:.2f}s", "Last allocation"
                )

                # Update last run time
                if metrics.timestamp:
                    time_diff = datetime.now() - metrics.timestamp
                    if time_diff.days > 0:
                        time_str = f"{time_diff.days}d ago"
                    elif time_diff.seconds > 3600:
                        time_str = f"{time_diff.seconds // 3600}h ago"
                    elif time_diff.seconds > 60:
                        time_str = f"{time_diff.seconds // 60}m ago"
                    else:
                        time_str = "Just now"

                    self.last_run_card.update_value(
                        metrics.timestamp.strftime("%H:%M:%S"), time_str
                    )

                # Update activity history
                self.update_activity_history()

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    def update_activity_history(self):
        """Update the activity history display."""
        try:
            if self.allocation_engine:
                history = self.allocation_engine.get_history(limit=10)

                self.activity_text.delete("1.0", "end")

                if history:
                    for result in reversed(history):
                        summary = result.get_allocation_summary()
                        timestamp = result.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                        status_emoji = "✅" if result.status == "completed" else "⚠️"

                        text = (
                            f"{status_emoji} {timestamp}\n"
                            f"   Request ID: {result.request_id[:8]}...\n"
                            f"   Drivers: {summary['total_drivers']}, "
                            f"Allocated: {summary['total_allocated_vehicles']}, "
                            f"Unallocated: {summary['total_unallocated_vehicles']}\n"
                            f"   Rate: {summary['allocation_rate']:.1%}\n"
                            f"{'-' * 60}\n"
                        )

                        self.activity_text.insert("end", text)
                else:
                    self.activity_text.insert("1.0", "No allocation history available.\n")

                self.activity_text.configure(state="disabled")

        except Exception as e:
            logger.error(f"Error updating activity history: {e}")

    def check_allocation_engine_status(self) -> str:
        """Check allocation engine status.

        Returns:
            Status string.
        """
        if self.allocation_engine and self.allocation_engine.is_initialized():
            return "Active"
        return "Inactive"

    def check_excel_service_status(self) -> str:
        """Check Excel service status.

        Returns:
            Status string.
        """
        return "Active"  # Placeholder

    def refresh_dashboard(self):
        """Refresh dashboard data."""

        def refresh_thread():
            self.update_metrics()

        thread = threading.Thread(target=refresh_thread)
        thread.daemon = True
        thread.start()

        logger.info("Dashboard refreshed")
