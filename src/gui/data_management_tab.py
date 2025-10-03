"""Data management tab for Resource Allocation GUI."""

import threading
import tkinter as tk
from tkinter import StringVar, filedialog, messagebox, ttk
from typing import Optional

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
            values=["Daily Summary (Vehicle Status)", "Custom Workbook (Vehicles)"],
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

        # Treeview
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
        self._vehicle_enriched = False
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
        try:
            self.vehicles_tree.tag_configure("hidden", foreground="gray")
        except Exception:
            pass

        # Prepare per-cell overlay labels for Status column coloring
        self._veh_status_labels: dict[str, tk.Label] = {}
        # Keep overlays in sync on resize/config
        self.vehicles_tree.bind("<Configure>", lambda e: self._update_vehicle_status_overlays())
        self.vehicles_tree.bind(
            "<<TreeviewSelect>>", lambda e: self._update_vehicle_status_overlays()
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

        # Treeview
        columns = (
            "ID",
            "Employee ID",
            "Name",
            "Location",
            "Status",
            "Priority",
            "Experience",
            "License Type",
        )
        self.drivers_tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings", selectmode="extended"
        )
        self.drivers_tree.grid(row=0, column=0, sticky="nsew")

        # Configure columns
        self.drivers_tree.heading("#0", text="")
        self.drivers_tree.heading("ID", text="ID")
        self.drivers_tree.heading("Employee ID", text="Employee ID")
        self.drivers_tree.heading("Name", text="Name")
        self.drivers_tree.heading("Location", text="Location")
        self.drivers_tree.heading("Status", text="Status")
        self.drivers_tree.heading("Priority", text="Priority")
        self.drivers_tree.heading("Experience", text="Experience")
        self.drivers_tree.heading("License Type", text="License Type")

        # Column widths
        self.drivers_tree.column("#0", width=0, stretch=False)
        self.drivers_tree.column("ID", width=50)
        self.drivers_tree.column("Employee ID", width=100)
        self.drivers_tree.column("Name", width=150)
        self.drivers_tree.column("Location", width=100)
        self.drivers_tree.column("Status", width=80)
        self.drivers_tree.column("Priority", width=80)
        self.drivers_tree.column("Experience", width=80)
        self.drivers_tree.column("License Type", width=100)

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
            "<KeyRelease>", lambda e: self.search_items(data_type, search_entry.get())
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
        """Load data from Excel file."""
        selected_source = self.source_var.get()

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

    def _resolve_daily_summary_path(self) -> Optional[str]:
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

        Accepts DataFrames from either legacy "Vehicles" sheet or Daily Summary
        "Vehicle Status" and maps columns accordingly.
        """
        # Clear existing data
        self.vehicles_tree.delete(*self.vehicles_tree.get_children())

        # Normalize source columns
        cols_map = {c.lower().strip(): c for c in df.columns}
        is_vehicle_status = ("van id" in cols_map) or ("vehicle id" in cols_map)

        rows = []
        if is_vehicle_status:
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

        # Insert rows
        # Enrichment-aware column setup
        has_enrichment = hasattr(self, "_vehicle_details") and bool(self._vehicle_details)
        if has_enrichment and not self._vehicle_enriched:
            self._configure_vehicle_columns(enriched=True)
        if not has_enrichment and self._vehicle_enriched:
            self._configure_vehicle_columns(enriched=False)

        for idx, (veh, vtype, loc, status, prio, cap) in enumerate(rows, start=1):
            if self._vehicle_enriched:
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
        try:
            self.vehicles_tree.event_generate(sequence, x=event.x, y=event.y)
        except Exception:
            pass
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
                try:
                    lbl.destroy()
                except Exception:
                    pass
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

    def _configure_vehicle_columns(self, enriched: bool):
        """Configure vehicles tree columns depending on enrichment presence."""
        self._vehicle_enriched = enriched
        cols = self.vehicles_columns_enriched if enriched else self.vehicles_columns_base
        self.vehicles_tree.configure(columns=cols)
        # Headings
        self.vehicles_tree.heading("#0", text="")
        for name in cols:
            if name == "ID":
                text = "ID"
            else:
                text = name
            self.vehicles_tree.heading(name, text=text)
        # Widths
        self.vehicles_tree.column("#0", width=0, stretch=False)
        width_map = {
            "ID": 50,
            "Vehicle Number": 120,
            "Type": 100,
            "Location": 100,
            "Status": 100,
            "Priority": 80,
            "Capacity": 80,
            "VIN": 130,
            "GeoTab": 110,
            "Brand/Rental": 120,
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
        """Populate drivers treeview with data."""
        # Clear existing data
        self.drivers_tree.delete(*self.drivers_tree.get_children())

        # Add data
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

        # Update statistics
        total = len(df)
        active = len(df[df.get("Status", "") == "active"]) if "Status" in df else 0
        avg_exp = df["Experience"].mean() if "Experience" in df else 0
        self.drivers_stats_label.configure(
            text=f"Total: {total} | Active: {active} | Inactive: {total - active} | Average Experience: {avg_exp:.1f} years"
        )

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

        if selected:
            if messagebox.askyesno("Confirm Delete", f"Delete {len(selected)} {data_type}(s)?"):
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
        rows = []
        for item in self.drivers_tree.get_children(""):
            vals = self.drivers_tree.item(item, "values")
            if len(vals) < 8:
                continue
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
            messagebox.showinfo("Validation", "Driver validation not implemented yet.")

    def _validate_vehicles(self, df: pd.DataFrame) -> str:
        """Perform basic, non-intrusive validation on Vehicles."""
        issues = []
        cols = {c.lower().strip(): c for c in df.columns}
        # Detect source
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
                    1 for vid in van_series if str(vid) in details and details[str(vid)].get("VIN")
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

        if not issues:
            # Provide a concise positive summary
            total_rows = len(df)
            return f"Data validation complete. {total_rows} vehicles checked. No issues found."
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
