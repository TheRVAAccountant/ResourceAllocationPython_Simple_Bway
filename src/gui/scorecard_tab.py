"""Scorecard tab for displaying DA current week performance data."""

from __future__ import annotations

import csv
import os
import platform
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

import customtkinter as ctk
from loguru import logger

from src.gui.widgets.recent_file_selector import RecentFileSelector
from src.models.scorecard import DAWeeklyPerformance, ScorecardMetadata
from src.services.scorecard_service import ScorecardData, ScorecardService
from src.utils.recent_files_manager import FileFieldType


class ScorecardTab:
    """GUI tab that visualizes weekly scorecard performance."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        *,
        scorecard_service: ScorecardService,
        settings: Optional[dict] = None,
    ) -> None:
        self.parent = parent
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(2, weight=1)

        self.scorecard_service = scorecard_service
        self.settings = settings or {}

        self.current_data: Optional[ScorecardData] = None
        self.filtered_rows: List[DAWeeklyPerformance] = []
        self._all_rows: List[DAWeeklyPerformance] = []
        self._current_path: Optional[str] = self.settings.get("scorecard_pdf_path")

        self.search_var = ctk.StringVar(value="")
        self.tier_var = ctk.StringVar(value="All")

        self._build_ui()
        self.refresh_data()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self.parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            header,
            text="Scorecard",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.summary_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("gray70", "gray50"),
        )
        self.summary_label.grid(row=1, column=0, sticky="w", pady=(6, 0))

        controls = ctk.CTkFrame(self.parent)
        controls.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=0)
        controls.grid_columnconfigure(2, weight=0)
        controls.grid_columnconfigure(3, weight=0)
        controls.grid_columnconfigure(4, weight=0)

        # File selector
        self._file_var = ctk.StringVar(value=self._current_path or "")
        self.file_selector = RecentFileSelector(
            controls,
            field_type=FileFieldType.SCORECARD_PDF,
            textvariable=self._file_var,
            placeholder_text="Select scorecard PDF...",
            on_file_selected_callback=self._on_file_selected,
        )
        self.file_selector.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(10, 10), pady=10)

        # Search
        search_entry = ctk.CTkEntry(
            controls,
            textvariable=self.search_var,
            placeholder_text="Search by DA name or transporter ID",
            width=240,
        )
        search_entry.grid(row=1, column=0, sticky="w", padx=(10, 10), pady=(0, 10))
        search_entry.bind("<KeyRelease>", lambda _event: self.apply_filters())

        # Tier filter
        tier_combo = ctk.CTkComboBox(
            controls,
            values=["All", "Fantastic", "Great", "Fair", "Poor"],
            variable=self.tier_var,
            width=150,
            command=lambda _value: self.apply_filters(),
        )
        tier_combo.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=(0, 10))

        # Buttons
        refresh_btn = ctk.CTkButton(
            controls,
            text="🔄 Refresh",
            width=110,
            command=lambda: self.refresh_data(force=True),
        )
        refresh_btn.grid(row=0, column=2, padx=(10, 5), pady=10)

        open_btn = ctk.CTkButton(
            controls,
            text="📂 Open PDF",
            width=110,
            command=self.open_scorecard_pdf,
        )
        open_btn.grid(row=0, column=3, padx=5, pady=10)

        export_btn = ctk.CTkButton(
            controls,
            text="📤 Export CSV",
            width=120,
            command=self.export_filtered,
        )
        export_btn.grid(row=0, column=4, padx=(5, 10), pady=10)

        # Table
        table_frame = ctk.CTkFrame(self.parent)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self.columns = [
            ("rank", "#", 40),
            ("name", "Name", 180),
            ("transporter_id", "Transporter ID", 140),
            ("overall_tier", "Tier", 100),
            ("delivered", "Delivered", 90),
            ("key_focus_area", "Key Focus", 110),
            ("dcr_percent", "DCR %", 80),
            ("pod_percent", "POD %", 80),
            ("seatbelt_off_rate", "Seatbelt", 80),
            ("speeding_event_rate", "Speeding", 80),
            ("distractions_rate", "Distract", 80),
            ("following_distance_rate", "Following", 80),
            ("sign_signal_violations", "Sign/Signal", 90),
            ("cdf_dpmo", "CDF DPMO", 90),
            ("ced_dpmo", "CED", 80),
            ("dsb_count", "DSB", 70),
            ("psb_status", "PSB", 90),
            ("dsb_events", "DSB DNR", 80),
            ("pod_opportunities", "POD Opps", 90),
        ]

        tree_columns = [col_id for col_id, _, _ in self.columns]
        self.tree = ttk.Treeview(
            table_frame,
            columns=tree_columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        style = ttk.Style()
        try:
            style.configure("Scorecard.Treeview", rowheight=28)
            style.configure("Scorecard.Treeview.Heading", font=("Helvetica", 12, "bold"))
            style.map("Scorecard.Treeview", background=[("selected", "#1f538d")])
            self.tree.configure(style="Scorecard.Treeview")
        except Exception:
            pass

        for col_id, heading, width in self.columns:
            self.tree.heading(col_id, text=heading)
            anchor = (
                "center"
                if col_id not in {"name", "transporter_id", "key_focus_area", "psb_status"}
                else "w"
            )
            self.tree.column(col_id, width=width, anchor=anchor)

        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=v_scroll.set)

        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=h_scroll.set)

        self.tree.tag_configure("fantastic", foreground="#20c997")
        self.tree.tag_configure("great", foreground="#0d6efd")
        self.tree.tag_configure("fair", foreground="#fd7e14")
        self.tree.tag_configure("poor", foreground="#dc3545")

    # ------------------------------------------------------------------
    def _on_file_selected(self, path: str) -> None:
        self._current_path = path
        self._file_var.set(path)
        self.refresh_data(force=True, override_path=path)

    def update_settings(self, settings: Optional[dict]) -> None:
        self.settings = settings or {}
        self._current_path = self.settings.get("scorecard_pdf_path")
        self._file_var.set(self._current_path or "")
        self.file_selector.set_file_path(self._current_path or "")
        self.refresh_data()

    # ------------------------------------------------------------------
    def refresh_data(self, *, force: bool = False, override_path: Optional[str] = None) -> None:
        path = override_path or self._current_path
        if force and path:
            data = self.scorecard_service.load_scorecard(path)
        else:
            data = self.scorecard_service.load_scorecard(path)

        if not data:
            self._all_rows = []
            self.filtered_rows = []
            self.tree.delete(*self.tree.get_children())
            self.summary_label.configure(text="No scorecard data available.")
            return

        self.current_data = data
        self._current_path = path or (data.metadata and self.settings.get("scorecard_pdf_path"))

        meta = data.metadata
        title_parts = []
        if meta.dsp_name:
            title_parts.append(meta.dsp_name)
        if meta.station:
            title_parts.append(meta.station)
        if meta.week_number:
            title_parts.append(f"Week {meta.week_number}")
        if meta.year:
            title_parts.append(str(meta.year))
        self.title_label.configure(text="Scorecard" if not title_parts else " | ".join(title_parts))

        self._all_rows = data.associates
        self.apply_filters()

    # ------------------------------------------------------------------
    def apply_filters(self) -> None:
        rows = getattr(self, "_all_rows", [])
        query = self.search_var.get().strip().lower()
        tier_filter = self.tier_var.get()

        def matches(row: DAWeeklyPerformance) -> bool:
            if query:
                if query not in row.name.lower() and query not in row.transporter_id.lower():
                    return False
            if tier_filter and tier_filter != "All":
                if row.overall_tier.lower() != tier_filter.lower():
                    return False
            return True

        filtered = [row for row in rows if matches(row)]
        self.filtered_rows = filtered
        self._populate_tree(filtered)
        self._update_summary()

    # ------------------------------------------------------------------
    def _populate_tree(self, rows: List[DAWeeklyPerformance]) -> None:
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            values = [
                row.rank,
                row.name,
                row.transporter_id,
                row.overall_tier,
                self._format_int(row.delivered),
                row.key_focus_area or "",
                self._format_percent(row.dcr_percent),
                self._format_percent(row.pod_percent),
                self._format_float(row.seatbelt_off_rate),
                self._format_float(row.speeding_event_rate),
                self._format_float(row.distractions_rate),
                self._format_float(row.following_distance_rate),
                self._format_float(row.sign_signal_violations),
                self._format_float(row.cdf_dpmo),
                self._format_float(row.ced_dpmo),
                self._format_float(row.dsb_count),
                row.psb_status or "",
                self._format_int(row.dsb_events),
                self._format_int(row.pod_opportunities),
            ]
            tier_tag = row.overall_tier.lower() if row.overall_tier else ""
            tags = (tier_tag,) if tier_tag in {"fantastic", "great", "fair", "poor"} else None
            self.tree.insert("", "end", values=values, tags=tags)

    def _update_summary(self) -> None:
        if not self.current_data:
            self.summary_label.configure(text="")
            return

        meta = self.current_data.metadata
        rows = self.filtered_rows
        total = len(getattr(self, "_all_rows", []))
        visible = len(rows)
        tiers = Counter((row.overall_tier or "Unknown" for row in rows))
        parts = [
            f"Showing {visible} of {total} associates",
        ]
        if meta.week_number and meta.year:
            parts.append(f"Week {meta.week_number} {meta.year}")
        if meta.station:
            parts.append(meta.station)
        tier_summary = ", ".join(f"{tier}: {count}" for tier, count in tiers.items())
        if tier_summary:
            parts.append(tier_summary)
        self.summary_label.configure(text=" | ".join(parts))

    # ------------------------------------------------------------------
    def open_scorecard_pdf(self) -> None:
        path = self._current_path or self.settings.get("scorecard_pdf_path")
        resolved = self.scorecard_service.resolve_scorecard_path(path)
        if not resolved:
            messagebox.showwarning("File Not Found", "Scorecard PDF path could not be resolved.")
            return
        try:
            if platform.system() == "Windows":
                os.startfile(resolved)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                os.system(f"open '{resolved}'")
            else:
                os.system(f"xdg-open '{resolved}'")
        except Exception as exc:
            logger.error(f"Failed to open scorecard PDF: {exc}")
            messagebox.showerror("Open Failed", f"Could not open file:\n{exc}")

    def export_filtered(self) -> None:
        if not self.filtered_rows:
            messagebox.showinfo("No Data", "There are no rows to export.")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Scorecard Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not filename:
            return

        try:
            with open(filename, "w", newline="", encoding="utf-8") as handle:
                fieldnames = [
                    "rank",
                    "name",
                    "transporter_id",
                    "overall_tier",
                    "delivered",
                    "key_focus_area",
                    "fico_score",
                    "seatbelt_off_rate",
                    "speeding_event_rate",
                    "distractions_rate",
                    "following_distance_rate",
                    "sign_signal_violations",
                    "cdf_dpmo",
                    "ced_dpmo",
                    "dcr_percent",
                    "dsb_count",
                    "pod_percent",
                    "psb_status",
                    "dsb_events",
                    "pod_opportunities",
                ]
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for row in self.filtered_rows:
                    writer.writerow(asdict(row))
            messagebox.showinfo(
                "Export Complete", f"Exported {len(self.filtered_rows)} rows to {filename}"
            )
        except Exception as exc:
            logger.error(f"Failed to export scorecard data: {exc}")
            messagebox.showerror("Export Failed", f"Could not export data:\n{exc}")

    # ------------------------------------------------------------------
    @staticmethod
    def _format_percent(value: Optional[float]) -> str:
        if value is None:
            return ""
        return f"{value:.1f}%"

    @staticmethod
    def _format_float(value: Optional[float]) -> str:
        if value is None:
            return ""
        return f"{value:.1f}"

    @staticmethod
    def _format_int(value: Optional[int]) -> str:
        if value is None:
            return ""
        return f"{value:,}"
