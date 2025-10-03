"""Associate listing tab for displaying company employee roster."""

from __future__ import annotations

import csv
import os
import platform
from datetime import datetime, date
from typing import List, Optional

import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from loguru import logger

from src.models.associate import AssociateRecord
from src.services.associate_service import AssociateService
from src.gui.utils import HoverTooltip


class AssociateListingTab:
    """GUI tab that renders the associate roster with filtering and actions."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        *,
        associate_service: AssociateService,
        settings: Optional[dict] = None,
    ) -> None:
        self.parent = parent
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(2, weight=1)

        self.associate_service = associate_service
        self.settings = settings or {}

        self._associate_path: Optional[str] = self.settings.get("associate_data_path")
        self.auto_refresh_enabled: bool = bool(self.settings.get("auto_refresh_associates", False))
        self.refresh_interval_minutes: int = self._safe_int(
            self.settings.get("associate_refresh_interval_minutes", 10), default=10
        )
        self._auto_refresh_job: Optional[str] = None

        self.records: List[AssociateRecord] = []
        self.filtered_records: List[AssociateRecord] = []
        self._row_tooltip_text: dict[str, str] = {}
        self._current_hover_item: Optional[str] = None

        self.search_var = ctk.StringVar(value="")
        self.status_var = ctk.StringVar(value="All")
        self.expiration_var = ctk.StringVar(value="All")

        self._build_ui()
        self.refresh_data(force=True)

    # ------------------------------------------------------------------
    # UI construction
    def _build_ui(self) -> None:
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            header_frame,
            text="Associate Listing",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.summary_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("gray70", "gray50"),
        )
        self.summary_label.grid(row=1, column=0, sticky="w", pady=(8, 0))

        controls_frame = ctk.CTkFrame(self.parent)
        controls_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=0)
        controls_frame.grid_columnconfigure(3, weight=0)
        controls_frame.grid_columnconfigure(4, weight=0)

        # File path label
        self.file_label = ctk.CTkLabel(
            controls_frame,
            text="Associate CSV: (not set)",
            font=ctk.CTkFont(size=12)
        )
        self.file_label.grid(row=0, column=0, columnspan=5, sticky="w", pady=(10, 6))

        search_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="Search by name, transporter ID, position, or email…",
            textvariable=self.search_var,
            width=320,
        )
        search_entry.grid(row=1, column=0, sticky="w", padx=(10, 10), pady=5)
        search_entry.bind("<KeyRelease>", lambda _event: self.apply_filters())

        status_combo = ctk.CTkComboBox(
            controls_frame,
            values=["All", "Active", "Inactive"],
            variable=self.status_var,
            width=140,
            command=lambda _value: self.apply_filters(),
        )
        status_combo.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        expiration_options = [
            "All",
            "Expired",
            "Expiring ≤30 days",
            "Expiring ≤60 days",
            "Expiring ≤90 days",
        ]
        expiration_combo = ctk.CTkComboBox(
            controls_frame,
            values=expiration_options,
            variable=self.expiration_var,
            width=160,
            command=lambda _value: self.apply_filters(),
        )
        expiration_combo.grid(row=1, column=2, sticky="w", padx=10, pady=5)

        self.refresh_button = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh",
            width=110,
            command=lambda: self.refresh_data(force=True),
        )
        self.refresh_button.grid(row=1, column=3, padx=10, pady=5)

        self.open_button = ctk.CTkButton(
            controls_frame,
            text="📂 Open CSV",
            width=110,
            command=self.open_current_file,
        )
        self.open_button.grid(row=1, column=4, padx=(10, 0), pady=5)

        self.export_button = ctk.CTkButton(
            controls_frame,
            text="📤 Export Filtered",
            width=140,
            command=self.export_filtered,
        )
        self.export_button.grid(row=1, column=5, padx=(10, 10), pady=5)

        # Treeview container
        table_frame = ctk.CTkFrame(self.parent)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = (
            "Name",
            "Transporter ID",
            "Position",
            "Qualifications",
            "ID Expiration",
            "Days Remaining",
            "Status",
            "Personal Phone",
            "Work Phone",
            "Email",
        )

        self.tree = ttk.Treeview(
            table_frame,
            show="headings",
            columns=columns,
            selectmode="browse",
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        self._configure_treeview(columns)

        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=h_scrollbar.set)

        self.tree.tag_configure("expired", foreground="#ff6b6b")
        self.tree.tag_configure("expiring", foreground="#f2c744")
        self.tree.tag_configure("inactive", foreground="#9aa0a6")

        self._tooltip = HoverTooltip(self.parent)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", lambda _e: self._tooltip.cancel())
        self.tree.bind("<ButtonPress-1>", lambda _e: self._tooltip.cancel())
        self.tree.bind("<MouseWheel>", lambda _e: self._tooltip.cancel())
        self.tree.bind("<KeyPress>", lambda _e: self._tooltip.cancel())

    def _configure_treeview(self, columns: tuple[str, ...]) -> None:
        style = ttk.Style()
        try:
            style.configure("Associates.Treeview", rowheight=28)
            style.configure("Associates.Treeview.Heading", font=("Helvetica", 12, "bold"))
            style.map("Associates.Treeview", background=[("selected", "#1f538d")])
            self.tree.configure(style="Associates.Treeview")
        except Exception:
            pass

        widths = {
            "Name": 220,
            "Transporter ID": 140,
            "Position": 140,
            "Qualifications": 220,
            "ID Expiration": 120,
            "Days Remaining": 120,
            "Status": 100,
            "Personal Phone": 140,
            "Work Phone": 140,
            "Email": 220,
        }

        for column in columns:
            self.tree.heading(column, text=column)
            width = widths.get(column, 120)
            self.tree.column(column, width=width, anchor="w")

    # ------------------------------------------------------------------
    # Data lifecycle
    def refresh_data(self, *, force: bool = False) -> None:
        try:
            records = self.associate_service.load_associates(
                path=self._associate_path,
                force_reload=force,
            )
        except Exception as exc:
            logger.error(f"Associate listing refresh failed: {exc}")
            messagebox.showerror("Associate Refresh Failed", f"Unable to load associates:\n{exc}")
            return

        self.records = records
        self.apply_filters()
        self._update_file_label()
        self._schedule_auto_refresh()

    def apply_filters(self) -> None:
        filtered = list(self.records)

        status_filter = (self.status_var.get() or "All").lower()
        if status_filter == "active":
            filtered = [record for record in filtered if record.is_active]
        elif status_filter == "inactive":
            filtered = [record for record in filtered if not record.is_active]

        exp_filter = self.expiration_var.get() or "All"
        if exp_filter == "Expired":
            filtered = [record for record in filtered if record.is_expired]
        elif exp_filter == "Expiring ≤30 days":
            filtered = [record for record in filtered if self._within_days(record, 30)]
        elif exp_filter == "Expiring ≤60 days":
            filtered = [record for record in filtered if self._within_days(record, 60)]
        elif exp_filter == "Expiring ≤90 days":
            filtered = [record for record in filtered if self._within_days(record, 90)]

        query = self.search_var.get().strip().lower()
        if query:
            filtered = [
                record
                for record in filtered
                if query in record.name.lower()
                or query in record.transporter_id.lower()
                or query in record.position.lower()
                or query in record.email.lower()
            ]

        self.filtered_records = filtered
        self._populate_tree(filtered)
        self._update_summary(filtered)

    def _populate_tree(self, records: List[AssociateRecord]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        self._row_tooltip_text.clear()

        for record in records:
            expiration_text = self._format_date(record.id_expiration)
            days_text = self._format_days(record.days_until_expiration)
            personal_phone = self._format_phone(record.personal_phone)
            work_phone = self._format_phone(record.work_phone)

            tags: List[str] = []
            if record.is_expired:
                tags.append("expired")
            elif record.is_expiring_soon:
                tags.append("expiring")
            if not record.is_active:
                tags.append("inactive")

            insert_kwargs = {}
            if tags:
                insert_kwargs["tags"] = tuple(tags)

            iid = self.tree.insert(
                "",
                "end",
                values=(
                    record.name,
                    record.transporter_id,
                    record.position,
                    record.formatted_qualifications(),
                    expiration_text,
                    days_text,
                    record.status.title(),
                    personal_phone,
                    work_phone,
                    record.email,
                ),
                **insert_kwargs,
            )
            self._row_tooltip_text[iid] = self._format_tooltip_text(
                record,
                expiration_text=expiration_text,
                days_text=days_text,
                personal_phone=personal_phone,
                work_phone=work_phone,
            )

        if not records:
            self.summary_label.configure(text="No associate records found.")

    def _update_summary(self, filtered: List[AssociateRecord]) -> None:
        total = len(self.records)
        visible = len(filtered)
        active = sum(1 for record in filtered if record.is_active)
        inactive = visible - active
        expiring = sum(1 for record in filtered if record.is_expiring_soon)
        expired = sum(1 for record in filtered if record.is_expired)

        summary = (
            f"Showing {visible} of {total} associates | Active: {active} | "
            f"Inactive: {inactive} | Expiring soon: {expiring} | Expired: {expired}"
        )
        self.summary_label.configure(text=summary)

    def _update_file_label(self) -> None:
        resolved = self.associate_service.resolve_associate_path(self._associate_path)
        if not resolved:
            self.file_label.configure(text="Associate CSV: (not found)")
            return

        try:
            stat_info = resolved.stat()
            modified = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
            display = f"Associate CSV: {resolved} (updated {modified})"
        except OSError:
            display = f"Associate CSV: {resolved}"
        self.file_label.configure(text=display)

    # ------------------------------------------------------------------
    # Actions
    def open_current_file(self) -> None:
        resolved = self.associate_service.resolve_associate_path(self._associate_path)
        if not resolved:
            messagebox.showwarning("File Not Found", "Associate CSV path could not be resolved.")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(resolved)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                os.system(f"open '{resolved}'")
            else:
                os.system(f"xdg-open '{resolved}'")
        except Exception as exc:
            logger.error(f"Failed to open associate CSV: {exc}")
            messagebox.showerror("Open Failed", f"Could not open file:\n{exc}")

    def export_filtered(self) -> None:
        if not self.filtered_records:
            messagebox.showinfo("No Data", "There are no associates to export with the current filters.")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Associates",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not filename:
            return

        rows = [
            {
                "Name": record.name,
                "Transporter ID": record.transporter_id,
                "Position": record.position,
                "Qualifications": record.formatted_qualifications(),
                "ID Expiration": self._format_date(record.id_expiration),
                "Days Remaining": self._format_days(record.days_until_expiration),
                "Status": record.status.title(),
                "Personal Phone": self._format_phone(record.personal_phone),
                "Work Phone": self._format_phone(record.work_phone),
                "Email": record.email,
            }
            for record in self.filtered_records
        ]

        try:
            with open(filename, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            messagebox.showinfo("Export Complete", f"Exported {len(rows)} associates to {filename}")
        except Exception as exc:
            logger.error(f"Associate export failed: {exc}")
            messagebox.showerror("Export Failed", f"Failed to export associates:\n{exc}")

    # ------------------------------------------------------------------
    # Settings
    def update_settings(self, settings: Optional[dict]) -> None:
        self.settings = settings or {}
        self._associate_path = self.settings.get("associate_data_path")
        self.auto_refresh_enabled = bool(self.settings.get("auto_refresh_associates", False))
        self.refresh_interval_minutes = self._safe_int(
            self.settings.get("associate_refresh_interval_minutes", self.refresh_interval_minutes),
            default=self.refresh_interval_minutes,
        )
        self.refresh_data(force=True)

    def _schedule_auto_refresh(self) -> None:
        if self._auto_refresh_job is not None:
            try:
                self.parent.after_cancel(self._auto_refresh_job)
            except Exception:
                pass
            finally:
                self._auto_refresh_job = None

        if not self.auto_refresh_enabled:
            return

        interval_ms = max(1, self.refresh_interval_minutes) * 60_000
        self._auto_refresh_job = self.parent.after(interval_ms, lambda: self.refresh_data(force=True))

    # ------------------------------------------------------------------
    # Utility helpers
    @staticmethod
    def _within_days(record: AssociateRecord, days: int) -> bool:
        if record.days_until_expiration is None:
            return False
        return 0 <= record.days_until_expiration <= days

    @staticmethod
    def _format_date(value: Optional[date]) -> str:
        if not value:
            return "—"
        return value.strftime("%Y-%m-%d")

    @staticmethod
    def _format_days(value: Optional[int]) -> str:
        if value is None:
            return ""
        if value < 0:
            return f"{value}"
        return str(value)

    @staticmethod
    def _format_phone(value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return digits

    def _on_tree_motion(self, event) -> None:
        row_id = self.tree.identify_row(event.y)
        if not row_id or row_id not in self._row_tooltip_text:
            self._current_hover_item = None
            self._tooltip.cancel()
            return
        if self._current_hover_item != row_id:
            text = self._row_tooltip_text.get(row_id, "")
            self._tooltip.schedule(
                self.tree,
                text,
                x=self.tree.winfo_rootx() + event.x,
                y=self.tree.winfo_rooty() + event.y,
            )
            self._current_hover_item = row_id
        else:
            self._tooltip.move(
                x=self.tree.winfo_rootx() + event.x,
                y=self.tree.winfo_rooty() + event.y,
            )

    def _format_tooltip_text(
        self,
        record: AssociateRecord,
        *,
        expiration_text: str,
        days_text: str,
        personal_phone: str,
        work_phone: str,
    ) -> str:
        lines = [
            f"{record.name}",
            f"Transporter ID: {record.transporter_id}",
            f"Position: {record.position}",
        ]
        quals = record.formatted_qualifications() or "—"
        lines.append(f"Qualifications: {quals}")
        status_line = f"Status: {record.status.title()}"
        if record.is_expired:
            status_line += " (Expired)"
        elif record.is_expiring_soon:
            status_line += " (Expiring soon)"
        lines.append(status_line)
        expiration_details = expiration_text
        if days_text:
            expiration_details += f"  |  Days remaining: {days_text}"
        lines.append(f"ID Expiration: {expiration_details}")
        lines.append(f"Personal: {personal_phone or '—'}")
        lines.append(f"Work: {work_phone or '—'}")
        lines.append(f"Email: {record.email or '—'}")
        return "\n".join(lines)

    @staticmethod
    def _safe_int(value: object, *, default: int) -> int:
        try:
            return max(1, int(float(value)))
        except Exception:
            return default
