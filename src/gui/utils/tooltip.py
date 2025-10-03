"""Reusable tooltip helper for hover details in CustomTkinter UIs."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk


class HoverTooltip:
    """Delayed tooltip that follows the cursor with lightweight styling."""

    def __init__(self, master: ctk.CTkBaseClass, *, delay_ms: int = 200, max_width: int = 360):
        self._master = master
        self._delay = delay_ms
        self._max_width = max_width
        self._after_id: Optional[str] = None
        self._tooltip: Optional[ctk.CTkToplevel] = None
        self._label: Optional[ctk.CTkLabel] = None
        self._current_text: str = ""

    # ------------------------------------------------------------------
    # Public API
    def schedule(self, widget: ctk.CTkBaseClass, text: str, *, x: int, y: int) -> None:
        """Schedule tooltip display after delay."""
        self.cancel()
        self._current_text = text or ""
        if not self._current_text.strip():
            return
        self._after_id = widget.after(
            self._delay,
            lambda: self._show_at(widget=widget, x=x, y=y),
        )

    def move(self, *, x: int, y: int) -> None:
        """Reposition tooltip if visible."""
        if self._tooltip is None:
            return
        self._place_window(x, y)

    def cancel(self) -> None:
        """Cancel pending tooltip or hide active tooltip."""
        if self._after_id and self._master:
            try:
                self._master.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None
        self.hide()

    def hide(self) -> None:
        if self._tooltip is not None:
            try:
                self._tooltip.destroy()
            except Exception:
                pass
        self._tooltip = None
        self._label = None

    # ------------------------------------------------------------------
    # Internal helpers
    def _show_at(self, *, widget: ctk.CTkBaseClass, x: int, y: int) -> None:
        if self._tooltip is not None:
            self.hide()
        self._tooltip = ctk.CTkToplevel(widget)
        self._tooltip.overrideredirect(True)
        self._tooltip.attributes("-topmost", True)
        self._tooltip.configure(fg_color=("#1f1f1f", "#1f1f1f"))

        self._label = ctk.CTkLabel(
            self._tooltip,
            text=self._current_text,
            justify="left",
            corner_radius=6,
            fg_color=("#1f1f1f", "#1f1f1f"),
            text_color=("#f2f2f2", "#f2f2f2"),
            font=ctk.CTkFont(size=12),
            wraplength=self._max_width,
            padx=12,
            pady=8,
        )
        self._label.pack()
        self._place_window(x, y)

    def _place_window(self, x: int, y: int) -> None:
        if self._tooltip is None:
            return
        offset_x = 18
        offset_y = 18
        screen_width = self._tooltip.winfo_screenwidth()
        screen_height = self._tooltip.winfo_screenheight()
        self._tooltip.update_idletasks()
        width = self._tooltip.winfo_width()
        height = self._tooltip.winfo_height()

        new_x = x + offset_x
        new_y = y + offset_y

        if new_x + width > screen_width - 10:
            new_x = screen_width - width - 10
        if new_y + height > screen_height - 10:
            new_y = screen_height - height - 10

        self._tooltip.geometry(f"{width}x{height}+{int(new_x)}+{int(new_y)}")
