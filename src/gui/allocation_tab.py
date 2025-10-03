"""Allocation tab for Resource Allocation GUI."""

import json
import threading
from datetime import date, datetime
from pathlib import Path
from tkinter import StringVar, filedialog, messagebox

import customtkinter as ctk
from loguru import logger

from src.core.gas_compatible_allocator import GASCompatibleAllocator
from src.gui.widgets import RecentFileSelector
from src.utils.recent_files_manager import FileFieldType


class AllocationTab:
    """Allocation tab implementation."""

    def __init__(self, parent, allocation_engine, excel_service, border_service):
        """Initialize allocation tab.

        Args:
            parent: Parent widget.
            allocation_engine: Reference to allocation engine.
            excel_service: Reference to Excel service.
            border_service: Reference to border formatting service.
        """
        self.parent = parent
        self.allocation_engine = allocation_engine
        self.excel_service = excel_service
        self.border_service = border_service

        # File paths for GAS-compatible allocation
        self.day_of_ops_path = StringVar()
        self.daily_routes_path = StringVar()
        self.daily_summary_path = StringVar()  # This will also be the output file
        self.allocation_date = StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.current_result = None

        # Configure grid
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_rowconfigure(2, weight=1)

        # Create UI elements
        self.setup_ui()

    def setup_ui(self):
        """Setup allocation tab UI."""
        # Header
        header_label = ctk.CTkLabel(
            self.parent, text="Run Vehicle Allocation", font=ctk.CTkFont(size=24, weight="bold")
        )
        header_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 10))

        # File Selection Section
        self.create_file_selection_section()

        # Configuration Section
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
            font=ctk.CTkFont(size=16, weight="bold"),
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
            text="ℹ️ Daily Summary Log provides Vehicle Status input and receives allocation results (Daily Details, Results, Unassigned sheets)",
            font=ctk.CTkFont(size=12),
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
        # Left config frame
        left_config_frame = ctk.CTkFrame(self.parent)
        left_config_frame.grid(row=2, column=0, sticky="nsew", padx=(20, 10), pady=10)
        left_config_frame.grid_columnconfigure(1, weight=1)

        left_title = ctk.CTkLabel(
            left_config_frame, text="Allocation Settings", font=ctk.CTkFont(size=16, weight="bold")
        )
        left_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 5))

        # Allocation date
        date_label = ctk.CTkLabel(left_config_frame, text="Allocation Date:")
        date_label.grid(row=1, column=0, sticky="w", padx=15, pady=10)

        self.date_entry = ctk.CTkEntry(left_config_frame, textvariable=self.allocation_date)
        self.date_entry.grid(row=1, column=1, sticky="ew", padx=(10, 15), pady=10)

        # Max vehicles per driver
        max_vehicles_label = ctk.CTkLabel(left_config_frame, text="Max Vehicles/Driver:")
        max_vehicles_label.grid(row=2, column=0, sticky="w", padx=15, pady=10)

        self.max_vehicles_slider = ctk.CTkSlider(
            left_config_frame, from_=1, to=10, number_of_steps=9
        )
        self.max_vehicles_slider.set(3)
        self.max_vehicles_slider.grid(row=2, column=1, sticky="ew", padx=(10, 15), pady=10)

        self.max_vehicles_value = ctk.CTkLabel(left_config_frame, text="3")
        self.max_vehicles_value.grid(row=2, column=2, padx=(0, 15), pady=10)

        self.max_vehicles_slider.configure(
            command=lambda v: self.max_vehicles_value.configure(text=str(int(v)))
        )

        # Min vehicles per driver
        min_vehicles_label = ctk.CTkLabel(left_config_frame, text="Min Vehicles/Driver:")
        min_vehicles_label.grid(row=3, column=0, sticky="w", padx=15, pady=10)

        self.min_vehicles_slider = ctk.CTkSlider(
            left_config_frame, from_=0, to=5, number_of_steps=5
        )
        self.min_vehicles_slider.set(1)
        self.min_vehicles_slider.grid(row=3, column=1, sticky="ew", padx=(10, 15), pady=10)

        self.min_vehicles_value = ctk.CTkLabel(left_config_frame, text="1")
        self.min_vehicles_value.grid(row=3, column=2, padx=(0, 15), pady=10)

        self.min_vehicles_slider.configure(
            command=lambda v: self.min_vehicles_value.configure(text=str(int(v)))
        )

        # Priority weight
        priority_label = ctk.CTkLabel(left_config_frame, text="Priority Weight:")
        priority_label.grid(row=4, column=0, sticky="w", padx=15, pady=10)

        self.priority_slider = ctk.CTkSlider(left_config_frame, from_=1.0, to=3.0)
        self.priority_slider.set(1.5)
        self.priority_slider.grid(row=4, column=1, sticky="ew", padx=(10, 15), pady=10)

        self.priority_value = ctk.CTkLabel(left_config_frame, text="1.5")
        self.priority_value.grid(row=4, column=2, padx=(0, 15), pady=10)

        self.priority_slider.configure(
            command=lambda v: self.priority_value.configure(text=f"{v:.1f}")
        )

        # Right config frame (Options)
        right_config_frame = ctk.CTkFrame(self.parent)
        right_config_frame.grid(row=2, column=1, sticky="nsew", padx=(10, 20), pady=10)

        right_title = ctk.CTkLabel(
            right_config_frame, text="Options", font=ctk.CTkFont(size=16, weight="bold")
        )
        right_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        # Checkboxes
        self.optimize_checkbox = ctk.CTkCheckBox(
            right_config_frame, text="Optimize allocation before processing"
        )
        self.optimize_checkbox.grid(row=1, column=0, sticky="w", padx=15, pady=10)
        self.optimize_checkbox.select()

        self.validate_checkbox = ctk.CTkCheckBox(
            right_config_frame, text="Validate results after allocation"
        )
        self.validate_checkbox.grid(row=2, column=0, sticky="w", padx=15, pady=10)
        self.validate_checkbox.select()

        self.borders_checkbox = ctk.CTkCheckBox(
            right_config_frame, text="Apply daily section borders"
        )
        self.borders_checkbox.grid(row=3, column=0, sticky="w", padx=15, pady=10)
        self.borders_checkbox.select()

        self.email_checkbox = ctk.CTkCheckBox(right_config_frame, text="Send email notification")
        self.email_checkbox.grid(row=4, column=0, sticky="w", padx=15, pady=10)

        self.open_after_checkbox = ctk.CTkCheckBox(
            right_config_frame, text="Open Daily Summary Log after completion"
        )
        self.open_after_checkbox.grid(row=5, column=0, sticky="w", padx=15, pady=10)
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
            results_frame, text="Allocation Results", font=ctk.CTkFont(size=16, weight="bold")
        )
        results_title.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        # Results text area
        self.results_text = ctk.CTkTextbox(
            results_frame, corner_radius=5, font=ctk.CTkFont(family="Courier", size=12)
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
            font=ctk.CTkFont(size=14, weight="bold"),
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
        )
        self.export_button.grid(row=0, column=2, padx=5)

        # Open results file button
        self.open_results_button = ctk.CTkButton(
            button_container,
            text="📂 Open Results File",
            width=140,
            height=40,
            state="disabled",
            command=self.open_results_file,
        )
        self.open_results_button.grid(row=0, column=3, padx=5)

        # Create sample data button
        self.sample_button = ctk.CTkButton(
            button_container,
            text="📝 Create Sample",
            width=130,
            height=40,
            command=self.create_sample_data,
        )
        self.sample_button.grid(row=0, column=3, padx=5)

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
        # Validate inputs
        if not self.day_of_ops_path.get():
            self.show_error("Please select Day of Ops file")
            return

        if not self.daily_routes_path.get():
            self.show_error("Please select Daily Routes file")
            return

        if not self.daily_summary_path.get():
            self.show_error("Please select Daily Summary Log file")
            return

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
        try:
            self.update_results("Starting GAS-compatible allocation process...\n")
            self.update_progress(0.1)

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

            # Open file if requested
            if self.open_after_checkbox.get():
                summary_path = self.daily_summary_path.get()
                self.update_results(f"\n📂 Opening Daily Summary Log: {summary_path}\n")
                self._open_daily_summary_log_async(summary_path)

        except Exception as e:
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
        text += f"  • Allocation Rate: {(assigned_routes/total_routes*100 if total_routes > 0 else 0):.1f}%\n"

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

    def update_progress(self, value: float):
        """Update progress bar."""
        self.progress_bar.set(value)

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
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#ff6b35", "#ff8c42"),
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=15)

        # Summary
        duplicate_count = len([w for w in warnings if "assigned to multiple" in w.lower()])
        summary_text = f"Found {duplicate_count} vehicles assigned to multiple routes. These have been marked in the Excel output."

        summary_label = ctk.CTkLabel(
            header_frame, text=summary_text, font=ctk.CTkFont(size=14), wraplength=750
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
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        details_title.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # Scrollable text area for details
        details_text = ctk.CTkTextbox(
            details_frame, font=ctk.CTkFont(family="Courier", size=12), wrap="word"
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
            font=ctk.CTkFont(size=14, weight="bold"),
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
                font=ctk.CTkFont(size=14),
                command=lambda: self._open_excel_file(self.daily_summary_path.get()),
            )
            view_btn.grid(row=0, column=1, padx=5, pady=5)

        # Help button
        help_btn = ctk.CTkButton(
            button_frame,
            text="❓ Help",
            width=80,
            height=35,
            font=ctk.CTkFont(size=14),
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
                    content += f"{route_info['route']:12s} | {route_info['van']:7s} | {route_info['driver']:20s} | {route_info['service']}\n"

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
