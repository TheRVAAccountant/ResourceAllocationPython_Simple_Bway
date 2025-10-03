"""Custom duplicate validation dialog widget using CustomTkinter."""


import customtkinter as ctk
from loguru import logger

from src.services.duplicate_validator import ValidationResult


class DuplicateValidationDialog:
    """Custom dialog for duplicate vehicle validation with detailed information."""

    def __init__(self, parent, validation_result: ValidationResult):
        """
        Initialize duplicate validation dialog.

        Args:
            parent: Parent widget.
            validation_result: ValidationResult containing duplicate information.
        """
        self.parent = parent
        self.validation_result = validation_result
        self.result: bool | None = None

        # Create dialog window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Duplicate Vehicle Assignments")
        self.window.geometry("800x600")
        self.window.resizable(True, True)

        # Make dialog modal
        self.window.transient(parent)
        self.window.grab_set()

        # Center dialog on parent
        self._center_dialog()

        # Setup dialog content
        self._setup_content()

        # Bind keyboard events
        self.window.bind("<Return>", lambda _event: self._on_proceed())
        self.window.bind("<Escape>", lambda _event: self._on_cancel())

        # Focus the dialog
        self.window.focus_set()

    def _center_dialog(self):
        """Center dialog on parent window."""
        try:
            # Get parent window position and size
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            # Calculate center position
            dialog_width = 800
            dialog_height = 600
            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2

            self.window.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        except Exception as e:
            logger.warning(f"Could not center dialog: {e}")

    def _setup_content(self):
        """Setup dialog content and layout."""
        # Main container
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚠️ Duplicate Vehicle Assignments Detected",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title_label.pack(pady=(0, 20))

        # Summary
        summary_text = (
            f"Found {self.validation_result.duplicate_count} vehicles assigned to multiple routes"
        )
        summary_label = ctk.CTkLabel(main_frame, text=summary_text, font=ctk.CTkFont(size=14))
        summary_label.pack(pady=(0, 10))

        # Details frame
        details_frame = ctk.CTkFrame(main_frame)
        details_frame.pack(fill="both", expand=True, pady=(0, 20))

        # Details label
        details_label = ctk.CTkLabel(
            details_frame,
            text="Duplicate Assignment Details:",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        details_label.pack(fill="x", padx=10, pady=(10, 5))

        # Details text box
        self.details_textbox = ctk.CTkTextbox(
            details_frame, font=ctk.CTkFont(family="Courier", size=12), wrap="word"
        )
        self.details_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Populate details
        self._populate_details()

        # Recommendations frame
        if any(d.resolution_suggestion for d in self.validation_result.duplicates.values()):
            recommendations_frame = ctk.CTkFrame(main_frame)
            recommendations_frame.pack(fill="x", pady=(0, 20))

            rec_label = ctk.CTkLabel(
                recommendations_frame,
                text="💡 Recommendations:",
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
            )
            rec_label.pack(fill="x", padx=10, pady=(10, 5))

            self.recommendations_textbox = ctk.CTkTextbox(
                recommendations_frame, height=100, font=ctk.CTkFont(size=12), wrap="word"
            )
            self.recommendations_textbox.pack(fill="x", padx=10, pady=(0, 10))

            self._populate_recommendations()

        # Button frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        # Buttons
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Cancel Allocation",
            command=self._on_cancel,
            fg_color="gray",
            hover_color="darkgray",
            width=150,
        )
        self.cancel_button.pack(side="left", padx=(0, 10))

        self.proceed_button = ctk.CTkButton(
            button_frame, text="✅ Proceed Anyway", command=self._on_proceed, width=150
        )
        self.proceed_button.pack(side="right")

        # Focus proceed button by default
        self.proceed_button.focus_set()

    def _populate_details(self):
        """Populate the details textbox with duplicate information."""
        details_text = ""

        for vehicle_id, duplicate in self.validation_result.duplicates.items():
            details_text += f"Vehicle: {vehicle_id}\n"
            details_text += f"Conflict Level: {duplicate.conflict_level.upper()}\n"
            details_text += f"Number of Assignments: {len(duplicate.assignments)}\n\n"

            details_text += "Assignments:\n"
            for i, assignment in enumerate(duplicate.assignments, 1):
                details_text += f"  {i}. Route: {assignment.route_code}\n"
                details_text += f"     Driver: {assignment.driver_name}\n"
                details_text += f"     Service: {assignment.service_type}\n"
                details_text += f"     Wave: {assignment.wave}\n"
                details_text += f"     Location: {assignment.staging_location}\n"
                details_text += (
                    f"     Timestamp: {assignment.assignment_timestamp.strftime('%H:%M:%S')}\n\n"
                )

            details_text += "-" * 60 + "\n\n"

        self.details_textbox.insert("1.0", details_text)
        self.details_textbox.configure(state="disabled")  # Make read-only

    def _populate_recommendations(self):
        """Populate recommendations textbox."""
        recommendations_text = ""

        for vehicle_id, duplicate in self.validation_result.duplicates.items():
            if duplicate.resolution_suggestion:
                recommendations_text += f"Vehicle {vehicle_id}:\n"
                recommendations_text += f"{duplicate.resolution_suggestion}\n\n"

        if recommendations_text:
            self.recommendations_textbox.insert("1.0", recommendations_text)
            self.recommendations_textbox.configure(state="disabled")  # Make read-only

    def _on_proceed(self):
        """Handle proceed button click."""
        self.result = True
        self.window.destroy()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = False
        self.window.destroy()

    def show(self) -> bool:
        """
        Show dialog and wait for user response.

        Returns:
            True if user chose to proceed, False if cancelled.
        """
        # Wait for dialog to close
        self.window.wait_window()

        # Return result (None means window was closed without button)
        return self.result if self.result is not None else False


def show_duplicate_validation_dialog(parent, validation_result: ValidationResult) -> bool:
    """
    Show duplicate validation dialog and return user choice.

    Args:
        parent: Parent widget.
        validation_result: ValidationResult containing duplicate information.

    Returns:
        True if user chooses to proceed, False if cancelled.
    """
    try:
        dialog = DuplicateValidationDialog(parent, validation_result)
        return dialog.show()
    except Exception as e:
        logger.error(f"Error showing duplicate validation dialog: {e}")
        return False  # Safe default
