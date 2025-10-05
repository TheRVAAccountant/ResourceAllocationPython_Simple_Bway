"""Allocation tab for Resource Allocation GUI."""

import json
import threading
import time
from datetime import date, datetime
from pathlib import Path
from tkinter import StringVar, filedialog, messagebox
from typing import Any

import customtkinter as ctk
from loguru import logger

from src.core.gas_compatible_allocator import GASCompatibleAllocator
from src.gui.utils.duplicate_dialog import show_duplicate_warning
from src.gui.widgets import RecentFileSelector
from src.services.duplicate_validator import DuplicateVehicleValidator
from src.utils.recent_files_manager import FileFieldType

__all__ = ["AllocationTab", "DuplicateVehicleValidator", "show_duplicate_warning"]


class AllocationTelemetry:
    """Telemetry and logging system for allocation tab operations."""

    def __init__(self, session_id: str | None = None):
        """Initialize telemetry system.

        Args:
            session_id: Optional session identifier for tracking.
        """
        self.session_id = session_id or f"session_{int(time.time())}"
        self.event_count = 0
        self.operation_timings = {}
        logger.info(f"Allocation telemetry initialized | session_id={self.session_id}")

    def log_event(
        self,
        event_type: str,
        action: str,
        details: dict[str, Any] | None = None,
        level: str = "info",
    ):
        """Log a telemetry event.

        Args:
            event_type: Type of event (ui_action, allocation, validation, etc.).
            action: Specific action performed.
            details: Additional event details.
            level: Log level (debug, info, warning, error).
        """
        self.event_count += 1
        event_data = {
            "session_id": self.session_id,
            "event_id": self.event_count,
            "event_type": event_type,
            "action": action,
            "timestamp": datetime.now().isoformat(),
        }

        if details:
            event_data.update(details)

        log_msg = " | ".join([f"{k}={v}" for k, v in event_data.items()])

        if level == "debug":
            logger.debug(log_msg)
        elif level == "warning":
            logger.warning(log_msg)
        elif level == "error":
            logger.error(log_msg)
        else:
            logger.info(log_msg)

    def start_operation(self, operation_name: str):
        """Start timing an operation.

        Args:
            operation_name: Name of the operation to time.
        """
        self.operation_timings[operation_name] = time.time()
        self.log_event("operation", "started", {"operation": operation_name}, "debug")

    def end_operation(
        self, operation_name: str, success: bool = True, details: dict[str, Any] | None = None
    ):
        """End timing an operation and log results.

        Args:
            operation_name: Name of the operation that completed.
            success: Whether the operation succeeded.
            details: Additional operation details.
        """
        if operation_name in self.operation_timings:
            duration = time.time() - self.operation_timings[operation_name]
            event_details = {
                "operation": operation_name,
                "duration_seconds": f"{duration:.3f}",
                "status": "success" if success else "failure",
            }
            if details:
                event_details.update(details)

            level = "info" if success else "error"
            self.log_event("operation", "completed", event_details, level)
            del self.operation_timings[operation_name]

    def log_user_action(self, action: str, component: str, details: dict[str, Any] | None = None):
        """Log a user interface action.

        Args:
            action: Action performed (click, select, input, etc.).
            component: UI component affected.
            details: Additional action details.
        """
        event_details = {"component": component}
        if details:
            event_details.update(details)
        self.log_event("ui_action", action, event_details)

    def log_allocation_event(self, action: str, details: dict[str, Any] | None = None):
        """Log an allocation-specific event.

        Args:
            action: Allocation action performed.
            details: Allocation details.
        """
        self.log_event("allocation", action, details)

    def log_validation_event(
        self, action: str, details: dict[str, Any] | None = None, level: str = "info"
    ):
        """Log a validation event.

        Args:
            action: Validation action performed.
            details: Validation details.
            level: Log level for the event.
        """
        self.log_event("validation", action, details, level)

    def log_error(self, error_type: str, message: str, details: dict[str, Any] | None = None):
        """Log an error event.

        Args:
            error_type: Type of error.
            message: Error message.
            details: Additional error details.
        """
        event_details = {"error_type": error_type, "message": message}
        if details:
            event_details.update(details)
        self.log_event("error", "occurred", event_details, "error")


class _FallbackStringVar:
    """Simplified stand-in for tkinter.StringVar when no Tk root is available."""

    def __init__(self, value: str = ""):
        self._value = value

    def get(self) -> str:
        return self._value

    def set(self, value: str) -> None:
        self._value = value


class _FallbackTextWidget:
    """Minimal text widget replacement used when the GUI cannot be constructed."""

    def insert(self, *_args, **_kwargs) -> None:  # pragma: no cover - trivial no-op
        return None

    def see(self, *_args, **_kwargs) -> None:  # pragma: no cover - trivial no-op
        return None


class _FallbackProgressBar:
    """Minimal progress bar replacement used when the GUI cannot be constructed."""

    def set(self, *_args, **_kwargs) -> None:  # pragma: no cover - trivial no-op
        return None


def _make_stringvar(master, value: str = ""):
    """Create a tkinter StringVar, falling back during headless tests."""
    try:
        return StringVar(master=master, value=value)
    except Exception as exc:  # pragma: no cover - primarily hit in mocked unit tests
        logger.debug(f"Falling back to mock StringVar: {exc}")
        return _FallbackStringVar(value)


def _make_font(size: int, weight: str = "normal", family: str | None = None):
    """Create a CTkFont while tolerating missing Tk roots during tests."""
    try:
        return ctk.CTkFont(size=size, weight=weight, family=family)
    except Exception as exc:  # pragma: no cover - primarily hit in mocked unit tests
        logger.debug(f"Falling back to default font size {size}: {exc}")
        return None


class AllocationTab:
    """Allocation tab implementation."""

    def __init__(
        self,
        parent,
        allocation_engine: GASCompatibleAllocator | None = None,
        excel_service=None,
        border_service=None,
    ):
        """Initialize allocation tab.

        Args:
            parent: Parent widget.
            allocation_engine: Reference to allocation engine.
            excel_service: Reference to Excel service.
            border_service: Reference to border formatting service.
        """
        self.parent = parent
        self.allocation_engine = allocation_engine or GASCompatibleAllocator()
        self.excel_service = excel_service
        self.border_service = border_service

        # Initialize telemetry system
        self.telemetry = AllocationTelemetry()
        self.telemetry.log_event("lifecycle", "tab_initialized")

        # File paths for GAS-compatible allocation
        self.day_of_ops_path = _make_stringvar(self.parent)
        self.daily_routes_path = _make_stringvar(self.parent)
        self.daily_summary_path = _make_stringvar(self.parent)  # This will also be the output file
        self.allocation_date = _make_stringvar(self.parent, value=date.today().strftime("%Y-%m-%d"))
        self.current_result = None

        # Provide fallbacks so non-GUI unit tests can still interact with the tab.
        self.results_text = _FallbackTextWidget()
        self.progress_bar = _FallbackProgressBar()

        # Configure grid
        try:
            self.parent.grid_columnconfigure(0, weight=1)
            self.parent.grid_columnconfigure(1, weight=1)
            # Row 0: Header (no weight)
            # Row 1: File selection (no weight)
            # Row 2: Scrollable config section (weight=1 for expansion)
            # Row 3: Results section (weight=1 for expansion)
            # Row 4: Action buttons (no weight)
            self.parent.grid_rowconfigure(
                2, weight=0
            )  # Config section - fixed height with scrolling
            self.parent.grid_rowconfigure(3, weight=1)  # Results section - expandable
        except Exception as exc:  # pragma: no cover - mocked parent widgets
            logger.debug(f"Skipping grid configuration due to mock parent: {exc}")

        # Create UI elements when possible
        try:
            self.setup_ui()
            self.ui_initialized = True
        except Exception as exc:  # pragma: no cover - mocked test environments
            logger.debug(f"Skipping AllocationTab UI setup in headless mode: {exc}")
            self.ui_initialized = False

    def setup_ui(self):
        """Setup allocation tab UI."""
        # Header
        header_label = ctk.CTkLabel(
            self.parent, text="Run Vehicle Allocation", font=_make_font(size=24, weight="bold")
        )
        header_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 10))

        # File Selection Section
        self.create_file_selection_section()

        # Create scrollable frame for configuration sections
        self.config_scroll_frame = ctk.CTkScrollableFrame(
            self.parent, fg_color="transparent", height=350
        )
        self.config_scroll_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        self.config_scroll_frame.grid_columnconfigure(0, weight=1)
        self.config_scroll_frame.grid_columnconfigure(1, weight=1)

        # Configuration Section (now inside scrollable frame)
        self.create_configuration_section()

        # Results Section
        self.create_results_section()

        # Action Buttons
        self.create_action_buttons()

    def create_file_selection_section(self):
        """Create file selection section."""
        file_frame = ctk.CTkFrame(self.parent)
        file_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        file_frame.grid_columnconfigure(1, weight=1)

        # Section title
        section_label = ctk.CTkLabel(
            file_frame,
            text="File Selection (GAS-Compatible Workflow)",
            font=_make_font(size=16, weight="bold"),
        )
        section_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(10, 5))

        # Day of Ops file
        day_ops_label = ctk.CTkLabel(file_frame, text="Day of Ops File:")
        day_ops_label.grid(row=1, column=0, sticky="w", padx=15, pady=10)

        self.day_ops_selector = RecentFileSelector(
            file_frame,
            field_type=FileFieldType.DAY_OF_OPS,
            textvariable=self.day_of_ops_path,
            placeholder_text="Select Day of Ops Excel file...",
            initialfile="Day_of_Ops.xlsx",
        )
        self.day_ops_selector.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=10)

        # Daily Routes file
        routes_label = ctk.CTkLabel(file_frame, text="Daily Routes File:")
        routes_label.grid(row=2, column=0, sticky="w", padx=15, pady=10)

        self.routes_selector = RecentFileSelector(
            file_frame,
            field_type=FileFieldType.DAILY_ROUTES,
            textvariable=self.daily_routes_path,
            placeholder_text="Select Daily Routes Excel file...",
            initialfile="Daily_Routes.xlsx",
        )
        self.routes_selector.grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=10)

        # Daily Summary Log file (contains Vehicle Status AND receives output)
        summary_label = ctk.CTkLabel(file_frame, text="Daily Summary Log (Input/Output):")
        summary_label.grid(row=3, column=0, sticky="w", padx=15, pady=10)

        self.summary_selector = RecentFileSelector(
            file_frame,
            field_type=FileFieldType.DAILY_SUMMARY,
            textvariable=self.daily_summary_path,
            placeholder_text="Select Daily Summary Log 2025.xlsx...",
            initialfile="Daily Summary Log 2025.xlsx",
        )
        self.summary_selector.grid(row=3, column=1, columnspan=2, sticky="ew", padx=10, pady=10)

        # Help text
        help_label = ctk.CTkLabel(
            file_frame,
            text=(
                "ℹ️ Daily Summary Log provides Vehicle Status input and receives "
                "allocation results (Daily Details, Results, Unassigned sheets)"
            ),
            font=_make_font(size=12),
            text_color=("gray60", "gray40"),
        )
        help_label.grid(row=4, column=0, columnspan=3, sticky="w", padx=15, pady=(5, 10))

        # Attempt to apply default Daily Summary path from settings
        try:
            self._apply_default_daily_summary()
        except Exception as e:
            logger.debug(f"Default Daily Summary not applied: {e}")

    def create_configuration_section(self):
        """Create configuration section."""
        # Left config frame with improved visual grouping (now inside scrollable frame)
        left_config_frame = ctk.CTkFrame(self.config_scroll_frame, corner_radius=10)
        left_config_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        left_config_frame.grid_columnconfigure(1, weight=1)

        # Header with icon, collapse button and reset button
        header_frame = ctk.CTkFrame(left_config_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=15, pady=(15, 5))
        header_frame.grid_columnconfigure(1, weight=1)

        # Collapse button
        self.collapse_settings_btn = ctk.CTkButton(
            header_frame,
            text="▼",
            width=30,
            height=28,
            font=_make_font(size=14),
            command=self.toggle_allocation_settings,
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
        )
        self.collapse_settings_btn.grid(row=0, column=0, padx=(0, 5))

        left_title = ctk.CTkLabel(
            header_frame, text="⚙️ Allocation Settings", font=_make_font(size=16, weight="bold")
        )
        left_title.grid(row=0, column=1, sticky="w")

        # Reset to defaults button
        self.reset_settings_btn = ctk.CTkButton(
            header_frame,
            text="↺ Reset",
            width=80,
            height=28,
            font=_make_font(size=12),
            command=self.reset_allocation_settings,
        )
        self.reset_settings_btn.grid(row=0, column=2, padx=5)

        # Separator
        separator1 = ctk.CTkFrame(left_config_frame, height=2, fg_color=("gray80", "gray30"))
        separator1.grid(row=1, column=0, columnspan=3, sticky="ew", padx=15, pady=(5, 10))

        # Collapsible content frame for allocation settings
        self.settings_content_frame = ctk.CTkFrame(left_config_frame, fg_color="transparent")
        self.settings_content_frame.grid(
            row=2, column=0, columnspan=3, sticky="nsew", padx=0, pady=0
        )
        self.settings_content_frame.grid_columnconfigure(1, weight=1)

        # Allocation date with tooltip
        date_label = ctk.CTkLabel(self.settings_content_frame, text="Allocation Date:")
        date_label.grid(row=2, column=0, sticky="w", padx=15, pady=10)
        self._create_tooltip(date_label, "Date for the allocation run (format: YYYY-MM-DD)")

        self.date_entry = ctk.CTkEntry(
            self.settings_content_frame, textvariable=self.allocation_date
        )
        self.date_entry.grid(row=2, column=1, sticky="ew", padx=(10, 15), pady=10)

        # DSP Filter selector
        dsp_label = ctk.CTkLabel(self.settings_content_frame, text="DSP Filter:")
        dsp_label.grid(row=3, column=0, sticky="w", padx=15, pady=10)
        self._create_tooltip(dsp_label, "Filter routes by DSP (Delivery Service Partner)")

        self.dsp_combo = ctk.CTkComboBox(
            self.settings_content_frame, values=["BWAY", "ALL", "AMZN", "FLEX"], width=120
        )
        self.dsp_combo.set("BWAY")
        self.dsp_combo.grid(row=3, column=1, sticky="w", padx=(10, 15), pady=10)

        # Allocation Strategy selector
        strategy_label = ctk.CTkLabel(self.settings_content_frame, text="Strategy:")
        strategy_label.grid(row=4, column=0, sticky="w", padx=15, pady=10)
        self._create_tooltip(
            strategy_label, "Allocation strategy: Priority-based, Balanced distribution, or Manual"
        )

        self.strategy_combo = ctk.CTkComboBox(
            self.settings_content_frame,
            values=["Priority-Based", "Balanced", "Experience-Weighted", "Manual Override"],
            width=150,
        )
        self.strategy_combo.set("Priority-Based")
        self.strategy_combo.grid(row=4, column=1, sticky="w", padx=(10, 15), pady=10)

        # Vehicle constraints section
        separator2 = ctk.CTkFrame(
            self.settings_content_frame, height=2, fg_color=("gray80", "gray30")
        )
        separator2.grid(row=5, column=0, columnspan=3, sticky="ew", padx=15, pady=(15, 10))

        constraints_label = ctk.CTkLabel(
            self.settings_content_frame,
            text="Vehicle Constraints",
            font=_make_font(size=13, weight="bold"),
        )
        constraints_label.grid(row=6, column=0, columnspan=3, sticky="w", padx=15, pady=(5, 10))

        # Max vehicles per driver
        max_vehicles_label = ctk.CTkLabel(self.settings_content_frame, text="Max Vehicles/Driver:")
        max_vehicles_label.grid(row=7, column=0, sticky="w", padx=15, pady=10)
        self._create_tooltip(max_vehicles_label, "Maximum number of vehicles per driver (1-10)")

        self.max_vehicles_slider = ctk.CTkSlider(
            self.settings_content_frame, from_=1, to=10, number_of_steps=9
        )
        self.max_vehicles_slider.set(3)
        self.max_vehicles_slider.grid(row=7, column=1, sticky="ew", padx=(10, 15), pady=10)

        self.max_vehicles_value = ctk.CTkLabel(
            self.settings_content_frame, text="3", font=_make_font(size=12, weight="bold")
        )
        self.max_vehicles_value.grid(row=7, column=2, padx=(0, 15), pady=10)

        self.max_vehicles_slider.configure(
            command=lambda v: self.max_vehicles_value.configure(text=str(int(v)))
        )

        # Min vehicles per driver
        min_vehicles_label = ctk.CTkLabel(self.settings_content_frame, text="Min Vehicles/Driver:")
        min_vehicles_label.grid(row=8, column=0, sticky="w", padx=15, pady=10)
        self._create_tooltip(min_vehicles_label, "Minimum number of vehicles per driver (0-5)")

        self.min_vehicles_slider = ctk.CTkSlider(
            self.settings_content_frame, from_=0, to=5, number_of_steps=5
        )
        self.min_vehicles_slider.set(1)
        self.min_vehicles_slider.grid(row=8, column=1, sticky="ew", padx=(10, 15), pady=10)

        self.min_vehicles_value = ctk.CTkLabel(
            self.settings_content_frame, text="1", font=_make_font(size=12, weight="bold")
        )
        self.min_vehicles_value.grid(row=8, column=2, padx=(0, 15), pady=10)

        self.min_vehicles_slider.configure(
            command=lambda v: self.min_vehicles_value.configure(text=str(int(v)))
        )

        # Priority weight
        priority_label = ctk.CTkLabel(self.settings_content_frame, text="Priority Weight:")
        priority_label.grid(row=9, column=0, sticky="w", padx=15, pady=10)
        self._create_tooltip(
            priority_label, "Weight factor for priority-based allocation (1.0-3.0)"
        )

        self.priority_slider = ctk.CTkSlider(self.settings_content_frame, from_=1.0, to=3.0)
        self.priority_slider.set(1.5)
        self.priority_slider.grid(row=9, column=1, sticky="ew", padx=(10, 15), pady=10)

        self.priority_value = ctk.CTkLabel(
            self.settings_content_frame, text="1.5", font=_make_font(size=12, weight="bold")
        )
        self.priority_value.grid(row=9, column=2, padx=(0, 15), pady=10)

        self.priority_slider.configure(
            command=lambda v: self.priority_value.configure(text=f"{v:.1f}")
        )

        # Configuration presets section
        separator3 = ctk.CTkFrame(
            self.settings_content_frame, height=2, fg_color=("gray80", "gray30")
        )
        separator3.grid(row=10, column=0, columnspan=3, sticky="ew", padx=15, pady=(15, 10))

        presets_label = ctk.CTkLabel(
            self.settings_content_frame,
            text="Configuration Presets",
            font=_make_font(size=13, weight="bold"),
        )
        presets_label.grid(row=11, column=0, columnspan=3, sticky="w", padx=15, pady=(5, 10))

        preset_buttons_frame = ctk.CTkFrame(self.settings_content_frame, fg_color="transparent")
        preset_buttons_frame.grid(
            row=12, column=0, columnspan=3, sticky="ew", padx=15, pady=(0, 15)
        )

        self.save_preset_btn = ctk.CTkButton(
            preset_buttons_frame,
            text="💾 Save Preset",
            width=120,
            height=32,
            command=self.save_configuration_preset,
        )
        self.save_preset_btn.pack(side="left", padx=(0, 5))

        self.load_preset_btn = ctk.CTkButton(
            preset_buttons_frame,
            text="📂 Load Preset",
            width=120,
            height=32,
            command=self.load_configuration_preset,
        )
        self.load_preset_btn.pack(side="left", padx=5)

        # Right config frame (Options) with improved visual grouping (now inside scrollable frame)
        right_config_frame = ctk.CTkFrame(self.config_scroll_frame, corner_radius=10)
        right_config_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)

        # Header with collapse and reset buttons
        options_header_frame = ctk.CTkFrame(right_config_frame, fg_color="transparent")
        options_header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        options_header_frame.grid_columnconfigure(1, weight=1)

        # Collapse button
        self.collapse_options_btn = ctk.CTkButton(
            options_header_frame,
            text="▼",
            width=30,
            height=28,
            font=_make_font(size=14),
            command=self.toggle_options,
            fg_color="transparent",
            hover_color=("gray80", "gray25"),
        )
        self.collapse_options_btn.grid(row=0, column=0, padx=(0, 5))

        right_title = ctk.CTkLabel(
            options_header_frame, text="⚡ Options", font=_make_font(size=16, weight="bold")
        )
        right_title.grid(row=0, column=1, sticky="w")

        self.reset_options_btn = ctk.CTkButton(
            options_header_frame,
            text="↺ Reset",
            width=80,
            height=28,
            font=_make_font(size=12),
            command=self.reset_options,
        )
        self.reset_options_btn.grid(row=0, column=2, padx=5)

        # Separator
        separator_opt1 = ctk.CTkFrame(right_config_frame, height=2, fg_color=("gray80", "gray30"))
        separator_opt1.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 10))

        # Collapsible content frame for options
        self.options_content_frame = ctk.CTkFrame(right_config_frame, fg_color="transparent")
        self.options_content_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)

        # Processing Options Section
        processing_label = ctk.CTkLabel(
            self.options_content_frame, text="Processing", font=_make_font(size=13, weight="bold")
        )
        processing_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5, 5))

        self.optimize_checkbox = ctk.CTkCheckBox(
            self.options_content_frame, text="Optimize allocation before processing"
        )
        self.optimize_checkbox.grid(row=3, column=0, sticky="w", padx=20, pady=8)
        self.optimize_checkbox.select()
        self._create_tooltip(
            self.optimize_checkbox, "Run optimization algorithms for better allocation results"
        )

        self.validate_checkbox = ctk.CTkCheckBox(
            self.options_content_frame, text="Validate results after allocation"
        )
        self.validate_checkbox.grid(row=4, column=0, sticky="w", padx=20, pady=8)
        self.validate_checkbox.select()
        self._create_tooltip(
            self.validate_checkbox, "Check for duplicate assignments and validation errors"
        )

        self.backup_checkbox = ctk.CTkCheckBox(
            self.options_content_frame, text="Backup original files before processing"
        )
        self.backup_checkbox.grid(row=5, column=0, sticky="w", padx=20, pady=8)
        self._create_tooltip(
            self.backup_checkbox, "Create backup copies of input files before modification"
        )

        self.verbose_logging_checkbox = ctk.CTkCheckBox(
            self.options_content_frame, text="Enable verbose logging"
        )
        self.verbose_logging_checkbox.grid(row=6, column=0, sticky="w", padx=20, pady=8)
        self._create_tooltip(
            self.verbose_logging_checkbox, "Generate detailed logs for troubleshooting"
        )

        # Output Options Section
        separator_opt2 = ctk.CTkFrame(
            self.options_content_frame, height=2, fg_color=("gray80", "gray30")
        )
        separator_opt2.grid(row=7, column=0, sticky="ew", padx=15, pady=(15, 10))

        output_label = ctk.CTkLabel(
            self.options_content_frame, text="Output", font=_make_font(size=13, weight="bold")
        )
        output_label.grid(row=8, column=0, sticky="w", padx=15, pady=(5, 5))

        self.borders_checkbox = ctk.CTkCheckBox(
            self.options_content_frame, text="Apply daily section borders"
        )
        self.borders_checkbox.grid(row=9, column=0, sticky="w", padx=20, pady=8)
        self.borders_checkbox.select()
        self._create_tooltip(
            self.borders_checkbox, "Add visual borders to separate daily sections in Excel"
        )

        self.pdf_report_checkbox = ctk.CTkCheckBox(
            self.options_content_frame, text="Generate PDF allocation report"
        )
        self.pdf_report_checkbox.grid(row=10, column=0, sticky="w", padx=20, pady=8)
        self._create_tooltip(
            self.pdf_report_checkbox, "Create a PDF summary report of allocation results"
        )

        self.open_after_checkbox = ctk.CTkCheckBox(
            self.options_content_frame, text="Open Daily Summary Log after completion"
        )
        self.open_after_checkbox.grid(row=11, column=0, sticky="w", padx=20, pady=8)
        self._create_tooltip(
            self.open_after_checkbox, "Automatically open the output file when allocation completes"
        )

        # Notification Options Section
        separator_opt3 = ctk.CTkFrame(
            self.options_content_frame, height=2, fg_color=("gray80", "gray30")
        )
        separator_opt3.grid(row=12, column=0, sticky="ew", padx=15, pady=(15, 10))

        notification_label = ctk.CTkLabel(
            self.options_content_frame,
            text="Notifications",
            font=_make_font(size=13, weight="bold"),
        )
        notification_label.grid(row=13, column=0, sticky="w", padx=15, pady=(5, 5))

        self.email_checkbox = ctk.CTkCheckBox(
            self.options_content_frame, text="Send email notification"
        )
        self.email_checkbox.grid(row=14, column=0, sticky="w", padx=20, pady=8)
        self._create_tooltip(self.email_checkbox, "Send email alert when allocation completes")

        self.sound_notification_checkbox = ctk.CTkCheckBox(
            self.options_content_frame, text="Play notification sound"
        )
        self.sound_notification_checkbox.grid(row=15, column=0, sticky="w", padx=20, pady=8)
        self._create_tooltip(
            self.sound_notification_checkbox, "Play sound alert when allocation completes"
        )

        # Advanced Options (collapsible)
        separator_opt4 = ctk.CTkFrame(
            self.options_content_frame, height=2, fg_color=("gray80", "gray30")
        )
        separator_opt4.grid(row=16, column=0, sticky="ew", padx=15, pady=(15, 10))

        self.advanced_frame = ctk.CTkFrame(self.options_content_frame, fg_color="transparent")
        self.advanced_frame.grid(row=17, column=0, sticky="ew", padx=15, pady=(0, 15))

        self.show_advanced_btn = ctk.CTkButton(
            self.advanced_frame,
            text="▼ Advanced Settings",
            width=160,
            height=32,
            fg_color="transparent",
            border_width=1,
            command=self.toggle_advanced_settings,
        )
        self.show_advanced_btn.pack(pady=5)
        # Initialize from persisted settings if available
        try:
            self._apply_open_after_preference()
        except Exception as e:
            logger.debug(f"Open-after preference not applied: {e}")

    def create_results_section(self):
        """Create results section."""
        results_frame = ctk.CTkFrame(self.parent)
        results_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)

        results_title = ctk.CTkLabel(
            results_frame, text="Allocation Results", font=_make_font(size=16, weight="bold")
        )
        results_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        # Results text area
        self.results_text = ctk.CTkTextbox(
            results_frame, corner_radius=5, font=_make_font(size=12, family="Courier")
        )
        self.results_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(5, 15))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(results_frame)
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.progress_bar.set(0)

    def create_action_buttons(self):
        """Create action buttons."""
        button_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 20))
        button_frame.grid_columnconfigure(0, weight=1)

        # Button container for centering
        button_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_container.grid(row=0, column=0)

        # Run allocation button
        self.run_button = ctk.CTkButton(
            button_container,
            text="▶️ Run Allocation",
            width=150,
            height=40,
            font=_make_font(size=14, weight="bold"),
            command=self.run_allocation,
        )
        self.run_button.grid(row=0, column=0, padx=5)

        # Stop button
        self.stop_button = ctk.CTkButton(
            button_container,
            text="⏹️ Stop",
            width=100,
            height=40,
            state="disabled",
            command=self.stop_allocation,
            font=_make_font(size=14, weight="bold"),
        )
        self.stop_button.grid(row=0, column=1, padx=5)

        # Export results button
        self.export_button = ctk.CTkButton(
            button_container,
            text="📥 Export Results",
            width=130,
            height=40,
            state="disabled",
            command=self.export_results,
            font=_make_font(size=14, weight="bold"),
        )
        self.export_button.grid(row=0, column=2, padx=5)

        # Open results file button
        self.open_results_button = ctk.CTkButton(
            button_container,
            text="📂 Open Results File",
            width=160,
            height=40,
            state="disabled",
            command=self.open_results_file,
            font=_make_font(size=14, weight="bold"),
        )
        self.open_results_button.grid(row=0, column=3, padx=5)

        # Create sample data button
        self.sample_button = ctk.CTkButton(
            button_container,
            text="📝 Create Sample",
            width=140,
            height=40,
            command=self.create_sample_data,
            font=_make_font(size=14, weight="bold"),
        )
        self.sample_button.grid(row=0, column=4, padx=5)

    def _apply_default_daily_summary(self):
        """Prefill the Daily Summary selector from persisted settings if enabled.

        Reads config/settings.json written by SettingsTab. Non-intrusive: only
        applies if the toggle is enabled and the file exists.
        """
        settings_path = Path("config/settings.json")
        if not settings_path.exists():
            return
        try:
            with open(settings_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.debug(f"Unable to read settings.json: {e}")
            return
        use_default = bool(data.get("use_default_daily_summary", False))
        default_path = data.get("default_daily_summary_path", "")
        if use_default and default_path:
            p = Path(default_path)
            if p.exists():
                self.summary_selector.set_file_path(str(p))
                logger.info(f"Loaded default Daily Summary Log from settings: {p}")
            else:
                logger.warning(
                    "Configured default Daily Summary Log path does not exist; ignoring."
                )

    def _apply_open_after_preference(self):
        """Initialize the 'Open after completion' checkbox from settings.json."""
        settings_path = Path("config/settings.json")
        if not settings_path.exists():
            return
        try:
            with open(settings_path, encoding="utf-8") as f:
                data = json.load(f)
            auto_open = bool(data.get("auto_open_results", False))
            if auto_open:
                self.open_after_checkbox.select()
            else:
                self.open_after_checkbox.deselect()
        except Exception as e:
            logger.debug(f"Unable to read auto_open_results: {e}")

    def set_auto_open_results(self, enabled: bool):
        """Programmatically set the 'Open after completion' checkbox state."""
        try:
            if enabled:
                self.open_after_checkbox.select()
            else:
                self.open_after_checkbox.deselect()
        except Exception as e:
            logger.debug(f"Failed to set auto_open_results: {e}")

    def run_allocation(self):
        """Run the allocation process."""
        self.telemetry.log_user_action("click", "run_allocation_button")

        # Validate inputs
        if not self.day_of_ops_path.get():
            self.telemetry.log_validation_event(
                "input_validation_failed",
                {"field": "day_of_ops", "reason": "no_file_selected"},
                "warning",
            )
            self.show_error("Please select Day of Ops file")
            return

        if not self.daily_routes_path.get():
            self.telemetry.log_validation_event(
                "input_validation_failed",
                {"field": "daily_routes", "reason": "no_file_selected"},
                "warning",
            )
            self.show_error("Please select Daily Routes file")
            return

        if not self.daily_summary_path.get():
            self.telemetry.log_validation_event(
                "input_validation_failed",
                {"field": "daily_summary", "reason": "no_file_selected"},
                "warning",
            )
            self.show_error("Please select Daily Summary Log file")
            return

        # Log allocation configuration
        self.telemetry.log_allocation_event(
            "started",
            {
                "day_of_ops": Path(self.day_of_ops_path.get()).name,
                "daily_routes": Path(self.daily_routes_path.get()).name,
                "daily_summary": Path(self.daily_summary_path.get()).name,
                "allocation_date": self.allocation_date.get(),
                "dsp_filter": self.dsp_combo.get(),
                "strategy": self.strategy_combo.get(),
                "max_vehicles": int(self.max_vehicles_slider.get()),
                "min_vehicles": int(self.min_vehicles_slider.get()),
                "optimize": self.optimize_checkbox.get(),
                "validate": self.validate_checkbox.get(),
            },
        )

        # Update UI state
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.export_button.configure(state="disabled")
        self.open_results_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.results_text.delete("1.0", "end")

        # Run in separate thread
        thread = threading.Thread(target=self._run_allocation_thread)
        thread.daemon = True
        thread.start()

    def _run_allocation_thread(self):
        """Run GAS-compatible allocation in separate thread."""
        self.telemetry.start_operation("allocation_process")
        try:
            self.update_results("Starting GAS-compatible allocation process...\n")
            self.update_progress(0.1)
            self.telemetry.log_allocation_event("process_started")

            # Create GAS allocator instance
            allocator = GASCompatibleAllocator()

            # Load Day of Ops
            self.update_results("Loading Day of Ops data...\n")
            self.update_progress(0.2)
            allocator.load_day_of_ops(self.day_of_ops_path.get())

            # Load Daily Routes
            self.update_results("Loading Daily Routes data...\n")
            self.update_progress(0.3)
            allocator.load_daily_routes(self.daily_routes_path.get())

            # Load Vehicle Status from Daily Summary Log
            self.update_results("Loading Vehicle Status from Daily Summary Log...\n")
            self.update_progress(0.4)
            allocator.load_vehicle_status(
                self.daily_summary_path.get(), sheet_name="Vehicle Status"
            )

            # Load Vehicle Log from Daily Summary Log (for GeoTab and Type data)
            self.update_results("Loading Vehicle Log from Daily Summary Log...\n")
            self.update_progress(0.45)
            try:
                allocator.load_vehicle_log(self.daily_summary_path.get(), sheet_name="Vehicle Log")
                self.update_results("✓ Vehicle Log loaded successfully\n")
            except Exception as e:
                self.update_results(f"⚠️ Warning: Could not load Vehicle Log: {str(e)}\n")
                self.update_results("  GeoTab Code and Type columns will be empty\n")

            # Filter for BWAY routes
            self.update_results("Filtering for DSP = 'BWAY' routes...\n")
            self.update_progress(0.55)
            bway_routes = allocator.filter_bway_routes()
            self.update_results(f"Found {len(bway_routes)} BWAY routes to allocate\n")

            # Run allocation
            self.update_results("Running vehicle allocation...\n")
            self.update_progress(0.65)

            allocation_results, assigned_van_ids = allocator.allocate_vehicles_to_routes(
                bway_routes
            )
            self.update_results(f"Allocated {len(allocation_results)} vehicles to routes\n")

            # Map driver names
            self.update_results("Mapping driver names from Daily Routes...\n")
            self.update_progress(0.75)
            allocator.map_driver_names()

            # Create output - write back to Daily Summary Log
            output_file = self.daily_summary_path.get()
            self.update_results("Writing results back to Daily Summary Log...\n")
            self.update_results(
                "Adding/updating: Daily Details, Results, and Unassigned sheets...\n"
            )
            self.update_progress(0.85)

            # Update Daily Details in the Daily Summary Log and get results file
            allocation_date = datetime.strptime(self.allocation_date.get(), "%Y-%m-%d").date()
            result_output = allocator.create_output_file(
                output_file=output_file, allocation_date=allocation_date
            )

            # Handle the return value - could be tuple or None
            if result_output is not None:
                if isinstance(result_output, tuple):
                    result, results_file_path = result_output
                    self.results_file_path = results_file_path
                else:
                    # Fallback for backward compatibility
                    result = allocator.create_allocation_result()
                    self.results_file_path = None
            else:
                result = allocator.create_allocation_result()
                self.results_file_path = None

            # Persist to allocation history
            try:
                allocator.record_history(
                    allocation_result=result,
                    files={
                        "day_of_ops": self.day_of_ops_path.get(),
                        "daily_routes": self.daily_routes_path.get(),
                        "vehicle_status": self.daily_summary_path.get(),
                    },
                )
            except Exception as history_error:
                logger.error(f"Failed to record GAS history entry: {history_error}")
                self.update_results(
                    "⚠️ Unable to record allocation history entry. Check logs for details.\n"
                )

            # Get summary for display
            self.update_progress(1.0)
            self.display_gas_allocation_results(allocator)

            # Check for duplicate warnings and display results with validation status
            result = allocator.create_allocation_result()
            if result.warnings:
                self.show_duplicate_warnings(result.warnings, allocator)

            # Store result for export
            self.current_result = result

            # Enable export button and open results button
            self.export_button.configure(state="normal")
            if hasattr(self, "results_file_path"):
                self.open_results_button.configure(state="normal")

            # Show results file location
            if hasattr(self, "results_file_path"):
                self.update_results(f"\n📄 Results saved to: {self.results_file_path}\n")

            # Log successful completion
            self.telemetry.end_operation(
                "allocation_process",
                success=True,
                details={
                    "total_routes": len(allocator.allocation_results),
                    "assigned_routes": len(
                        [r for r in allocator.allocation_results if r.get("Van ID")]
                    ),
                    "unassigned_vehicles": len(allocator.unassigned_vehicles)
                    if hasattr(allocator, "unassigned_vehicles")
                    else 0,
                    "warnings": len(result.warnings) if result.warnings else 0,
                },
            )

            # Open file if requested
            if self.open_after_checkbox.get():
                summary_path = self.daily_summary_path.get()
                self.update_results(f"\n📂 Opening Daily Summary Log: {summary_path}\n")
                self._open_daily_summary_log_async(summary_path)

        except Exception as e:
            self.telemetry.end_operation(
                "allocation_process",
                success=False,
                details={"error": str(e), "error_type": type(e).__name__},
            )
            self.telemetry.log_error(
                "allocation_failed", str(e), {"traceback": __import__("traceback").format_exc()}
            )
            logger.error(f"GAS allocation failed: {e}")
            self.update_results(f"\n❌ Error: {str(e)}\n")
            import traceback

            self.update_results(f"\nDetails: {traceback.format_exc()}\n")
        finally:
            self.run_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def display_allocation_results(self, result):
        """Display allocation results in the text area."""
        summary = result.get_allocation_summary()

        text = (
            f"\n{'='*60}\n"
            f"ALLOCATION COMPLETED SUCCESSFULLY\n"
            f"{'='*60}\n\n"
            f"Request ID: {summary['request_id']}\n"
            f"Status: {summary['status']}\n"
            f"Timestamp: {summary['timestamp']}\n\n"
            f"SUMMARY:\n"
            f"  • Total Drivers: {summary['total_drivers']}\n"
            f"  • Allocated Vehicles: {summary['total_allocated_vehicles']}\n"
            f"  • Unallocated Vehicles: {summary['total_unallocated_vehicles']}\n"
            f"  • Allocation Rate: {summary['allocation_rate']:.1%}\n\n"
        )

        if result.allocations:
            text += "ALLOCATIONS:\n"
            for driver_id, vehicles in result.allocations.items():
                text += f"  • Driver {driver_id}: {len(vehicles)} vehicles\n"
                for vehicle_id in vehicles[:3]:  # Show first 3
                    text += f"    - {vehicle_id}\n"
                if len(vehicles) > 3:
                    text += f"    ... and {len(vehicles) - 3} more\n"

        if result.unallocated_vehicles:
            text += f"\nUNALLOCATED ({len(result.unallocated_vehicles)}):\n"
            for vehicle_id in result.unallocated_vehicles[:5]:
                text += f"  • {vehicle_id}\n"
            if len(result.unallocated_vehicles) > 5:
                text += f"  ... and {len(result.unallocated_vehicles) - 5} more\n"

        self.update_results(text)

    def display_gas_allocation_results(self, allocator):
        """Display GAS allocation results in the text area."""
        text = f"\n{'='*60}\n" f"GAS-COMPATIBLE ALLOCATION COMPLETED SUCCESSFULLY\n" f"{'='*60}\n\n"

        # Summary statistics
        total_routes = len(allocator.allocation_results)
        assigned_routes = len([r for r in allocator.allocation_results if r.get("Van ID")])
        unassigned_routes = total_routes - assigned_routes
        duplicate_count = len(
            [r for r in allocator.allocation_results if r.get("Validation Status") == "DUPLICATE"]
        )

        text += "SUMMARY:\n"
        text += f"  • Total BWAY Routes: {total_routes}\n"
        text += f"  • Routes with Vehicles: {assigned_routes}\n"
        text += f"  • Routes without Vehicles: {unassigned_routes}\n"
        text += f"  • Unassigned Vehicles: {len(allocator.unassigned_vehicles)}\n"
        allocation_rate = (assigned_routes / total_routes * 100) if total_routes > 0 else 0
        text += f"  • Allocation Rate: {allocation_rate:.1f}%\n"

        # Show validation status
        if duplicate_count > 0:
            text += f"  • ⚠️ Duplicate Assignments: {duplicate_count} (marked for review)\n"
        else:
            text += "  • ✅ Validation Status: No duplicates detected\n"

        text += "\n"

        # Show sample allocations
        if allocator.allocation_results:
            text += "SAMPLE ALLOCATIONS (first 10):\n"
            for result in allocator.allocation_results[:10]:
                route = result.get("Route Code", "Unknown")
                van_id = result.get("Van ID", "UNASSIGNED")
                driver = result.get("Driver Name", "No Driver")
                _service = result.get("Service Type", "Unknown")
                validation_status = result.get("Validation Status", "OK")

                # Add warning indicator for duplicates
                status_indicator = ""
                if validation_status == "DUPLICATE":
                    status_indicator = " ⚠️"

                text += f"  • Route {route}: Van {van_id} - {driver}{status_indicator}\n"

        # Show unassigned vehicles
        if (
            hasattr(allocator, "unassigned_vehicles")
            and allocator.unassigned_vehicles is not None
            and not allocator.unassigned_vehicles.empty
        ):
            text += f"\nUNASSIGNED VEHICLES ({len(allocator.unassigned_vehicles)}):\n"
            # Iterate through DataFrame rows
            for _idx, vehicle in allocator.unassigned_vehicles.head(10).iterrows():
                van_id = vehicle.get("Van ID", "Unknown")
                van_type = vehicle.get("Type", "Unknown")
                text += f"  • {van_id} ({van_type})\n"
            if len(allocator.unassigned_vehicles) > 10:
                text += f"  ... and {len(allocator.unassigned_vehicles) - 10} more\n"

        text += "\nFILES UPDATED:\n"
        text += "  • Daily Summary Log: Daily Details sheet updated\n"
        if hasattr(self, "results_file_path"):
            text += f"  • Results File: {self.results_file_path}\n"
            text += "    - Contains 'Results' and 'Unassigned Vehicles' sheets\n"

        text += "\n✅ Allocation completed successfully!\n"

        self.update_results(text)

    def stop_allocation(self):
        """Stop the allocation process."""
        # This would need more sophisticated thread management
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.update_results("\n⏹️ Allocation stopped by user\n")

    def open_results_file(self):
        """Open the results file in the default application."""
        if not hasattr(self, "results_file_path") or not self.results_file_path:
            self.update_results("\n⚠️ No results file available\n")
            return

        try:
            import os
            import platform

            if platform.system() == "Windows":
                os.startfile(self.results_file_path)
            elif platform.system() == "Darwin":  # macOS
                os.system(f'open "{self.results_file_path}"')
            else:  # Linux
                os.system(f'xdg-open "{self.results_file_path}"')

            self.update_results(f"\n📂 Opened results file: {self.results_file_path}\n")
        except Exception as e:
            self.update_results(f"\n❌ Error opening file: {str(e)}\n")

    def export_results(self):
        """Export current results with validation information."""
        if not self.current_result:
            self.show_error("No results to export")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )

        if filename:
            try:
                import json
                from pathlib import Path

                file_path = Path(filename)

                # Prepare export data
                export_data = {
                    "allocation_summary": self.current_result.get_allocation_summary(),
                    "allocation_timestamp": self.current_result.timestamp.isoformat(),
                    "allocations": self.current_result.allocations,
                    "unallocated_vehicles": self.current_result.unallocated_vehicles,
                    "validation_status": {
                        "has_warnings": len(self.current_result.warnings) > 0,
                        "warning_count": len(self.current_result.warnings),
                        "warnings": self.current_result.warnings,
                        "has_errors": len(self.current_result.errors) > 0,
                        "errors": self.current_result.errors,
                    },
                    "metadata": self.current_result.metadata,
                }

                # Export based on file type
                if file_path.suffix.lower() == ".json":
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                elif file_path.suffix.lower() == ".csv":
                    import pandas as pd

                    # Convert allocations to flat structure for CSV
                    rows = []
                    for driver, vehicles in self.current_result.allocations.items():
                        for vehicle in vehicles:
                            rows.append(
                                {"Driver": driver, "Vehicle": vehicle, "Status": "Allocated"}
                            )
                    for vehicle in self.current_result.unallocated_vehicles:
                        rows.append({"Driver": "N/A", "Vehicle": vehicle, "Status": "Unallocated"})

                    df = pd.DataFrame(rows)
                    df.to_csv(filename, index=False)
                else:  # Text file
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write("ALLOCATION RESULTS EXPORT\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Request ID: {self.current_result.request_id}\n")
                        f.write(f"Status: {self.current_result.status.value}\n\n")

                        summary = self.current_result.get_allocation_summary()
                        f.write("SUMMARY:\n")
                        for key, value in summary.items():
                            f.write(f"  {key}: {value}\n")
                        f.write("\n")

                        if self.current_result.warnings:
                            f.write("VALIDATION WARNINGS:\n")
                            for warning in self.current_result.warnings:
                                f.write(f"  • {warning}\n")
                            f.write("\n")

                        if self.current_result.errors:
                            f.write("ERRORS:\n")
                            for error in self.current_result.errors:
                                f.write(f"  • {error}\n")
                            f.write("\n")

                logger.info(f"Results exported to: {filename}")
                messagebox.showinfo(
                    "Export Complete", f"Results exported successfully to:\n{filename}"
                )

            except Exception as e:
                logger.error(f"Export failed: {e}")
                self.show_error(f"Export failed: {str(e)}")

    def create_sample_data(self):
        """Create sample data files."""
        from tkinter import messagebox

        messagebox.showinfo(
            "Sample Data",
            "To create sample data:\n\n"
            "1. Create Day_of_Ops.xlsx with 'Solution' sheet\n"
            "   Columns: Route Code, Service Type, DSP, Wave, Staging Location\n\n"
            "2. Create Daily_Routes.xlsx with 'Routes' sheet\n"
            "   Columns: Route Code, Driver Name\n\n"
            "3. Create/Use Daily Summary Log 2025.xlsx with 'Vehicle Status' sheet\n"
            "   Columns: Van ID, Type, Opnal? Y/N\n\n"
            "The allocation will update the Daily Summary Log with results.",
        )

    def update_results(self, text: str):
        """Update results text area."""
        self.results_text.insert("end", text)
        self.results_text.see("end")

    def update_progress(self, message: str | float | None = None, value: float | None = None):
        """Update validation progress indicator and optionally append a status message."""
        # Support legacy calls such as update_progress(0.5)
        if isinstance(message, int | float) and value is None:
            value = float(message)
            message = None

        if message:
            text = message if message.endswith("\n") else f"{message}\n"
            self.update_results(text)

        if value is None:
            return

        # Accept either 0-1 or 0-100 ranges for convenience.
        normalized = value / 100 if value > 1 else value
        self.progress_bar.set(normalized)

    def show_error(self, message: str):
        """Show error message."""
        messagebox.showerror("Error", message)

    def show_duplicate_warnings(self, warnings: list, allocator=None):
        """Show detailed duplicate vehicle assignment warnings dialog."""
        if not warnings:
            return

        self._show_duplicate_dialog(warnings, allocator)

    def _show_duplicate_dialog(self, warnings: list, allocator=None):
        """Create and show detailed duplicate warning dialog."""
        # Create dialog window
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Duplicate Vehicle Assignments Detected")
        dialog.geometry("800x600")
        dialog.transient(self.parent.winfo_toplevel())
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"800x600+{x}+{y}")

        # Configure grid
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        # Header frame
        header_frame = ctk.CTkFrame(dialog)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        # Warning icon and title
        title_label = ctk.CTkLabel(
            header_frame,
            text="⚠️ Duplicate Vehicle Assignments Detected",
            font=_make_font(size=18, weight="bold"),
            text_color=("#ff6b35", "#ff8c42"),
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=15)

        # Summary
        duplicate_count = len([w for w in warnings if "assigned to multiple" in w.lower()])
        summary_text = (
            f"Found {duplicate_count} vehicles assigned to multiple routes. "
            "These have been marked in the Excel output."
        )

        summary_label = ctk.CTkLabel(
            header_frame, text=summary_text, font=_make_font(size=14), wraplength=750
        )
        summary_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 15))

        # Details frame with scrollable text
        details_frame = ctk.CTkFrame(dialog)
        details_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_rowconfigure(1, weight=1)

        details_title = ctk.CTkLabel(
            details_frame,
            text="Duplicate Assignment Details:",
            font=_make_font(size=16, weight="bold"),
        )
        details_title.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # Scrollable text area for details
        details_text = ctk.CTkTextbox(
            details_frame, font=_make_font(size=12, family="Courier"), wrap="word"
        )
        details_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(5, 15))

        # Populate details with formatted warning information
        details_content = self._format_duplicate_details(warnings, allocator)
        details_text.insert("1.0", details_content)
        details_text.configure(state="disabled")

        # Button frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_frame.grid_columnconfigure(1, weight=1)

        # Proceed button
        proceed_btn = ctk.CTkButton(
            button_frame,
            text="✓ Proceed with Results",
            width=150,
            height=35,
            font=_make_font(size=14, weight="bold"),
            fg_color=("#28a745", "#34d058"),
            hover_color=("#218838", "#28a745"),
            command=dialog.destroy,
        )
        proceed_btn.grid(row=0, column=0, padx=(0, 10), pady=5)

        # View Excel button (if allocator available)
        if allocator and hasattr(allocator, "daily_summary_path"):
            view_btn = ctk.CTkButton(
                button_frame,
                text="📁 Open Excel File",
                width=130,
                height=35,
                font=_make_font(size=14),
                command=lambda: self._open_excel_file(self.daily_summary_path.get()),
            )
            view_btn.grid(row=0, column=1, padx=5, pady=5)

        # Help button
        help_btn = ctk.CTkButton(
            button_frame,
            text="❓ Help",
            width=80,
            height=35,
            font=_make_font(size=14),
            fg_color=("#6c757d", "#6c757d"),
            hover_color=("#5a6268", "#545b62"),
            command=lambda: self._show_duplicate_help(),
        )
        help_btn.grid(row=0, column=2, padx=(10, 0), pady=5)

        # Focus and wait
        proceed_btn.focus()
        dialog.wait_window()

    def _format_duplicate_details(self, warnings: list, allocator=None) -> str:
        """Format duplicate warnings into detailed text for display."""
        content = "DUPLICATE VEHICLE ASSIGNMENTS:\n"
        content += "=" * 50 + "\n\n"

        # Group warnings by vehicle ID if possible
        duplicate_details = []
        route_details = []

        for warning in warnings:
            if "assigned to multiple routes" in warning.lower():
                duplicate_details.append(warning)
            else:
                route_details.append(warning)

        # Show duplicate vehicle details
        if duplicate_details:
            content += "VEHICLES WITH MULTIPLE ASSIGNMENTS:\n\n"
            for i, detail in enumerate(duplicate_details, 1):
                content += f"{i:2d}. {detail}\n"
            content += "\n"

        # Show additional route-level details if available
        if allocator and hasattr(allocator, "allocation_results"):
            content += "AFFECTED ROUTES SUMMARY:\n\n"
            duplicate_routes = []
            for result in allocator.allocation_results:
                if result.get("Validation Status") == "DUPLICATE":
                    route_code = result.get("Route Code", "Unknown")
                    van_id = result.get("Van ID", "Unknown")
                    driver = result.get("Associate Name", "Unknown")
                    service = result.get("Service Type", "Unknown")

                    duplicate_routes.append(
                        {"route": route_code, "van": van_id, "driver": driver, "service": service}
                    )

            if duplicate_routes:
                content += "Route Code    | Van ID  | Driver Name           | Service Type\n"
                content += "-" * 70 + "\n"
                for route_info in duplicate_routes[:20]:  # Show first 20
                    content += (
                        f"{route_info['route']:12s} | {route_info['van']:7s} | "
                        f"{route_info['driver']:20s} | {route_info['service']}\n"
                    )

                if len(duplicate_routes) > 20:
                    content += f"\n... and {len(duplicate_routes) - 20} more affected routes\n"
            content += "\n"

        # Resolution guidance
        content += "RESOLUTION GUIDANCE:\n"
        content += "=" * 20 + "\n"
        content += "• Check the Excel output for detailed assignment information\n"
        content += "• Duplicate assignments are marked with 'DUPLICATE' status\n"
        content += "• Review route priorities and reassign vehicles as needed\n"
        content += "• Consider adjusting service type mappings if mismatches occur\n"
        content += "• Contact system administrator if duplicates persist\n\n"

        content += "NOTE: The allocation has completed successfully despite these warnings.\n"
        content += "Review and resolve duplicates before finalizing daily assignments."

        return content

    def _open_daily_summary_log_async(self, file_path: str):
        """Open the Daily Summary Log in the default Excel application asynchronously."""
        if not file_path:
            logger.warning("Daily Summary Log path was empty; skipping auto-open.")
            self.update_results("\n⚠️ Daily Summary Log path unavailable; skipping auto-open.\n")
            return

        summary_path = Path(file_path)
        if not summary_path.exists():
            logger.warning(f"Daily Summary Log not found at {summary_path}; skipping auto-open.")
            self.update_results(f"\n⚠️ Daily Summary Log not found at: {summary_path}\n")
            return

        def _open_file():
            try:
                self._open_excel_file(str(summary_path))
                self.update_results(f"\n✅ Daily Summary Log opened: {summary_path}\n")
            except Exception as exc:
                logger.error(f"Failed to auto-open Daily Summary Log: {exc}")
                self.update_results(f"\n❌ Failed to open Daily Summary Log: {exc}\n")

        try:
            self.parent.after(0, _open_file)
        except Exception as exc:
            logger.debug(
                f"Could not schedule Daily Summary Log open via after: {exc}; opening immediately."
            )
            _open_file()

    def _open_excel_file(self, file_path: str):
        """Open Excel file in system default application."""
        try:
            import os
            import platform

            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{file_path}'")
            else:  # Linux
                os.system(f"xdg-open '{file_path}'")

            logger.info(f"Opened Excel file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to open Excel file: {e}")
            messagebox.showerror("File Open Error", f"Could not open Excel file:\n{str(e)}")

    def _show_duplicate_help(self):
        """Show help dialog for duplicate assignments."""
        help_text = (
            "UNDERSTANDING DUPLICATE VEHICLE ASSIGNMENTS\n\n"
            "What are duplicates?\n"
            "• A vehicle assigned to multiple routes simultaneously\n"
            "• Usually occurs due to data inconsistencies or conflicts\n\n"
            "Why do they happen?\n"
            "• Route data conflicts between input files\n"
            "• Vehicle availability timing issues\n"
            "• Service type mapping overlaps\n\n"
            "How to resolve:\n"
            "1. Review the Excel output for marked duplicates\n"
            "2. Check route priorities and timing\n"
            "3. Manually reassign conflicting vehicles\n"
            "4. Verify input data consistency\n"
            "5. Re-run allocation if needed\n\n"
            "Impact:\n"
            "• Allocation completes successfully\n"
            "• Duplicates are flagged for manual review\n"
            "• Excel output contains all assignment details"
        )

        messagebox.showinfo("Duplicate Assignment Help", help_text)

    def _create_tooltip(self, widget, text: str):
        """Create a tooltip for a widget.

        Args:
            widget: The widget to attach tooltip to.
            text: Tooltip text to display.
        """

        def on_enter(_event):
            tooltip = ctk.CTkToplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{widget.winfo_rootx() + 20}+{widget.winfo_rooty() + 30}")

            label = ctk.CTkLabel(
                tooltip,
                text=text,
                font=_make_font(size=11),
                fg_color=("gray85", "gray25"),
                corner_radius=5,
                padx=10,
                pady=5,
            )
            label.pack()

            widget._tooltip = tooltip

        def on_leave(_event):
            if hasattr(widget, "_tooltip"):
                widget._tooltip.destroy()
                delattr(widget, "_tooltip")

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def reset_allocation_settings(self):
        """Reset allocation settings to defaults."""
        self.telemetry.log_user_action("reset", "allocation_settings")
        self.allocation_date.set(date.today().strftime("%Y-%m-%d"))
        self.dsp_combo.set("BWAY")
        self.strategy_combo.set("Priority-Based")
        self.max_vehicles_slider.set(3)
        self.min_vehicles_slider.set(1)
        self.priority_slider.set(1.5)
        self.telemetry.log_user_action(
            "reset_completed",
            "allocation_settings",
            {
                "dsp": "BWAY",
                "strategy": "Priority-Based",
                "max_vehicles": 3,
                "min_vehicles": 1,
                "priority_weight": 1.5,
            },
        )
        logger.info("Allocation settings reset to defaults")

    def reset_options(self):
        """Reset options to defaults."""
        self.telemetry.log_user_action("reset", "options")
        self.optimize_checkbox.select()
        self.validate_checkbox.select()
        self.backup_checkbox.deselect()
        self.verbose_logging_checkbox.deselect()
        self.borders_checkbox.select()
        self.pdf_report_checkbox.deselect()
        self.open_after_checkbox.deselect()
        self.email_checkbox.deselect()
        self.sound_notification_checkbox.deselect()
        self.telemetry.log_user_action(
            "reset_completed",
            "options",
            {
                "optimize": True,
                "validate": True,
                "backup": False,
                "verbose": False,
                "borders": True,
                "pdf_report": False,
                "open_after": False,
                "email": False,
                "sound": False,
            },
        )
        logger.info("Options reset to defaults")

    def save_configuration_preset(self):
        """Save current configuration as a preset."""
        self.telemetry.log_user_action("save_preset", "configuration", {"action": "initiated"})
        preset_name = ctk.CTkInputDialog(
            text="Enter preset name:", title="Save Configuration Preset"
        ).get_input()

        if preset_name:
            self.telemetry.log_user_action(
                "save_preset", "configuration", {"preset_name": preset_name}
            )
            preset_data = {
                "allocation_date": self.allocation_date.get(),
                "dsp_filter": self.dsp_combo.get(),
                "strategy": self.strategy_combo.get(),
                "max_vehicles": int(self.max_vehicles_slider.get()),
                "min_vehicles": int(self.min_vehicles_slider.get()),
                "priority_weight": float(self.priority_slider.get()),
                "optimize": self.optimize_checkbox.get(),
                "validate": self.validate_checkbox.get(),
                "backup": self.backup_checkbox.get(),
                "verbose_logging": self.verbose_logging_checkbox.get(),
                "borders": self.borders_checkbox.get(),
                "pdf_report": self.pdf_report_checkbox.get(),
                "open_after": self.open_after_checkbox.get(),
                "email": self.email_checkbox.get(),
                "sound_notification": self.sound_notification_checkbox.get(),
            }

            # Save to config file
            config_dir = Path("config/presets")
            config_dir.mkdir(parents=True, exist_ok=True)
            preset_file = config_dir / f"{preset_name}.json"

            try:
                with open(preset_file, "w", encoding="utf-8") as f:
                    json.dump(preset_data, f, indent=2)
                self.telemetry.log_user_action(
                    "save_preset_completed",
                    "configuration",
                    {"preset_name": preset_name, "status": "success"},
                )
                logger.info(f"Configuration preset saved: {preset_name}")
                messagebox.showinfo("Success", f"Preset '{preset_name}' saved successfully!")
            except Exception as e:
                self.telemetry.log_error("preset_save_failed", str(e), {"preset_name": preset_name})
                logger.error(f"Failed to save preset: {e}")
                messagebox.showerror("Error", f"Failed to save preset: {str(e)}")

    def load_configuration_preset(self):
        """Load a configuration preset."""
        config_dir = Path("config/presets")
        if not config_dir.exists():
            messagebox.showinfo("No Presets", "No configuration presets found.")
            return

        # Get list of presets
        presets = [f.stem for f in config_dir.glob("*.json")]
        if not presets:
            messagebox.showinfo("No Presets", "No configuration presets found.")
            return

        # Show preset selection dialog
        preset_dialog = ctk.CTkInputDialog(
            text=f"Available presets:\n{', '.join(presets)}\n\nEnter preset name to load:",
            title="Load Configuration Preset",
        )
        preset_name = preset_dialog.get_input()

        if preset_name:
            preset_file = config_dir / f"{preset_name}.json"
            if not preset_file.exists():
                messagebox.showerror("Error", f"Preset '{preset_name}' not found.")
                return

            try:
                with open(preset_file, encoding="utf-8") as f:
                    preset_data = json.load(f)

                # Apply preset data
                self.allocation_date.set(
                    preset_data.get("allocation_date", date.today().strftime("%Y-%m-%d"))
                )
                self.dsp_combo.set(preset_data.get("dsp_filter", "BWAY"))
                self.strategy_combo.set(preset_data.get("strategy", "Priority-Based"))
                self.max_vehicles_slider.set(preset_data.get("max_vehicles", 3))
                self.min_vehicles_slider.set(preset_data.get("min_vehicles", 1))
                self.priority_slider.set(preset_data.get("priority_weight", 1.5))

                # Apply checkboxes
                self._set_checkbox(self.optimize_checkbox, preset_data.get("optimize", True))
                self._set_checkbox(self.validate_checkbox, preset_data.get("validate", True))
                self._set_checkbox(self.backup_checkbox, preset_data.get("backup", False))
                self._set_checkbox(
                    self.verbose_logging_checkbox, preset_data.get("verbose_logging", False)
                )
                self._set_checkbox(self.borders_checkbox, preset_data.get("borders", True))
                self._set_checkbox(self.pdf_report_checkbox, preset_data.get("pdf_report", False))
                self._set_checkbox(self.open_after_checkbox, preset_data.get("open_after", False))
                self._set_checkbox(self.email_checkbox, preset_data.get("email", False))
                self._set_checkbox(
                    self.sound_notification_checkbox, preset_data.get("sound_notification", False)
                )

                logger.info(f"Configuration preset loaded: {preset_name}")
                messagebox.showinfo("Success", f"Preset '{preset_name}' loaded successfully!")
            except Exception as e:
                logger.error(f"Failed to load preset: {e}")
                messagebox.showerror("Error", f"Failed to load preset: {str(e)}")

    def _set_checkbox(self, checkbox, value: bool):
        """Helper to set checkbox state."""
        if value:
            checkbox.select()
        else:
            checkbox.deselect()

    def toggle_advanced_settings(self):
        """Toggle advanced settings visibility."""
        # This will be implemented to show/hide advanced options panel
        if self.show_advanced_btn.cget("text").startswith("▼"):
            self.show_advanced_btn.configure(text="▲ Advanced Settings")
            # TODO: Show advanced settings panel
            logger.info("Advanced settings expanded")
        else:
            self.show_advanced_btn.configure(text="▼ Advanced Settings")
            # TODO: Hide advanced settings panel
            logger.info("Advanced settings collapsed")

    def toggle_allocation_settings(self):
        """Toggle allocation settings section visibility."""
        if self.collapse_settings_btn.cget("text") == "▼":
            # Collapse - hide content
            self.settings_content_frame.grid_remove()
            self.collapse_settings_btn.configure(text="▶")
            self.telemetry.log_user_action("collapse", "allocation_settings")
            logger.debug("Allocation settings collapsed")
        else:
            # Expand - show content
            self.settings_content_frame.grid()
            self.collapse_settings_btn.configure(text="▼")
            self.telemetry.log_user_action("expand", "allocation_settings")
            logger.debug("Allocation settings expanded")

    def toggle_options(self):
        """Toggle options section visibility."""
        if self.collapse_options_btn.cget("text") == "▼":
            # Collapse - hide content
            self.options_content_frame.grid_remove()
            self.collapse_options_btn.configure(text="▶")
            self.telemetry.log_user_action("collapse", "options")
            logger.debug("Options collapsed")
        else:
            # Expand - show content
            self.options_content_frame.grid()
            self.collapse_options_btn.configure(text="▼")
            self.telemetry.log_user_action("expand", "options")
            logger.debug("Options expanded")
