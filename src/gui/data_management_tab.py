"""Data management tab for Resource Allocation GUI."""

import threading
import tkinter as tk
from contextlib import suppress
from pathlib import Path
from tkinter import StringVar, filedialog, messagebox, ttk

import customtkinter as ctk
import pandas as pd
from loguru import logger


class DataManagementTab:
    """Data management tab implementation."""

    def __init__(self, parent, excel_service, data_service=None):
        """Initialize data management tab.

        Args:
            parent: Parent widget.
            excel_service: Reference to Excel service.
        """
        self.parent = parent
        self.excel_service = excel_service
        self.data_service = data_service

        self.current_data = {"vehicles": None, "drivers": None}
        self.current_file = None
        self._daily_summary_path_getter = None
        self.source_var = StringVar(value="Daily Summary (Vehicle Status)")

        # Configure grid
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)

        # Create UI elements
        self.setup_ui()

    def setup_ui(self):
        """Setup data management UI."""
        # Header with file controls
        self.create_header()

        # Create notebook for vehicles and drivers
        self.notebook = ctk.CTkTabview(self.parent)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Add tabs
        self.notebook.add("Vehicles")
        self.notebook.add("Drivers")

        # Create data tables
        self.create_vehicles_tab()
        self.create_drivers_tab()

        # Action buttons
        self.create_action_buttons()

    def create_header(self):
        """Create header with file controls."""
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            header_frame, text="Data Management", font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        # File controls
        file_controls = ctk.CTkFrame(header_frame, fg_color="transparent")
        file_controls.grid(row=0, column=1, sticky="e")

        # Source selector
        source_label = ctk.CTkLabel(file_controls, text="Source:")
        source_label.grid(row=0, column=0, padx=(0, 5))

        self.source_menu = ctk.CTkOptionMenu(
            file_controls,
            variable=self.source_var,
            values=[
                "Fleet Inventory (VehiclesData.xlsx)",
                "Daily Summary (Vehicle Status)",
                "Associate Data (Drivers)",
                "Custom Workbook (Vehicles)",
            ],
        )
        self.source_menu.grid(row=0, column=1, padx=(0, 10))

        self.load_button = ctk.CTkButton(
            file_controls, text="📂 Load Data", width=120, command=self.load_data
        )
        self.load_button.grid(row=0, column=2, padx=5)

        self.save_button = ctk.CTkButton(
            file_controls, text="💾 Save Data", width=120, state="disabled", command=self.save_data
        )
        self.save_button.grid(row=0, column=3, padx=5)

        self.new_button = ctk.CTkButton(
            file_controls, text="➕ New Dataset", width=120, command=self.new_dataset
        )
        self.new_button.grid(row=0, column=4, padx=5)

    def create_vehicles_tab(self):
        """Create vehicles data table."""
        vehicles_tab = self.notebook.tab("Vehicles")
        vehicles_tab.grid_columnconfigure(0, weight=1)
        vehicles_tab.grid_rowconfigure(1, weight=1)

        # Toolbar
        toolbar = self.create_toolbar(vehicles_tab, "vehicle")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Create treeview with scrollbars
        tree_frame = ctk.CTkFrame(vehicles_tab)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Treeview - support multiple column configurations
        columns = ("ID", "Vehicle Number", "Type", "Location", "Status", "Priority", "Capacity")
        self.vehicles_columns_base = columns
        self.vehicles_columns_enriched = (
            "ID",
            "Vehicle Number",
            "Type",
            "Location",
            "Status",
            "Priority",
            "Capacity",
            "VIN",
            "GeoTab",
            "Brand/Rental",
        )
        # Full fleet inventory columns for VehiclesData.xlsx
        self.vehicles_columns_fleet = (
            "ID",
            "Vehicle Name",
            "VIN",
            "Service Type",
            "Status",
            "Ownership",
            "Make",
            "Model",
            "Year",
            "License Plate",
            "Reg. Expiry",
            "Station",
        )
        self._vehicle_enriched = False
        self._vehicle_mode = "base"  # base, enriched, or fleet
        self.vehicles_tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings", selectmode="extended"
        )
        self.vehicles_tree.grid(row=0, column=0, sticky="nsew")

        self._configure_vehicle_columns(enriched=False)

        # Scrollbars
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.vehicles_tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        # Wrap yscroll/xscroll to update overlays
        def _yset(*args):
            v_scrollbar.set(*args)
            self._update_vehicle_status_overlays()

        self.vehicles_tree.configure(yscrollcommand=_yset)

        h_scrollbar = ttk.Scrollbar(
            tree_frame, orient="horizontal", command=self.vehicles_tree.xview
        )
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        def _xset(*args):
            h_scrollbar.set(*args)
            self._update_vehicle_status_overlays()

        self.vehicles_tree.configure(xscrollcommand=_xset)

        # Statistics panel
        self.create_statistics_panel(vehicles_tab, "vehicles")

        # Configure helper tag for search hiding
        with suppress(Exception):
            self.vehicles_tree.tag_configure("hidden", foreground="gray")

        # Prepare per-cell overlay labels for Status column coloring
        self._veh_status_labels: dict[str, tk.Label] = {}
        # Keep overlays in sync on resize/config
        self.vehicles_tree.bind(
            "<Configure>", lambda _event: self._update_vehicle_status_overlays()
        )
        self.vehicles_tree.bind(
            "<<TreeviewSelect>>", lambda _event: self._update_vehicle_status_overlays()
        )

    def create_drivers_tab(self):
        """Create drivers data table."""
        drivers_tab = self.notebook.tab("Drivers")
        drivers_tab.grid_columnconfigure(0, weight=1)
        drivers_tab.grid_rowconfigure(1, weight=1)

        # Toolbar
        toolbar = self.create_toolbar(drivers_tab, "driver")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Create treeview with scrollbars
        tree_frame = ctk.CTkFrame(drivers_tab)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Treeview with extended columns for associate data
        columns = (
            "ID",
            "TransporterID",
            "Name",
            "Position",
            "Qualifications",
            "ID Expiration",
            "Personal Phone",
            "Work Phone",
            "Email",
            "Status",
        )
        self.drivers_tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings", selectmode="extended"
        )
        self.drivers_tree.grid(row=0, column=0, sticky="nsew")

        # Configure columns
        self.drivers_tree.heading("#0", text="")
        self.drivers_tree.heading("ID", text="ID")
        self.drivers_tree.heading("TransporterID", text="TransporterID")
        self.drivers_tree.heading("Name", text="Name")
        self.drivers_tree.heading("Position", text="Position")
        self.drivers_tree.heading("Qualifications", text="Qualifications")
        self.drivers_tree.heading("ID Expiration", text="ID Expiration")
        self.drivers_tree.heading("Personal Phone", text="Personal Phone")
        self.drivers_tree.heading("Work Phone", text="Work Phone")
        self.drivers_tree.heading("Email", text="Email")
        self.drivers_tree.heading("Status", text="Status")

        # Column widths optimized for associate data
        self.drivers_tree.column("#0", width=0, stretch=False)
        self.drivers_tree.column("ID", width=50)
        self.drivers_tree.column("TransporterID", width=130)
        self.drivers_tree.column("Name", width=180)
        self.drivers_tree.column("Position", width=100)
        self.drivers_tree.column("Qualifications", width=250)
        self.drivers_tree.column("ID Expiration", width=100)
        self.drivers_tree.column("Personal Phone", width=120)
        self.drivers_tree.column("Work Phone", width=120)
        self.drivers_tree.column("Email", width=180)
        self.drivers_tree.column("Status", width=80)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.drivers_tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.drivers_tree.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(
            tree_frame, orient="horizontal", command=self.drivers_tree.xview
        )
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.drivers_tree.configure(xscrollcommand=h_scrollbar.set)

        # Statistics panel
        self.create_statistics_panel(drivers_tab, "drivers")

    def create_toolbar(self, parent, data_type: str):
        """Create toolbar for data operations.

        Args:
            parent: Parent widget.
            data_type: Type of data (vehicle or driver).

        Returns:
            Toolbar frame.
        """
        toolbar = ctk.CTkFrame(parent, height=40, fg_color="transparent")

        # Add button
        add_button = ctk.CTkButton(
            toolbar,
            text=f"➕ Add {data_type.title()}",
            width=120,
            command=lambda: self.add_item(data_type),
        )
        add_button.grid(row=0, column=0, padx=5)

        # Edit button
        edit_button = ctk.CTkButton(
            toolbar, text="✏️ Edit", width=80, command=lambda: self.edit_item(data_type)
        )
        edit_button.grid(row=0, column=1, padx=5)

        # Delete button
        delete_button = ctk.CTkButton(
            toolbar, text="🗑️ Delete", width=80, command=lambda: self.delete_item(data_type)
        )
        delete_button.grid(row=0, column=2, padx=5)

        # Details button (vehicles only)
        if data_type == "vehicle":
            details_button = ctk.CTkButton(
                toolbar, text="ℹ️ Details", width=90, command=self.show_vehicle_details
            )
            details_button.grid(row=0, column=3, padx=(10, 5))

        # Search entry
        search_label = ctk.CTkLabel(toolbar, text="Search:")
        search_label.grid(row=0, column=4, padx=(20, 5))

        search_entry = ctk.CTkEntry(toolbar, width=200, placeholder_text=f"Search {data_type}s...")
        search_entry.grid(row=0, column=5, padx=5)
        search_entry.bind(
            "<KeyRelease>",
            lambda _event: self.search_items(data_type, search_entry.get()),
        )

        # Import/Export buttons
        import_button = ctk.CTkButton(
            toolbar, text="📥 Import", width=80, command=lambda: self.import_data(data_type)
        )
        import_button.grid(row=0, column=6, padx=(20, 5))

        export_button = ctk.CTkButton(
            toolbar, text="📤 Export", width=80, command=lambda: self.export_data(data_type)
        )
        export_button.grid(row=0, column=7, padx=5)

        # Qualification filter for drivers only
        if data_type == "driver":
            filter_label = ctk.CTkLabel(toolbar, text="Filter:")
            filter_label.grid(row=0, column=8, padx=(20, 5))

            self.qual_filter = ctk.CTkComboBox(
                toolbar,
                values=["All", "Step Van", "EDV", "CDV", "DOT", "Helper Only"],
                width=120,
                command=lambda val: self.filter_by_qualification(val),
            )
            self.qual_filter.set("All")
            self.qual_filter.grid(row=0, column=9, padx=5)

        return toolbar

    def create_statistics_panel(self, parent, data_type: str):
        """Create statistics panel.

        Args:
            parent: Parent widget.
            data_type: Type of data (vehicles or drivers).
        """
        stats_frame = ctk.CTkFrame(parent)
        stats_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))

        # Statistics labels
        if data_type == "vehicles":
            self.vehicles_stats_label = ctk.CTkLabel(
                stats_frame,
                text="Total: 0 | Available: 0 | In Use: 0 | Maintenance: 0",
                font=ctk.CTkFont(size=12),
            )
            self.vehicles_stats_label.grid(row=0, column=0, padx=10, pady=5)
        else:
            self.drivers_stats_label = ctk.CTkLabel(
                stats_frame,
                text="Total: 0 | Active: 0 | Inactive: 0 | Average Experience: 0 years",
                font=ctk.CTkFont(size=12),
            )
            self.drivers_stats_label.grid(row=0, column=0, padx=10, pady=5)

    def create_action_buttons(self):
        """Create action buttons at bottom."""
        button_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_frame.grid_columnconfigure(0, weight=1)

        # Button container
        button_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_container.grid(row=0, column=0)

        # Refresh button
        refresh_button = ctk.CTkButton(
            button_container, text="🔄 Refresh", width=100, command=self.refresh_data
        )
        refresh_button.grid(row=0, column=0, padx=5)

        # Validate button
        validate_button = ctk.CTkButton(
            button_container, text="✓ Validate", width=100, command=self.validate_data
        )
        validate_button.grid(row=0, column=1, padx=5)

        # Generate sample button
        sample_button = ctk.CTkButton(
            button_container, text="📝 Generate Sample", width=130, command=self.generate_sample_data
        )
        sample_button.grid(row=0, column=2, padx=5)

    def load_data(self):
        """Load data from Excel file or CSV."""
        selected_source = self.source_var.get()

        # Handle Fleet Inventory loading (VehiclesData.xlsx)
        if selected_source.startswith("Fleet Inventory"):

            def load_fleet_inventory():
                try:
                    if not self.data_service:
                        raise ValueError("Data service not available")

                    # Resolve path or prompt
                    fleet_path = Path("bway_files") / "VehiclesData.xlsx"
                    if not fleet_path.exists():
                        # Try inputs folder
                        fleet_path = Path("inputs") / "VehiclesData.xlsx"
                    if not fleet_path.exists():
                        # Prompt user
                        selected_path = filedialog.askopenfilename(
                            title="Select VehiclesData.xlsx",
                            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
                        )
                        if not selected_path:
                            return
                        fleet_path = Path(selected_path)

                    df = self.data_service.load_vehicles_data(str(fleet_path))
                    if df is None or df.empty:
                        raise ValueError("Fleet inventory data not found or empty")

                    self.populate_vehicles_tree(df)

                    # Clear drivers when loading fleet inventory
                    self.drivers_tree.delete(*self.drivers_tree.get_children())

                    self.current_file = str(fleet_path)
                    self.save_button.configure(state="normal")
                    logger.info(f"Loaded {len(df)} vehicles from fleet inventory: {fleet_path}")

                except Exception as e:
                    logger.error(f"Failed to load fleet inventory: {e}")
                    messagebox.showerror("Load Error", str(e))

            threading.Thread(target=load_fleet_inventory, daemon=True).start()
            return

        # Handle Associate Data loading
        if selected_source.startswith("Associate Data"):

            def load_associates():
                try:
                    if not self.data_service:
                        raise ValueError("Data service not available")

                    # Resolve path or prompt
                    assoc_path = Path("bway_files") / "AssociateData.csv"
                    if not assoc_path.exists():
                        # Try inputs folder
                        assoc_path = Path("inputs") / "AssociateData.csv"
                    if not assoc_path.exists():
                        # Prompt user
                        selected_path = filedialog.askopenfilename(
                            title="Select AssociateData.csv",
                            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                        )
                        if not selected_path:
                            return
                        assoc_path = Path(selected_path)

                    df = self.data_service.load_associate_data(str(assoc_path))
                    if df is None or df.empty:
                        raise ValueError("Associate data not found or empty")

                    self.populate_drivers_tree(df)

                    # Clear vehicles when loading associates
                    self.vehicles_tree.delete(*self.vehicles_tree.get_children())

                    self.current_file = str(assoc_path)
                    self.save_button.configure(state="normal")
                    logger.info(f"Loaded {len(df)} associates from {assoc_path}")

                except Exception as e:
                    logger.error(f"Failed to load associate data: {e}")
                    messagebox.showerror("Load Error", str(e))

            threading.Thread(target=load_associates, daemon=True).start()
            return

        if selected_source.startswith("Daily Summary"):
            # Resolve Daily Summary path
            ds_path = self._resolve_daily_summary_path()
            if not ds_path:
                # Prompt for file and remember selection via settings if desired
                ds_path = filedialog.askopenfilename(
                    title="Select Daily Summary Log",
                    filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
                )
                if not ds_path:
                    return

            def load_thread():
                try:
                    if not self.data_service:
                        raise ValueError("Data service not available")
                    vs_df = self.data_service.load_vehicle_status(ds_path)
                    if vs_df is None or vs_df.empty:
                        raise ValueError("Vehicle Status sheet not found or empty")
                    # Populate vehicles from Vehicle Status (mapping happens in populate_vehicles_tree)
                    self.populate_vehicles_tree(vs_df)

                    # Load optional Vehicle Log for enrichment
                    self._vehicle_details = {}
                    try:
                        vl_df = self.data_service.load_vehicle_log(ds_path)
                        if vl_df is not None and not vl_df.empty:
                            colmap = {c.lower().strip(): c for c in vl_df.columns}
                            van_col = colmap.get("van id")
                            vin_col = colmap.get("vin")
                            geo_col = colmap.get("geotab") or colmap.get("geotab code")
                            brand_col = colmap.get("branded or rental")
                            for _, r in vl_df.iterrows():
                                vid = str(r.get(van_col, "") or "").strip() if van_col else ""
                                if not vid:
                                    continue
                                self._vehicle_details[vid] = {
                                    "VIN": str(r.get(vin_col, "") or "").strip() if vin_col else "",
                                    "GeoTab": str(r.get(geo_col, "") or "").strip()
                                    if geo_col
                                    else "",
                                    "Branded/Rental": str(r.get(brand_col, "") or "").strip()
                                    if brand_col
                                    else "",
                                }
                    except Exception as e:
                        logger.debug(f"Vehicle Log enrichment skipped: {e}")

                    # Drivers table is not sourced from Daily Summary in this phase; clear it
                    self.drivers_tree.delete(*self.drivers_tree.get_children())

                    self.current_file = ds_path
                    self.save_button.configure(state="normal")
                    logger.info(f"Loaded Vehicles from Daily Summary: {ds_path}")
                except Exception as e:
                    logger.error(f"Failed to load Daily Summary: {e}")
                    messagebox.showerror("Load Error", str(e))

            t = threading.Thread(target=load_thread, daemon=True)
            t.start()
            return

        # Legacy: custom workbook path with Vehicles/Drivers sheets
        filename = filedialog.askopenfilename(
            title="Load Data File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if not filename:
            return

        def load_legacy():
            try:
                self.excel_service.open_workbook(filename)
                vehicles_df = self.excel_service.read_data("Vehicles", as_dataframe=True)
                self.populate_vehicles_tree(vehicles_df)
                drivers_df = self.excel_service.read_data("Drivers", as_dataframe=True)
                self.populate_drivers_tree(drivers_df)
                self.current_file = filename
                self.save_button.configure(state="normal")
                logger.info(f"Data loaded from: {filename}")
            except Exception as e:
                logger.error(f"Failed to load data: {e}")
                messagebox.showerror("Load Error", str(e))

        threading.Thread(target=load_legacy, daemon=True).start()

    def set_daily_summary_path_getter(self, getter):
        """Wire a callable that returns the selected Daily Summary path."""
        self._daily_summary_path_getter = getter

    def _resolve_daily_summary_path(self) -> str | None:
        try:
            if self._daily_summary_path_getter:
                p = self._daily_summary_path_getter()
                if p:
                    return p
        except Exception:
            pass
        if self.data_service:
            return self.data_service.resolve_daily_summary_path(None)
        return None

    def save_data(self):
        """Save data to Excel file."""
        try:
            # Build export DataFrames from current grid state (read-only safe export)
            vehicles_df = self._build_vehicles_export_df()
            drivers_df = self._build_drivers_export_df()

            # Ensure outputs directory
            from pathlib import Path

            outputs_dir = Path("outputs")
            outputs_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = outputs_dir / f"vehicles_export_{ts}.xlsx"

            with pd.ExcelWriter(export_path, engine="openpyxl") as writer:
                if vehicles_df is not None:
                    vehicles_df.to_excel(writer, sheet_name="Vehicles", index=False)
                if drivers_df is not None and not drivers_df.empty:
                    drivers_df.to_excel(writer, sheet_name="Drivers", index=False)

            messagebox.showinfo("Save Complete", f"Exported to {export_path}")
            logger.info(f"Safe export created at: {export_path}")
        except Exception as e:
            logger.error(f"Save export failed: {e}")
            messagebox.showerror("Save Error", str(e))

    def new_dataset(self):
        """Create new dataset."""
        # Clear current data
        self.vehicles_tree.delete(*self.vehicles_tree.get_children())
        self.drivers_tree.delete(*self.drivers_tree.get_children())
        self.current_file = None
        self.save_button.configure(state="disabled")

        logger.info("New dataset created")

    def populate_vehicles_tree(self, df: pd.DataFrame):
        """Populate vehicles treeview with data.

        Accepts DataFrames from:
        - VehiclesData.xlsx (fleet inventory with 28 columns)
        - Daily Summary Vehicle Status (operational snapshot)
        - Legacy Vehicles sheet

        Maps columns accordingly based on detected format.
        """
        # Clear existing data
        self.vehicles_tree.delete(*self.vehicles_tree.get_children())

        # Normalize source columns
        cols_map = {c.lower().strip(): c for c in df.columns}
        is_vehicles_data = "vin" in cols_map and "vehiclename" in cols_map
        is_vehicle_status = ("van id" in cols_map) or ("vehicle id" in cols_map)

        rows = []
        if is_vehicles_data:
            # VehiclesData.xlsx format - comprehensive fleet inventory
            for _, row in df.iterrows():
                # Map operational status to availability
                op_status = str(row.get("operationalStatus", "")).upper()
                status = "available" if op_status == "OPERATIONAL" else "unavailable"

                # Format registration expiry date
                reg_expiry = row.get("registrationExpiryDate", "")
                if pd.notna(reg_expiry):
                    try:
                        reg_expiry = pd.to_datetime(reg_expiry).strftime("%m/%d/%Y")
                    except Exception:
                        reg_expiry = str(reg_expiry)
                else:
                    reg_expiry = ""

                rows.append(
                    (
                        str(row.get("vehicleName", "")).strip(),
                        str(row.get("vin", "")).strip(),
                        str(row.get("serviceType", "")).strip(),
                        status,
                        str(row.get("ownershipType", "")).strip(),
                        str(row.get("make", "")).strip(),
                        str(row.get("model", "")).strip(),
                        str(row.get("year", "")).strip(),
                        str(row.get("licensePlateNumber", "")).strip(),
                        reg_expiry,
                        str(row.get("stationCode", "")).strip(),
                    )
                )
        elif is_vehicle_status:
            van_col = cols_map.get("van id") or cols_map.get("vehicle id")
            type_col = cols_map.get("type") or cols_map.get("vehicle type")
            op_col = cols_map.get("opnal? y/n") or cols_map.get("operational")
            for _, row in df.iterrows():
                veh_num = str(row.get(van_col, "") or "").strip()
                vtype = str(row.get(type_col, "") or "").strip()
                opval = str(row.get(op_col, "") or "").strip().upper() if op_col else ""
                status = "available" if opval == "Y" else "unavailable" if opval else ""
                rows.append((veh_num, vtype, "", status, "", ""))
        else:
            # Legacy Vehicles sheet
            for _, row in df.iterrows():
                rows.append(
                    (
                        str(row.get("Vehicle Number", "") or "").strip(),
                        str(row.get("Type", "") or "").strip(),
                        str(row.get("Location", "") or "").strip(),
                        str(row.get("Status", "") or "").strip(),
                        row.get("Priority", ""),
                        row.get("Capacity", ""),
                    )
                )

        # Persist current dataset for validation/export
        self.current_data["vehicles"] = df.copy()

        # Configure columns based on data source
        if is_vehicles_data:
            # Fleet inventory mode with comprehensive columns
            self._configure_vehicle_columns(mode="fleet")

            # Insert fleet data rows
            for idx, row_data in enumerate(rows, start=1):
                vals = (idx,) + row_data
                # Color-code by operational status
                status = row_data[3]  # Status column
                tag = "operational" if status == "available" else "grounded"
                self.vehicles_tree.insert("", "end", values=vals, tags=(tag,))

            # Configure status tags with colors
            self.vehicles_tree.tag_configure("operational", foreground="#34d058")
            self.vehicles_tree.tag_configure("grounded", foreground="#ff6b6b")

        else:
            # Legacy enrichment-aware column setup for Daily Summary / legacy formats
            has_enrichment = hasattr(self, "_vehicle_details") and bool(self._vehicle_details)
            if has_enrichment and self._vehicle_mode != "enriched":
                self._configure_vehicle_columns(mode="enriched")
            elif not has_enrichment and self._vehicle_mode != "base":
                self._configure_vehicle_columns(mode="base")

            for idx, (veh, vtype, loc, status, prio, cap) in enumerate(rows, start=1):
                if self._vehicle_mode == "enriched":
                    det = (
                        self._vehicle_details.get(str(veh), {})
                        if hasattr(self, "_vehicle_details")
                        else {}
                    )
                    vin = det.get("VIN", "")
                    geo = det.get("GeoTab", "")
                    brand = det.get("Branded/Rental", "")
                    vals = (idx, veh, vtype, loc, status, prio, cap, vin, geo, brand)
                else:
                    vals = (idx, veh, vtype, loc, status, prio, cap)
                self.vehicles_tree.insert("", "end", values=vals)

        # After inserting, refresh overlay
        self.parent.after(10, self._update_vehicle_status_overlays)

        # Stats
        total = len(rows)
        available = sum(1 for r in rows if str(r[3]).lower() == "available")
        veh_ids = [str(r[0]) for r in rows]
        in_use = self._compute_in_use_count(set(veh_ids))
        self.vehicles_stats_label.configure(
            text=f"Total: {total} | Available: {available} | In Use: {in_use} | Maintenance: 0"
        )

    def _forward_event_to_tree_with_seq(self, event, sequence: str):
        """Forward mouse events from overlay label to underlying treeview."""
        with suppress(Exception):
            self.vehicles_tree.event_generate(sequence, x=event.x, y=event.y)
        return "break"

    def _update_vehicle_status_overlays(self):
        """Redraw colored text only over the Status column cells.

        This uses a transparent-like canvas overlay that draws the status text in
        green/red at the exact bbox of the Status column, while the underlying
        treeview still holds the original text (which we visually cover).
        """
        tree = self.vehicles_tree
        try:
            # Destroy existing labels
            for lbl in list(getattr(self, "_veh_status_labels", {}).values()):
                with suppress(Exception):
                    lbl.destroy()
            self._veh_status_labels.clear()
            # Determine column identifier for 'Status'
            status_col = "Status"
            field_bg, select_bg = self._get_tree_colors()
            # For each visible item, draw status text
            for item in tree.get_children(""):
                bbox = tree.bbox(item, status_col)
                if not bbox:
                    continue
                x, y, w, h = bbox
                vals = tree.item(item, "values")
                if len(vals) < 5:
                    continue
                status_text = str(vals[4])
                if not status_text:
                    continue
                color = (
                    "#34d058"
                    if status_text.lower() == "available"
                    else "#ff6b6b"
                    if status_text.lower() == "unavailable"
                    else None
                )
                if not color:
                    continue
                # Create an overlay label only covering the Status cell
                bg_color = select_bg if item in tree.selection() else field_bg
                lbl = tk.Label(
                    tree,
                    text=status_text,
                    fg=color,
                    bg=bg_color or tree.cget("background"),
                    borderwidth=0,
                    padx=4,
                    pady=0,
                    anchor="w",
                )
                lbl.place(x=x + 2, y=y + 1, width=w - 4, height=h - 2)
                # Forward clicks to tree for normal behavior
                for seq in (
                    "<Button-1>",
                    "<Double-Button-1>",
                    "<B1-Motion>",
                    "<ButtonRelease-1>",
                    "<MouseWheel>",
                ):
                    lbl.bind(seq, lambda e, s=seq: self._forward_event_to_tree_with_seq(e, s))
                self._veh_status_labels[item] = lbl
        except Exception:
            # Fail silently to avoid impacting UX
            pass

    def _get_tree_colors(self):
        """Return (fieldbackground, selectbackground) from ttk style with fallbacks."""
        try:
            style = ttk.Style(self.vehicles_tree)
            field_bg = style.lookup("Treeview", "fieldbackground") or style.lookup(
                "Treeview", "background"
            )
            select_bg = style.lookup("Treeview", "selectbackground")
            # Fallbacks
            if not field_bg:
                field_bg = self.vehicles_tree.cget("background")
            if not select_bg:
                # Try active selection color
                select_bg = style.lookup("Treeview", "focusfill") or field_bg
            return field_bg, select_bg
        except Exception:
            bg = self.vehicles_tree.cget("background")
            return bg, bg

    # Zebra helpers removed

    def _configure_vehicle_columns(self, enriched: bool = False, mode: str = "base"):
        """Configure vehicles tree columns depending on data source.

        Args:
            enriched: Legacy parameter for backward compatibility
            mode: Column mode - "base", "enriched", or "fleet"
        """
        # Support legacy enriched parameter
        if enriched and mode == "base":
            mode = "enriched"

        self._vehicle_mode = mode
        self._vehicle_enriched = enriched or (mode == "enriched")

        # Select column set based on mode
        if mode == "fleet":
            cols = self.vehicles_columns_fleet
        elif mode == "enriched":
            cols = self.vehicles_columns_enriched
        else:
            cols = self.vehicles_columns_base

        self.vehicles_tree.configure(columns=cols)

        # Headings
        self.vehicles_tree.heading("#0", text="")
        for name in cols:
            text = "ID" if name == "ID" else name
            self.vehicles_tree.heading(name, text=text)

        # Widths - comprehensive map for all column types
        self.vehicles_tree.column("#0", width=0, stretch=False)
        width_map = {
            "ID": 50,
            "Vehicle Number": 120,
            "Vehicle Name": 120,
            "Type": 100,
            "Location": 100,
            "Status": 100,
            "Priority": 80,
            "Capacity": 80,
            "VIN": 150,
            "GeoTab": 110,
            "Brand/Rental": 120,
            "Service Type": 200,
            "Ownership": 120,
            "Make": 100,
            "Model": 120,
            "Year": 60,
            "License Plate": 100,
            "Reg. Expiry": 100,
            "Station": 80,
        }
        for name in cols:
            self.vehicles_tree.column(name, width=width_map.get(name, 100))

    def set_allocated_vehicles_getter(self, getter):
        """Wire a callable returning a set of allocated vehicle IDs."""
        self._allocated_vehicles_getter = getter

    def _compute_in_use_count(self, vehicle_ids: set[str]) -> int:
        try:
            getter = getattr(self, "_allocated_vehicles_getter", None)
            if not getter:
                return 0
            allocated = getter() or set()
            allocated = {str(v).strip() for v in allocated}
            return len(vehicle_ids & allocated)
        except Exception:
            return 0

    def populate_drivers_tree(self, df: pd.DataFrame):
        """Populate drivers treeview with data.

        Handles both legacy driver sheets and AssociateData.csv format.
        """
        # Clear existing data
        self.drivers_tree.delete(*self.drivers_tree.get_children())

        # Detect source format
        cols_map = {c.lower().strip(): c for c in df.columns}
        is_associate_data = "transporterid" in cols_map or "name and id" in cols_map

        if is_associate_data:
            # Map AssociateData.csv columns
            for idx, row in df.iterrows():
                # Parse expiration date safely
                exp_date = row.get("ID expiration", "")
                if pd.notna(exp_date):
                    try:
                        exp_date = pd.to_datetime(exp_date).strftime("%m/%d/%Y")
                    except Exception:
                        exp_date = str(exp_date)
                else:
                    exp_date = ""

                values = (
                    idx + 1,
                    str(row.get("TransporterID", "")).strip(),
                    str(row.get("Name and ID", "")).strip(),
                    str(row.get("Position", "")).strip(),
                    str(row.get("Qualifications", "")).strip(),
                    exp_date,
                    str(row.get("Personal Phone Number", "")).strip(),
                    str(row.get("Work Phone Number", "")).strip(),
                    str(row.get("Email", "")).strip(),
                    str(row.get("Status", "")).strip(),
                )

                # Color-code by status
                status = str(row.get("Status", "")).upper()
                tag = "active" if status == "ACTIVE" else "inactive"
                self.drivers_tree.insert("", "end", values=values, tags=(tag,))

            # Configure status tags with colors
            self.drivers_tree.tag_configure("active", foreground="#34d058")
            self.drivers_tree.tag_configure("inactive", foreground="#ff6b6b")

            # Update statistics with expiration warnings
            total = len(df)
            active = (
                len(df[df.get("Status", "").str.upper() == "ACTIVE"])
                if "Status" in df.columns
                else 0
            )
            inactive = total - active

            # Calculate expiration warnings
            exp_col = "ID expiration"
            if exp_col in df.columns:
                today = pd.Timestamp.now()
                df_exp = df[pd.notna(df[exp_col])].copy()
                df_exp[exp_col] = pd.to_datetime(df_exp[exp_col], errors="coerce")
                expiring_soon = len(
                    df_exp[
                        (df_exp[exp_col] >= today)
                        & (df_exp[exp_col] <= today + pd.Timedelta(days=30))
                    ]
                )
                expired = len(df_exp[df_exp[exp_col] < today])

                self.drivers_stats_label.configure(
                    text=f"Total: {total} | Active: {active} | Inactive: {inactive} | "
                    f"Expiring Soon: {expiring_soon} | Expired: {expired}"
                )
            else:
                self.drivers_stats_label.configure(
                    text=f"Total: {total} | Active: {active} | Inactive: {inactive}"
                )

        else:
            # Legacy format handling
            for idx, row in df.iterrows():
                values = (
                    idx + 1,
                    row.get("Employee ID", ""),
                    row.get("Name", ""),
                    row.get("Location", ""),
                    row.get("Status", ""),
                    row.get("Priority", ""),
                    row.get("Experience", ""),
                    row.get("License Type", ""),
                )
                self.drivers_tree.insert("", "end", values=values)

            # Legacy statistics
            total = len(df)
            active = len(df[df.get("Status", "") == "active"]) if "Status" in df else 0
            avg_exp = df["Experience"].mean() if "Experience" in df else 0
            self.drivers_stats_label.configure(
                text=f"Total: {total} | Active: {active} | Inactive: {total - active} | "
                f"Average Experience: {avg_exp:.1f} years"
            )

        # Persist for validation/export
        self.current_data["drivers"] = df.copy()

    def add_item(self, data_type: str):
        """Add new item."""
        # This would open a dialog to add new vehicle or driver
        logger.info(f"Add {data_type} requested")

    def edit_item(self, data_type: str):
        """Edit selected item."""
        # This would open a dialog to edit selected item
        logger.info(f"Edit {data_type} requested")

    def delete_item(self, data_type: str):
        """Delete selected items."""
        tree = self.vehicles_tree if data_type == "vehicle" else self.drivers_tree
        selected = tree.selection()

        if selected and messagebox.askyesno(
            "Confirm Delete", f"Delete {len(selected)} {data_type}(s)?"
        ):
            for item in selected:
                tree.delete(item)
            logger.info(f"Deleted {len(selected)} {data_type}(s)")

    def search_items(self, data_type: str, search_text: str):
        """Search and filter items."""
        tree = self.vehicles_tree if data_type == "vehicle" else self.drivers_tree

        # Simple search: toggle 'hidden' tag while preserving status tags
        for item in tree.get_children():
            values = tree.item(item)["values"]
            existing = set(tree.item(item, "tags"))
            match = any(search_text.lower() in str(v).lower() for v in values)
            if match:
                existing.discard("hidden")
            else:
                existing.add("hidden")
            tree.item(item, tags=tuple(existing))

    def filter_by_qualification(self, qual_filter: str):
        """Filter drivers by qualification type.

        Args:
            qual_filter: Qualification filter value (All, Step Van, EDV, CDV, DOT, Helper Only)
        """
        if qual_filter == "All":
            # Clear all hidden tags
            for item in self.drivers_tree.get_children():
                tags = set(self.drivers_tree.item(item, "tags"))
                tags.discard("hidden")
                self.drivers_tree.item(item, tags=tuple(tags))
            return

        # Map filter to search terms
        filter_map = {
            "Step Van": "step van",
            "EDV": "edv",
            "CDV": "cdv",
            "DOT": "dot",
            "Helper Only": "helper",
        }
        search_term = filter_map.get(qual_filter, "").lower()

        for item in self.drivers_tree.get_children():
            values = self.drivers_tree.item(item, "values")
            if len(values) < 5:
                continue

            qualifications = str(values[4]).lower()  # Qualifications column
            tags = set(self.drivers_tree.item(item, "tags"))

            if search_term in qualifications:
                tags.discard("hidden")
            else:
                tags.add("hidden")

            self.drivers_tree.item(item, tags=tuple(tags))

    def import_data(self, data_type: str):
        """Import data from CSV."""
        filename = filedialog.askopenfilename(
            title=f"Import {data_type.title()}s",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if filename:
            # Import logic here
            logger.info(f"Imported {data_type}s from: {filename}")

    def export_data(self, data_type: str):
        """Export data to CSV."""
        filename = filedialog.asksaveasfilename(
            title=f"Export {data_type.title()}s",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if filename:
            try:
                if data_type == "vehicle":
                    # Build an export DataFrame normalized across sources
                    rows = []
                    for item in self.vehicles_tree.get_children(""):
                        vals = self.vehicles_tree.item(item, "values")
                        if len(vals) < 7:
                            continue
                        _, veh_num, vtype, _loc, status, _prio, _cap = vals
                        details = getattr(self, "_vehicle_details", {}).get(str(veh_num), {})
                        rows.append(
                            {
                                "Vehicle Number": veh_num,
                                "Type": vtype,
                                "Status": status,
                                "VIN": details.get("VIN", ""),
                                "GeoTab": details.get("GeoTab", ""),
                                "Branded/Rental": details.get("Branded/Rental", ""),
                            }
                        )
                    df = pd.DataFrame(rows)
                else:
                    # Drivers export: dump current tree values
                    rows = []
                    for item in self.drivers_tree.get_children(""):
                        vals = self.drivers_tree.item(item, "values")
                        if len(vals) < 8:
                            continue
                        _, emp_id, name, loc, status, priority, exp, lic = vals
                        rows.append(
                            {
                                "Employee ID": emp_id,
                                "Name": name,
                                "Location": loc,
                                "Status": status,
                                "Priority": priority,
                                "Experience": exp,
                                "License Type": lic,
                            }
                        )
                    df = pd.DataFrame(rows)

                df.to_csv(filename, index=False)
                messagebox.showinfo("Export", f"Exported {data_type}s to: {filename}")
                logger.info(f"Exported {data_type}s to: {filename}")
            except Exception as e:
                logger.error(f"Export failed: {e}")
                messagebox.showerror("Export Error", str(e))

    def _build_vehicles_export_df(self) -> pd.DataFrame:
        """Construct a normalized vehicles DataFrame from the current grid.

        Includes enrichment columns when available.
        """
        rows = []
        for item in self.vehicles_tree.get_children(""):
            vals = self.vehicles_tree.item(item, "values")
            if len(vals) < 7:
                continue
            # Base columns by current column config
            col_names = list(self.vehicles_tree["columns"])  # order includes ID first
            row_map = {col_names[i]: vals[i] for i in range(min(len(col_names), len(vals)))}
            # Normalize output keys
            record = {
                "Vehicle Number": row_map.get("Vehicle Number", ""),
                "Type": row_map.get("Type", ""),
                "Location": row_map.get("Location", ""),
                "Status": row_map.get("Status", ""),
                "Priority": row_map.get("Priority", ""),
                "Capacity": row_map.get("Capacity", ""),
            }
            # Enrichment
            if self._vehicle_enriched:
                record.update(
                    {
                        "VIN": row_map.get("VIN", ""),
                        "GeoTab": row_map.get("GeoTab", ""),
                        "Branded/Rental": row_map.get("Brand/Rental", ""),
                    }
                )
            rows.append(record)
        return pd.DataFrame(rows)

    def _build_drivers_export_df(self) -> pd.DataFrame:
        """Build export DataFrame from current drivers tree.

        Supports both associate data format (10 columns) and legacy format (8 columns).
        """
        rows = []
        for item in self.drivers_tree.get_children(""):
            vals = self.drivers_tree.item(item, "values")

            # Detect format by column count
            if len(vals) >= 10:
                # Associate data format
                rows.append(
                    {
                        "Name and ID": vals[2],
                        "TransporterID": vals[1],
                        "Position": vals[3],
                        "Qualifications": vals[4],
                        "ID expiration": vals[5],
                        "Personal Phone Number": vals[6],
                        "Work Phone Number": vals[7],
                        "Email": vals[8],
                        "Status": vals[9],
                    }
                )
            elif len(vals) >= 8:
                # Legacy format
                rows.append(
                    {
                        "Employee ID": vals[1],
                        "Name": vals[2],
                        "Location": vals[3],
                        "Status": vals[4],
                        "Priority": vals[5],
                        "Experience": vals[6],
                        "License Type": vals[7],
                    }
                )

        return pd.DataFrame(rows)

    def refresh_data(self):
        """Refresh current data."""
        if self.current_file:
            self.load_data()

    def validate_data(self):
        """Validate current data with user-friendly summary."""
        active_tab = self.notebook.get()
        if active_tab == "Vehicles":
            df = self.current_data.get("vehicles")
            if df is None or df.empty:
                messagebox.showinfo("Validation", "No vehicle data to validate.")
                return
            summary = self._validate_vehicles(df)
            messagebox.showinfo("Validation", summary)
        else:
            # Driver validation
            df = self.current_data.get("drivers")
            if df is None or df.empty:
                messagebox.showinfo("Validation", "No driver data to validate.")
                return
            summary = self._validate_drivers(df)
            messagebox.showinfo("Validation", summary)

    def _validate_vehicles(self, df: pd.DataFrame) -> str:
        """Perform basic, non-intrusive validation on Vehicles.

        Handles multiple formats:
        - VehiclesData.xlsx (fleet inventory)
        - Daily Summary Vehicle Status
        - Legacy Vehicle Log
        """
        from datetime import timedelta

        issues = []
        warnings = []
        cols = {c.lower().strip(): c for c in df.columns}

        # Detect source format
        is_vehicles_data = "vin" in cols and "vehiclename" in cols

        if is_vehicles_data:
            # VehiclesData.xlsx format validation
            van_col = cols.get("vehiclename")
            vin_col = cols.get("vin")
            op_col = cols.get("operationalstatus")
            reg_col = cols.get("registrationexpirydate")
            ownership_end_col = cols.get("ownershipenddate")

            # Required columns for fleet inventory
            required = ["vehicleName", "vin", "operationalStatus", "serviceType"]
            for req in required:
                req_lower = req.lower()
                if req_lower not in cols:
                    issues.append(f"Missing required column: {req}")

            # VIN uniqueness
            if vin_col and vin_col in df.columns:
                try:
                    vin_series = df[vin_col].astype(str).str.strip()
                    vin_series = vin_series[vin_series != ""]
                    dupes = vin_series[vin_series.duplicated()].unique().tolist()
                    if dupes:
                        issues.append(
                            f"Duplicate VINs: {', '.join(map(str, dupes[:5]))}{'...' if len(dupes)>5 else ''}"
                        )
                except Exception:
                    issues.append("Could not evaluate VIN uniqueness")

            # Vehicle name uniqueness
            if van_col and van_col in df.columns:
                try:
                    name_series = df[van_col].astype(str).str.strip()
                    dupes = name_series[name_series.duplicated()].unique().tolist()
                    if dupes:
                        issues.append(
                            f"Duplicate vehicle names: {', '.join(map(str, dupes[:5]))}{'...' if len(dupes)>5 else ''}"
                        )
                except Exception:
                    issues.append("Could not evaluate vehicle name uniqueness")

            # Operational status validation
            if op_col and op_col in df.columns:
                try:
                    statuses = df[op_col].dropna().astype(str).str.upper().unique()
                    valid_statuses = {"OPERATIONAL", "GROUNDED", "MAINTENANCE", "INACTIVE"}
                    invalid = set(statuses) - valid_statuses
                    if invalid:
                        warnings.append(
                            f"Unexpected operational statuses: {', '.join(sorted(invalid))}"
                        )

                    # Count grounded vehicles
                    grounded_count = (df[op_col].astype(str).str.upper() != "OPERATIONAL").sum()
                    if grounded_count > 0:
                        warnings.append(f"{grounded_count} vehicles are not operational")
                except Exception:
                    issues.append("Could not validate operational status")

            # Registration expiry warnings
            if reg_col and reg_col in df.columns:
                try:
                    today = pd.Timestamp.now()
                    warning_threshold = today + timedelta(days=30)

                    # Parse dates
                    reg_dates = pd.to_datetime(df[reg_col], errors="coerce")

                    # Expired registrations
                    expired = df[reg_dates < today]
                    if len(expired) > 0:
                        expired_names = expired[van_col].astype(str).tolist()[:5]
                        warnings.append(
                            f"⚠️ {len(expired)} vehicles with EXPIRED registrations: {', '.join(expired_names)}{'...' if len(expired)>5 else ''}"
                        )

                    # Expiring soon
                    expiring_soon = df[(reg_dates >= today) & (reg_dates <= warning_threshold)]
                    if len(expiring_soon) > 0:
                        expiring_names = expiring_soon[van_col].astype(str).tolist()[:5]
                        warnings.append(
                            f"⏰ {len(expiring_soon)} vehicles expiring within 30 days: {', '.join(expiring_names)}{'...' if len(expiring_soon)>5 else ''}"
                        )
                except Exception as e:
                    warnings.append(f"Could not check registration expiry dates: {e}")

            # Ownership/lease end date warnings
            if ownership_end_col and ownership_end_col in df.columns:
                try:
                    today = pd.Timestamp.now()
                    warning_threshold = today + timedelta(days=90)

                    # Parse dates
                    end_dates = pd.to_datetime(df[ownership_end_col], errors="coerce")

                    # Ending soon
                    ending_soon = df[(end_dates >= today) & (end_dates <= warning_threshold)]
                    if len(ending_soon) > 0:
                        ending_names = ending_soon[van_col].astype(str).tolist()[:5]
                        warnings.append(
                            f"📅 {len(ending_soon)} vehicles with ownership/lease ending within 90 days: {', '.join(ending_names)}{'...' if len(ending_soon)>5 else ''}"
                        )
                except Exception:
                    pass  # Ownership end date is optional

        else:
            # Daily Summary / Legacy format validation
            van_col = cols.get("van id") or cols.get("vehicle id") or "Vehicle Number"
            op_col = cols.get("opnal? y/n") or cols.get("operational")
            type_col = cols.get("type") or cols.get("vehicle type") or "Type"

            # Required columns
            for req in [van_col, type_col]:
                if req not in df.columns:
                    issues.append(f"Missing required column: {req}")

            # Uniqueness
            try:
                van_series = df[van_col].astype(str).str.strip()
                dupes = van_series[van_series.duplicated()].unique().tolist()
                if dupes:
                    issues.append(
                        f"Duplicate vehicle IDs: {', '.join(map(str, dupes[:10]))}{'...' if len(dupes)>10 else ''}"
                    )
            except Exception:
                issues.append("Could not evaluate duplicate vehicle IDs")

            # Operational/Status field presence
            if op_col and op_col in df.columns:
                invalid_op = df[op_col].dropna().astype(str).str.upper().isin(["Y", "N"]).all()
                if not invalid_op:
                    issues.append("Operational column contains values other than Y/N")
            else:
                issues.append("Operational status column not found (Opnal? Y/N)")

            # Type normalization hints
            known_types = {"extra large", "large", "step van"}
            if type_col in df.columns:
                unknown_types = sorted(
                    {str(x).strip().lower() for x in df[type_col].dropna().unique()} - known_types
                )
                if unknown_types:
                    issues.append(
                        f"Unrecognized vehicle types: {', '.join(unknown_types[:10])}{'...' if len(unknown_types)>10 else ''}"
                    )

            # Cross-check with Vehicle Log enrichment if available
            details = getattr(self, "_vehicle_details", {})
            if details:
                try:
                    van_series = df[van_col].astype(str).str.strip()
                    total = int(van_series.nunique())
                    with_details = sum(
                        1
                        for vid in van_series
                        if str(vid) in details and details[str(vid)].get("VIN")
                    )
                    without_vin = [
                        str(vid)
                        for vid in van_series
                        if str(vid) in details and not details[str(vid)].get("VIN")
                    ]
                    if total:
                        coverage = with_details / total * 100.0
                        if coverage < 80:
                            issues.append(
                                f"VIN coverage low: {coverage:.1f}% of vehicles have VIN in Vehicle Log"
                            )
                    if without_vin:
                        issues.append(
                            f"Vehicles missing VIN: {', '.join(without_vin[:10])}{'...' if len(without_vin)>10 else ''}"
                        )
                except Exception:
                    issues.append("Could not compute Vehicle Log enrichment metrics")

        # Build result message
        if not issues and not warnings:
            total_rows = len(df)
            format_name = "fleet inventory" if is_vehicles_data else "vehicle status"
            return f"Data validation complete. {total_rows} vehicles checked ({format_name}). No issues found."

        result_parts = []
        if issues:
            result_parts.append("⚠️ Issues:\n- " + "\n- ".join(issues))
        if warnings:
            result_parts.append("ℹ️ Warnings:\n- " + "\n- ".join(warnings))

        return "\n\n".join(result_parts)

    def _validate_drivers(self, df: pd.DataFrame) -> str:
        """Validate driver/associate data.

        Performs comprehensive validation on driver data including:
        - Required column presence
        - Duplicate detection
        - Expiration date warnings
        - Status consistency
        - Contact information completeness

        Args:
            df: DataFrame containing driver/associate data

        Returns:
            Validation summary string with issues or success message
        """
        issues = []
        cols_map = {c.lower().strip(): c for c in df.columns}

        # Detect format
        is_associate = "transporterid" in cols_map

        if is_associate:
            # Required columns for associate data
            required = ["Name and ID", "TransporterID", "Status", "Qualifications"]
            for req in required:
                if req not in df.columns:
                    issues.append(f"Missing required column: {req}")

            # Check for duplicate TransporterIDs
            if "TransporterID" in df.columns:
                dupes = df["TransporterID"].duplicated()
                dupe_count = dupes.sum()
                if dupe_count > 0:
                    dupe_ids = df.loc[dupes, "TransporterID"].unique().tolist()
                    issues.append(
                        f"Found {dupe_count} duplicate TransporterID values: {', '.join(map(str, dupe_ids[:5]))}"
                        f"{'...' if len(dupe_ids) > 5 else ''}"
                    )

            # Check expiration dates
            if "ID expiration" in df.columns:
                today = pd.Timestamp.now()
                exp_dates = pd.to_datetime(df["ID expiration"], errors="coerce")
                expired = (exp_dates < today).sum()
                expiring_30 = (
                    (exp_dates >= today) & (exp_dates <= today + pd.Timedelta(days=30))
                ).sum()

                if expired > 0:
                    # Get expired associate names
                    expired_assocs = df.loc[exp_dates < today, "Name and ID"].head(5).tolist()
                    issues.append(
                        f"⚠️ {expired} associates have EXPIRED certifications: {', '.join(expired_assocs)}"
                        f"{'...' if expired > 5 else ''}"
                    )

                if expiring_30 > 0:
                    # Get expiring soon associate names
                    expiring_assocs = (
                        df.loc[
                            (exp_dates >= today) & (exp_dates <= today + pd.Timedelta(days=30)),
                            "Name and ID",
                        ]
                        .head(5)
                        .tolist()
                    )
                    issues.append(
                        f"⚠️ {expiring_30} associates have certifications expiring within 30 days: {', '.join(expiring_assocs)}"
                        f"{'...' if expiring_30 > 5 else ''}"
                    )

            # Check status consistency
            if "Status" in df.columns:
                valid_statuses = ["ACTIVE", "INACTIVE"]
                invalid_status = ~df["Status"].str.upper().isin(valid_statuses)
                invalid_count = invalid_status.sum()
                if invalid_count > 0:
                    invalid_vals = df.loc[invalid_status, "Status"].unique().tolist()
                    issues.append(
                        f"Found {invalid_count} records with invalid status: {', '.join(map(str, invalid_vals))}"
                    )

            # Contact information completeness
            contact_fields = {
                "Email": "email addresses",
                "Personal Phone Number": "personal phone numbers",
                "Work Phone Number": "work phone numbers",
            }
            for col, desc in contact_fields.items():
                if col in df.columns:
                    missing = df[col].isna() | (df[col].astype(str).str.strip() == "")
                    missing_count = missing.sum()
                    if missing_count > 0:
                        issues.append(f"{missing_count} associates missing {desc}")

            # Qualification completeness
            if "Qualifications" in df.columns:
                missing_qual = df["Qualifications"].isna() | (
                    df["Qualifications"].astype(str).str.strip() == ""
                )
                missing_qual_count = missing_qual.sum()
                if missing_qual_count > 0:
                    issues.append(f"{missing_qual_count} associates missing qualifications")

        else:
            # Legacy format validation (minimal)
            issues.append("Legacy driver format detected - limited validation available")

        if not issues:
            return f"Driver validation complete. {len(df)} associates checked. No issues found."

        return "Validation summary:\n- " + "\n- ".join(issues)

    def show_vehicle_details(self):
        """Show VIN/GeoTab/Brand details for selected vehicle when available."""
        sel = self.vehicles_tree.selection()
        if not sel:
            messagebox.showinfo("Details", "Select a vehicle to view details.")
            return
        item = sel[0]
        values = self.vehicles_tree.item(item)["values"]
        if len(values) < 2:
            messagebox.showinfo("Details", "No vehicle selected.")
            return
        van_id = str(values[1])

        details = getattr(self, "_vehicle_details", {}).get(van_id)
        if not details:
            messagebox.showinfo("Details", f"No additional details for {van_id}.")
            return

        info = (
            f"Vehicle: {van_id}\n"
            f"VIN: {details.get('VIN', '')}\n"
            f"GeoTab: {details.get('GeoTab', '')}\n"
            f"Brand/Rental: {details.get('Branded/Rental', '')}"
        )
        messagebox.showinfo("Vehicle Details", info)

    def generate_sample_data(self):
        """Generate sample data."""
        # Generate sample vehicles
        vehicles_data = []
        for i in range(1, 21):
            vehicles_data.append(
                {
                    "Vehicle Number": f"VEH{i:03d}",
                    "Type": ["Standard", "Premium", "Economy"][i % 3],
                    "Location": ["Main", "North", "South"][i % 3],
                    "Status": "available",
                    "Priority": 50 + (i % 3) * 10,
                    "Capacity": 4 + (i % 2) * 2,
                }
            )

        vehicles_df = pd.DataFrame(vehicles_data)
        self.populate_vehicles_tree(vehicles_df)

        # Generate sample drivers
        drivers_data = []
        for i in range(1, 11):
            drivers_data.append(
                {
                    "Employee ID": f"EMP{i:03d}",
                    "Name": f"Driver {i}",
                    "Location": ["Main", "North", "South"][i % 3],
                    "Status": "active",
                    "Priority": ["Low", "Medium", "High"][i % 3],
                    "Experience": i % 10,
                    "License Type": "Standard",
                }
            )

        drivers_df = pd.DataFrame(drivers_data)
        self.populate_drivers_tree(drivers_df)

        self.save_button.configure(state="normal")
        logger.info("Sample data generated")
