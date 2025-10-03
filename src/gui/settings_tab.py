"""Settings tab for Resource Allocation GUI."""

import json
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable, Optional

import customtkinter as ctk
from loguru import logger


class SettingsTab:
    """Settings tab implementation."""

    def __init__(
        self,
        parent,
        allocation_engine,
        excel_service,
        on_settings_saved: Optional[Callable[[dict], None]] = None,
    ):
        """Initialize settings tab.

        Args:
            parent: Parent widget.
            allocation_engine: Reference to allocation engine.
            excel_service: Reference to Excel service.
        """
        self.parent = parent
        self.allocation_engine = allocation_engine
        self.excel_service = excel_service
        self.on_settings_saved = on_settings_saved

        self.settings = self.load_settings()
        self.unsaved_changes = False

        # Configure grid
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)

        # Create UI elements
        self.setup_ui()

    def setup_ui(self):
        """Setup settings UI."""
        # Create scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self.parent)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        # Header
        header_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="Application Settings",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        header_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Create settings sections
        self.create_general_settings()
        self.create_allocation_settings()
        self.create_excel_settings()
        self.create_email_settings()
        self.create_advanced_settings()
        self.create_workflow_defaults_settings()

        # Action buttons
        self.create_action_buttons()

    def create_general_settings(self):
        """Create general settings section."""
        section_frame = self.create_section("General Settings")
        row = 0

        # Company name (used to prefix the application title)
        self.create_setting_row(
            section_frame,
            row,
            "Company name:",
            "company_name",
            widget_type="entry",
            tooltip="Shown as '<Company> - Resource Management System' in the header and window title",
        )
        row += 1

        # Application theme
        self.create_setting_row(
            section_frame,
            row,
            "Theme:",
            "theme",
            widget_type="combo",
            values=["System", "Dark", "Light"],
            tooltip="Application appearance theme",
        )
        row += 1

        # Language
        self.create_setting_row(
            section_frame,
            row,
            "Language:",
            "language",
            widget_type="combo",
            values=["English", "Spanish", "French", "German"],
            tooltip="Interface language",
        )
        row += 1

        # Auto-save
        self.create_setting_row(
            section_frame,
            row,
            "Auto-save:",
            "auto_save",
            widget_type="checkbox",
            tooltip="Automatically save changes",
        )
        row += 1

        # Auto-save interval
        self.create_setting_row(
            section_frame,
            row,
            "Auto-save interval (minutes):",
            "auto_save_interval",
            widget_type="spinbox",
            min_value=1,
            max_value=60,
            tooltip="Minutes between auto-saves",
        )
        row += 1

        # Default directory
        self.create_setting_row(
            section_frame,
            row,
            "Default directory:",
            "default_directory",
            widget_type="path",
            tooltip="Default directory for file operations",
        )

    def create_allocation_settings(self):
        """Create allocation settings section."""
        section_frame = self.create_section("Allocation Settings")
        row = 0

        # Max vehicles per driver
        self.create_setting_row(
            section_frame,
            row,
            "Max vehicles per driver:",
            "max_vehicles_per_driver",
            widget_type="spinbox",
            min_value=1,
            max_value=10,
            tooltip="Maximum number of vehicles that can be assigned to one driver",
        )
        row += 1

        # Min vehicles per driver
        self.create_setting_row(
            section_frame,
            row,
            "Min vehicles per driver:",
            "min_vehicles_per_driver",
            widget_type="spinbox",
            min_value=0,
            max_value=5,
            tooltip="Minimum number of vehicles to assign to each driver",
        )
        row += 1

        # Priority weight factor
        self.create_setting_row(
            section_frame,
            row,
            "Priority weight factor:",
            "priority_weight_factor",
            widget_type="slider",
            min_value=1.0,
            max_value=3.0,
            tooltip="Weight factor for priority-based allocation",
        )
        row += 1

        # Allocation threshold
        self.create_setting_row(
            section_frame,
            row,
            "Allocation threshold:",
            "allocation_threshold",
            widget_type="slider",
            min_value=0.5,
            max_value=1.0,
            tooltip="Minimum allocation rate threshold",
        )
        row += 1

        # Optimization
        self.create_setting_row(
            section_frame,
            row,
            "Enable optimization:",
            "enable_optimization",
            widget_type="checkbox",
            tooltip="Optimize allocation before processing",
        )
        row += 1

        # Validation
        self.create_setting_row(
            section_frame,
            row,
            "Enable validation:",
            "enable_validation",
            widget_type="checkbox",
            tooltip="Validate results after allocation",
        )

    def create_excel_settings(self):
        """Create Excel settings section."""
        section_frame = self.create_section("Excel Settings")
        row = 0

        # Use xlwings
        self.create_setting_row(
            section_frame,
            row,
            "Use xlwings:",
            "use_xlwings",
            widget_type="checkbox",
            tooltip="Use xlwings for live Excel integration",
        )
        row += 1

        # Excel visible
        self.create_setting_row(
            section_frame,
            row,
            "Show Excel window:",
            "excel_visible",
            widget_type="checkbox",
            tooltip="Make Excel window visible during operations",
        )
        row += 1

        # Display alerts
        self.create_setting_row(
            section_frame,
            row,
            "Display Excel alerts:",
            "display_alerts",
            widget_type="checkbox",
            tooltip="Show Excel alerts and prompts",
        )
        row += 1

        # Template path
        self.create_setting_row(
            section_frame,
            row,
            "Template file:",
            "template_path",
            widget_type="file",
            tooltip="Excel template file path",
        )
        row += 1

        # Apply borders
        self.create_setting_row(
            section_frame,
            row,
            "Apply section borders:",
            "apply_borders",
            widget_type="checkbox",
            tooltip="Apply thick borders to daily sections",
        )
        row += 1

        # Border style
        self.create_setting_row(
            section_frame,
            row,
            "Border style:",
            "border_style",
            widget_type="combo",
            values=["Thin", "Medium", "Thick", "Double"],
            tooltip="Style for section borders",
        )

    def create_email_settings(self):
        """Create email settings section."""
        section_frame = self.create_section("Email Settings")
        row = 0

        # Enable email
        self.create_setting_row(
            section_frame,
            row,
            "Enable email notifications:",
            "email_enabled",
            widget_type="checkbox",
            tooltip="Send email notifications after allocation",
        )
        row += 1

        # SMTP server
        self.create_setting_row(
            section_frame,
            row,
            "SMTP server:",
            "smtp_server",
            widget_type="entry",
            tooltip="SMTP server address",
        )
        row += 1

        # SMTP port
        self.create_setting_row(
            section_frame,
            row,
            "SMTP port:",
            "smtp_port",
            widget_type="spinbox",
            min_value=1,
            max_value=65535,
            tooltip="SMTP server port",
        )
        row += 1

        # Email username
        self.create_setting_row(
            section_frame,
            row,
            "Username:",
            "email_username",
            widget_type="entry",
            tooltip="Email account username",
        )
        row += 1

        # Email password
        self.create_setting_row(
            section_frame,
            row,
            "Password:",
            "email_password",
            widget_type="password",
            tooltip="Email account password",
        )
        row += 1

        # Recipients
        self.create_setting_row(
            section_frame,
            row,
            "Recipients:",
            "email_recipients",
            widget_type="text",
            tooltip="Email recipients (comma-separated)",
        )

    def create_advanced_settings(self):
        """Create advanced settings section."""
        section_frame = self.create_section("Advanced Settings")
        row = 0

        # Cache enabled
        self.create_setting_row(
            section_frame,
            row,
            "Enable caching:",
            "cache_enabled",
            widget_type="checkbox",
            tooltip="Enable caching for performance",
        )
        row += 1

    def create_workflow_defaults_settings(self):
        """Create workflow defaults section for persistent file selections."""
        section_frame = self.create_section("Workflow Defaults")
        row = 0

        # Default Daily Summary Log path
        self.create_setting_row(
            section_frame,
            row,
            "Default Daily Summary Log:",
            "default_daily_summary_path",
            widget_type="file",
            tooltip="Excel file used for Daily Summary Log (prefilled on startup)",
        )
        row += 1

        # Use default on startup toggle
        self.create_setting_row(
            section_frame,
            row,
            "Use default on startup:",
            "use_default_daily_summary",
            widget_type="checkbox",
            tooltip="When enabled, Allocation tab preloads the Daily Summary Log path",
        )
        row += 1

        # Auto-open results after allocation
        self.create_setting_row(
            section_frame,
            row,
            "Auto-open results after allocation:",
            "auto_open_results",
            widget_type="checkbox",
            tooltip="When enabled, the application opens the results file automatically once allocation completes",
        )
        row += 1

        # Cache TTL
        self.create_setting_row(
            section_frame,
            row,
            "Cache TTL (seconds):",
            "cache_ttl",
            widget_type="spinbox",
            min_value=60,
            max_value=86400,
            tooltip="Cache time-to-live in seconds",
        )
        row += 1

        # Max workers
        self.create_setting_row(
            section_frame,
            row,
            "Max worker threads:",
            "max_workers",
            widget_type="spinbox",
            min_value=1,
            max_value=16,
            tooltip="Maximum number of worker threads",
        )
        row += 1

        # Batch size
        self.create_setting_row(
            section_frame,
            row,
            "Batch size:",
            "batch_size",
            widget_type="spinbox",
            min_value=10,
            max_value=1000,
            tooltip="Processing batch size",
        )
        row += 1

        # Debug mode
        self.create_setting_row(
            section_frame,
            row,
            "Debug mode:",
            "debug_mode",
            widget_type="checkbox",
            tooltip="Enable debug logging",
        )
        row += 1

        # Log level
        self.create_setting_row(
            section_frame,
            row,
            "Log level:",
            "log_level",
            widget_type="combo",
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            tooltip="Minimum log level to record",
        )

    def create_section(self, title: str) -> ctk.CTkFrame:
        """Create a settings section frame.

        Args:
            title: Section title.

        Returns:
            Section frame.
        """
        section_frame = ctk.CTkFrame(self.scrollable_frame)
        section_frame.grid(sticky="ew", pady=(0, 20))
        section_frame.grid_columnconfigure(1, weight=1)

        # Section title
        title_label = ctk.CTkLabel(
            section_frame, text=title, font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=15, pady=(10, 15))

        return section_frame

    def create_setting_row(
        self,
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        key: str,
        widget_type: str = "entry",
        **kwargs,
    ):
        """Create a setting row.

        Args:
            parent: Parent frame.
            row: Row number.
            label: Setting label.
            key: Setting key.
            widget_type: Type of widget to create.
            **kwargs: Additional widget parameters.
        """
        # Adjust row for section title
        row += 1

        # Label
        label_widget = ctk.CTkLabel(parent, text=label)
        label_widget.grid(row=row, column=0, sticky="w", padx=(30, 10), pady=8)

        # Create appropriate widget
        if widget_type == "entry":
            widget = ctk.CTkEntry(parent, placeholder_text=kwargs.get("placeholder", ""))
            widget.grid(row=row, column=1, sticky="ew", padx=10, pady=8)

        elif widget_type == "password":
            widget = ctk.CTkEntry(parent, show="*", placeholder_text=kwargs.get("placeholder", ""))
            widget.grid(row=row, column=1, sticky="ew", padx=10, pady=8)

        elif widget_type == "checkbox":
            widget = ctk.CTkCheckBox(parent, text="")
            widget.grid(row=row, column=1, sticky="w", padx=10, pady=8)

        elif widget_type == "combo":
            widget = ctk.CTkComboBox(parent, values=kwargs.get("values", []))
            widget.grid(row=row, column=1, sticky="ew", padx=10, pady=8)

        elif widget_type == "spinbox":
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.grid(row=row, column=1, sticky="w", padx=10, pady=8)

            widget = ctk.CTkEntry(frame, width=100)
            widget.grid(row=0, column=0)

            # Add up/down buttons
            up_btn = ctk.CTkButton(
                frame,
                text="▲",
                width=30,
                height=15,
                command=lambda: self.spin_value(widget, 1, kwargs),
            )
            up_btn.grid(row=0, column=1, padx=(2, 0))

            down_btn = ctk.CTkButton(
                frame,
                text="▼",
                width=30,
                height=15,
                command=lambda: self.spin_value(widget, -1, kwargs),
            )
            down_btn.grid(row=0, column=2, padx=(2, 0))

        elif widget_type == "slider":
            widget = ctk.CTkSlider(
                parent, from_=kwargs.get("min_value", 0), to=kwargs.get("max_value", 100)
            )
            widget.grid(row=row, column=1, sticky="ew", padx=10, pady=8)

            # Add value label
            value_label = ctk.CTkLabel(parent, text="0")
            value_label.grid(row=row, column=2, padx=(0, 30), pady=8)
            widget.configure(command=lambda v: value_label.configure(text=f"{v:.2f}"))

        elif widget_type == "text":
            widget = ctk.CTkTextbox(parent, height=60)
            widget.grid(row=row, column=1, sticky="ew", padx=10, pady=8)

        elif widget_type == "file" or widget_type == "path":
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            frame.grid_columnconfigure(0, weight=1)

            widget = ctk.CTkEntry(frame)
            widget.grid(row=0, column=0, sticky="ew")

            browse_btn = ctk.CTkButton(
                frame,
                text="Browse",
                width=80,
                command=lambda: self.browse_path(widget, widget_type == "file"),
            )
            browse_btn.grid(row=0, column=1, padx=(5, 0))

        else:
            widget = ctk.CTkEntry(parent)
            widget.grid(row=row, column=1, sticky="ew", padx=10, pady=8)

        # Store widget reference
        setattr(self, f"{key}_widget", widget)

        # Load current value
        self.load_setting_value(key, widget, widget_type)

        # Add change handler
        self.add_change_handler(widget, widget_type)

        # Add tooltip if provided
        if "tooltip" in kwargs:
            self.add_tooltip(label_widget, kwargs["tooltip"])

    def create_action_buttons(self):
        """Create action buttons."""
        button_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        button_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_frame.grid_columnconfigure(0, weight=1)

        # Button container
        button_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_container.grid(row=0, column=0)

        # Save button
        self.save_button = ctk.CTkButton(
            button_container, text="💾 Save Settings", width=130, command=self.save_settings_to_file
        )
        self.save_button.grid(row=0, column=0, padx=5)

        # Reset button
        self.reset_button = ctk.CTkButton(
            button_container, text="🔄 Reset to Defaults", width=140, command=self.reset_to_defaults
        )
        self.reset_button.grid(row=0, column=1, padx=5)

        # Import button
        self.import_button = ctk.CTkButton(
            button_container, text="📥 Import", width=100, command=self.import_settings
        )
        self.import_button.grid(row=0, column=2, padx=5)

        # Export button
        self.export_button = ctk.CTkButton(
            button_container, text="📤 Export", width=100, command=self.export_settings
        )
        self.export_button.grid(row=0, column=3, padx=5)

    def load_settings(self) -> dict:
        """Load settings from file.

        Returns:
            Settings dictionary.
        """
        settings_file = Path("config/settings.json")
        if settings_file.exists():
            try:
                with open(settings_file) as f:
                    file_settings = json.load(f)
                # Merge with defaults to ensure newly added keys (like company_name) exist
                defaults = self.get_default_settings()
                defaults.update(file_settings or {})
                return defaults
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")

        # Return defaults
        return self.get_default_settings()

    def get_default_settings(self) -> dict:
        """Get default settings.

        Returns:
            Default settings dictionary.
        """
        return {
            "company_name": "",
            "auto_open_results": False,
            "theme": "System",
            "language": "English",
            "auto_save": True,
            "auto_save_interval": 5,
            "default_directory": str(Path.home()),
            "max_vehicles_per_driver": 3,
            "min_vehicles_per_driver": 1,
            "priority_weight_factor": 1.5,
            "allocation_threshold": 0.8,
            "enable_optimization": True,
            "enable_validation": True,
            "use_xlwings": False,
            "excel_visible": False,
            "display_alerts": False,
            "template_path": "",
            "apply_borders": True,
            "border_style": "Thick",
            "email_enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email_username": "",
            "email_password": "",
            "email_recipients": "",
            "cache_enabled": True,
            "cache_ttl": 3600,
            "max_workers": 4,
            "batch_size": 100,
            "debug_mode": False,
            "log_level": "INFO",
            # Workflow defaults
            "default_daily_summary_path": "",
            "use_default_daily_summary": False,
        }

    def load_setting_value(self, key: str, widget: Any, widget_type: str):
        """Load setting value into widget.

        Args:
            key: Setting key.
            widget: Widget to update.
            widget_type: Type of widget.
        """
        value = self.settings.get(key, "")

        try:
            if widget_type == "checkbox":
                if value:
                    widget.select()
                else:
                    widget.deselect()
            elif widget_type == "combo":
                widget.set(value)
            elif widget_type == "slider":
                widget.set(float(value))
            elif widget_type == "text":
                widget.insert("1.0", str(value))
            else:
                if hasattr(widget, "insert"):
                    widget.insert(0, str(value))
        except Exception as e:
            logger.error(f"Error loading setting {key}: {e}")

    def add_change_handler(self, widget: Any, widget_type: str):
        """Add change handler to widget.

        Args:
            widget: Widget to monitor.
            widget_type: Type of widget.
        """

        def on_change(*args):
            self.unsaved_changes = True
            self.save_button.configure(text="💾 Save Settings*")

        # Add appropriate binding based on widget type
        if widget_type == "checkbox":
            widget.configure(command=on_change)
        elif widget_type in ["combo", "slider"]:
            widget.configure(command=on_change)
        elif widget_type == "text":
            widget.bind("<KeyRelease>", on_change)
        else:
            if hasattr(widget, "bind"):
                widget.bind("<KeyRelease>", on_change)

    def add_tooltip(self, widget: Any, text: str):
        """Add tooltip to widget.

        Args:
            widget: Widget to add tooltip to.
            text: Tooltip text.
        """
        # Simple tooltip implementation
        # In production, would use a proper tooltip library
        pass

    def spin_value(self, entry: ctk.CTkEntry, direction: int, kwargs: dict):
        """Spin numeric value up or down.

        Args:
            entry: Entry widget.
            direction: 1 for up, -1 for down.
            kwargs: Parameters including min/max values.
        """
        try:
            current = int(entry.get() or 0)
            new_value = current + direction

            min_val = kwargs.get("min_value", 0)
            max_val = kwargs.get("max_value", 100)

            new_value = max(min_val, min(new_value, max_val))

            entry.delete(0, "end")
            entry.insert(0, str(new_value))

            self.unsaved_changes = True
            self.save_button.configure(text="💾 Save Settings*")
        except ValueError:
            pass

    def browse_path(self, entry: ctk.CTkEntry, is_file: bool):
        """Browse for file or directory.

        Args:
            entry: Entry widget to update.
            is_file: True for file, False for directory.
        """
        if is_file:
            path = filedialog.askopenfilename()
        else:
            path = filedialog.askdirectory()

        if path:
            entry.delete(0, "end")
            entry.insert(0, path)
            self.unsaved_changes = True
            self.save_button.configure(text="💾 Save Settings*")

    def _collect_settings_from_widgets(self):
        """Collect setting values from created widgets into self.settings.

        Uses attributes named "<key>_widget" created by create_setting_row.
        Casts values to the type of the existing setting value when possible.
        """
        # Only collect for known keys. Include defaults to allow newly added fields
        allowed_keys = (
            set(self.settings.keys())
            | set(self.get_default_settings().keys())
            | {"default_daily_summary_path", "use_default_daily_summary"}
        )
        for attr in dir(self):
            if not attr.endswith("_widget"):
                continue
            key = attr[:-7]
            if key not in allowed_keys:
                continue
            widget = getattr(self, attr)
            # Determine raw value by widget capabilities
            raw = None
            try:
                if hasattr(widget, "get"):
                    raw = widget.get()
                elif hasattr(widget, "get"):
                    raw = widget.get()
            except Exception:
                raw = None

            # Fallbacks for specific widget classes
            try:
                import customtkinter as _ctk

                if isinstance(widget, _ctk.CTkCheckBox):
                    # get() returns 0/1; cast to bool
                    raw = bool(widget.get())
                elif isinstance(widget, _ctk.CTkSlider):
                    raw = float(widget.get())
                elif isinstance(widget, _ctk.CTkTextbox):
                    raw = widget.get("1.0", "end").strip()
                elif isinstance(widget, _ctk.CTkEntry):
                    raw = widget.get()
                elif isinstance(widget, _ctk.CTkComboBox):
                    raw = widget.get()
            except Exception:
                pass

            if raw is None:
                continue

            # Cast to existing type if present
            current = self.settings.get(key)
            try:
                if isinstance(current, bool):
                    value = (
                        bool(raw)
                        if not isinstance(raw, str)
                        else raw.lower() in ("1", "true", "yes", "on")
                    )
                elif isinstance(current, int):
                    value = int(float(raw))
                elif isinstance(current, float):
                    value = float(raw)
                else:
                    value = str(raw)
            except Exception:
                value = raw

            self.settings[key] = value

    def save_settings_to_file(self):
        """Save settings to file."""
        # Collect all settings from UI widgets
        self._collect_settings_from_widgets()

        # Validate workflow defaults conservatively
        try:
            path = self.settings.get("default_daily_summary_path", "")
            if path:
                p = Path(path)
                if not p.exists():
                    if not messagebox.askyesno(
                        "Path Not Found",
                        "The configured Default Daily Summary Log path does not exist.\n"
                        "Do you want to save it anyway?",
                    ):
                        return  # Abort save
        except Exception:
            pass

        # Save to file
        settings_file = Path("config/settings.json")
        settings_file.parent.mkdir(exist_ok=True)

        try:
            with open(settings_file, "w") as f:
                json.dump(self.settings, f, indent=2)

            self.unsaved_changes = False
            self.save_button.configure(text="💾 Save Settings")

            messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
            logger.info(
                "Settings saved | company_name=%s | auto_open_results=%s",
                self.settings.get("company_name", ""),
                self.settings.get("auto_open_results", False),
            )

            # Notify listener for live updates (e.g., main window title refresh)
            try:
                if self.on_settings_saved:
                    self.on_settings_saved(self.settings)
            except Exception as cb_e:
                logger.debug(f"on_settings_saved callback failed: {cb_e}")

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            messagebox.showerror("Save Error", f"Failed to save settings: {e}")

    def reset_to_defaults(self):
        """Reset settings to defaults."""
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?"):
            self.settings = self.get_default_settings()
            # Reload all widgets
            # This would update all setting widgets with default values
            logger.info("Settings reset to defaults")

    def import_settings(self):
        """Import settings from file."""
        filename = filedialog.askopenfilename(
            title="Import Settings", filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename) as f:
                    self.settings = json.load(f)
                # Reload all widgets
                logger.info(f"Settings imported from: {filename}")
                messagebox.showinfo("Import Complete", "Settings imported successfully.")
            except Exception as e:
                logger.error(f"Failed to import settings: {e}")
                messagebox.showerror("Import Error", f"Failed to import settings: {e}")

    def export_settings(self):
        """Export settings to file."""
        filename = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if filename:
            try:
                with open(filename, "w") as f:
                    json.dump(self.settings, f, indent=2)
                logger.info(f"Settings exported to: {filename}")
                messagebox.showinfo("Export Complete", "Settings exported successfully.")
            except Exception as e:
                logger.error(f"Failed to export settings: {e}")
                messagebox.showerror("Export Error", f"Failed to export settings: {e}")
