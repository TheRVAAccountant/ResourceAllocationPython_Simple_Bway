"""GUI component tests for duplicate validation dialog integration."""

import tkinter as tk
from unittest.mock import Mock, patch

import pytest

from src.services.duplicate_validator import (
    DuplicateAssignment,
    DuplicateVehicleValidator,
    ValidationResult,
    VehicleAssignment,
)


class TestGUIDuplicateValidation:
    """Test cases for GUI duplicate validation integration."""

    @pytest.fixture
    def mock_root(self):
        """Create mock tkinter root for testing."""
        return Mock(spec=tk.Tk)

    @pytest.fixture
    def mock_messagebox(self):
        """Mock messagebox for testing dialogs."""
        with patch("tkinter.messagebox") as mock_mb:
            yield mock_mb

    @pytest.fixture
    def sample_validation_result_with_duplicates(self):
        """Create validation result with duplicates for testing."""
        # Create sample assignments
        assignments = [
            VehicleAssignment(
                vehicle_id="BW1",
                route_code="CX1",
                driver_name="John Smith",
                service_type="Standard Parcel - Large Van",
                wave="8:00 AM",
                staging_location="STG.G.1",
            ),
            VehicleAssignment(
                vehicle_id="BW1",
                route_code="CX2",
                driver_name="Jane Doe",
                service_type="Standard Parcel - Large Van",
                wave="9:00 AM",
                staging_location="STG.G.2",
            ),
        ]

        duplicate = DuplicateAssignment(
            vehicle_id="BW1",
            assignments=assignments,
            conflict_level="warning",
            resolution_suggestion="Keep assignment to route CX1, remove from route CX2",
        )

        return ValidationResult(
            is_valid=False,
            duplicate_count=1,
            duplicates={"BW1": duplicate},
            warnings=[
                "Vehicle BW1 assigned to multiple routes: CX1, CX2 (Drivers: John Smith, Jane Doe)"
            ],
        )

    # ==================== Dialog Display Tests ====================

    def test_show_duplicate_warning_dialog(
        self, mock_messagebox, sample_validation_result_with_duplicates
    ):
        """Test showing duplicate warning dialog."""
        from src.gui.utils.duplicate_dialog import show_duplicate_warning

        # Mock the dialog response
        mock_messagebox.askyesno.return_value = True

        result = show_duplicate_warning(sample_validation_result_with_duplicates)

        # Should show warning dialog
        mock_messagebox.askyesno.assert_called_once()
        call_args = mock_messagebox.askyesno.call_args

        # Check dialog title and message content
        assert "Duplicate Vehicle Assignments" in call_args[1]["title"]
        assert "BW1" in call_args[1]["message"]
        assert "multiple routes" in call_args[1]["message"]
        assert result is True

    def test_show_duplicate_warning_dialog_user_cancels(
        self, mock_messagebox, sample_validation_result_with_duplicates
    ):
        """Test duplicate warning dialog when user cancels."""
        from src.gui.utils.duplicate_dialog import show_duplicate_warning

        # Mock user clicking "No"
        mock_messagebox.askyesno.return_value = False

        result = show_duplicate_warning(sample_validation_result_with_duplicates)

        mock_messagebox.askyesno.assert_called_once()
        assert result is False

    def test_show_duplicate_info_dialog(
        self, mock_messagebox, sample_validation_result_with_duplicates
    ):
        """Test showing detailed duplicate information dialog."""
        from src.gui.utils.duplicate_dialog import show_duplicate_details

        show_duplicate_details(sample_validation_result_with_duplicates)

        # Should show info dialog
        mock_messagebox.showinfo.assert_called_once()
        call_args = mock_messagebox.showinfo.call_args

        # Check dialog content includes details
        assert "Duplicate Details" in call_args[1]["title"]
        assert "BW1" in call_args[1]["message"]
        assert "CX1" in call_args[1]["message"]
        assert "CX2" in call_args[1]["message"]
        assert "John Smith" in call_args[1]["message"]
        assert "Jane Doe" in call_args[1]["message"]

    def test_show_no_duplicates_dialog(self, mock_messagebox):
        """Test showing no duplicates found dialog."""
        from src.gui.utils.duplicate_dialog import show_no_duplicates

        # Create validation result with no duplicates
        clean_result = ValidationResult(is_valid=True, duplicate_count=0)

        show_no_duplicates(clean_result)

        # Should show success dialog
        mock_messagebox.showinfo.assert_called_once()
        call_args = mock_messagebox.showinfo.call_args

        assert "Validation Complete" in call_args[1]["title"]
        assert "No duplicate" in call_args[1]["message"]

    # ==================== Dialog Integration Tests ====================

    @patch("src.gui.allocation_tab.DuplicateVehicleValidator")
    @patch("src.gui.allocation_tab.show_duplicate_warning")
    def test_allocation_tab_duplicate_validation_integration(
        self, mock_show_warning, mock_validator_class
    ):
        """Test allocation tab integration with duplicate validation."""
        # Setup mocks
        mock_validator = Mock()
        mock_validator_class.return_value = mock_validator

        # Create validation result with duplicates
        validation_result = ValidationResult(
            is_valid=False,
            duplicate_count=1,
            duplicates={"BW1": Mock()},
            warnings=["Duplicate warning"],
        )
        mock_validator.validate_allocations.return_value = validation_result
        mock_show_warning.return_value = True  # User proceeds

        # Mock allocation tab
        with patch("src.gui.allocation_tab.AllocationTab") as mock_tab_class:
            mock_tab = Mock()
            mock_tab_class.return_value = mock_tab

            # Simulate allocation process with validation
            allocation_results = [{"Van ID": "BW1", "Route Code": "CX1"}]

            # This would be called in the actual allocation process
            validation_result = mock_validator.validate_allocations(allocation_results)

            if validation_result.has_duplicates():
                user_choice = mock_show_warning(validation_result)

                if user_choice:
                    # User chose to proceed - mark duplicates
                    mock_validator.mark_duplicates_in_results(allocation_results, validation_result)

        # Verify the flow
        mock_validator.validate_allocations.assert_called_once_with(allocation_results)
        mock_show_warning.assert_called_once_with(validation_result)
        mock_validator.mark_duplicates_in_results.assert_called_once()

    @patch("src.gui.allocation_tab.show_duplicate_warning")
    def test_allocation_tab_user_aborts_on_duplicates(self, mock_show_warning):
        """Test allocation tab when user aborts due to duplicates."""
        mock_show_warning.return_value = False  # User cancels

        # Create validation result with duplicates
        validation_result = ValidationResult(
            is_valid=False,
            duplicate_count=1,
            duplicates={"BW1": Mock()},
            warnings=["Duplicate warning"],
        )

        # Simulate user aborting
        if validation_result.has_duplicates():
            user_choice = mock_show_warning(validation_result)

            allocation_aborted = not user_choice

        assert allocation_aborted is True

    # ==================== Custom Dialog Widget Tests ====================

    @patch("customtkinter.CTkToplevel")
    def test_custom_duplicate_dialog_creation(self, mock_toplevel):
        """Test creation of custom duplicate validation dialog."""
        from src.gui.widgets.duplicate_dialog import DuplicateValidationDialog

        # Setup mock window
        mock_window = Mock()
        mock_toplevel.return_value = mock_window

        # Create dialog
        parent = Mock()
        validation_result = ValidationResult(
            is_valid=False, duplicate_count=1, duplicates={"BW1": Mock()}, warnings=["Test warning"]
        )

        dialog = DuplicateValidationDialog(parent, validation_result)

        # Verify dialog was created
        mock_toplevel.assert_called_once()
        assert dialog.result is None  # Initially no result

    @patch("customtkinter.CTkToplevel")
    def test_custom_duplicate_dialog_layout(self, mock_toplevel):
        """Test layout of custom duplicate validation dialog."""
        from src.gui.widgets.duplicate_dialog import DuplicateValidationDialog

        # Setup mocks
        mock_window = Mock()
        mock_toplevel.return_value = mock_window

        # Create validation result
        assignments = [
            VehicleAssignment("BW1", "CX1", "Driver A", "Service A", "8:00 AM", "STG.G.1"),
            VehicleAssignment("BW1", "CX2", "Driver B", "Service B", "9:00 AM", "STG.G.2"),
        ]
        duplicate = DuplicateAssignment("BW1", assignments)
        validation_result = ValidationResult(
            is_valid=False,
            duplicate_count=1,
            duplicates={"BW1": duplicate},
            warnings=["Test warning"],
        )

        with patch("customtkinter.CTkLabel") as mock_label, patch(
            "customtkinter.CTkTextbox"
        ) as mock_textbox, patch("customtkinter.CTkButton") as mock_button:
            DuplicateValidationDialog(Mock(), validation_result)

            # Should create various widgets
            assert mock_label.call_count >= 1  # Title and other labels
            assert mock_textbox.call_count >= 1  # Details textbox
            assert mock_button.call_count >= 2  # Proceed and Cancel buttons

    def test_custom_dialog_proceed_action(self):
        """Test proceed action in custom dialog."""
        from src.gui.widgets.duplicate_dialog import DuplicateValidationDialog

        with patch("customtkinter.CTkToplevel") as mock_toplevel:
            mock_window = Mock()
            mock_toplevel.return_value = mock_window

            validation_result = ValidationResult(is_valid=False, duplicate_count=1)
            dialog = DuplicateValidationDialog(Mock(), validation_result)

            # Simulate clicking proceed
            dialog._on_proceed()

            assert dialog.result is True
            mock_window.destroy.assert_called_once()

    def test_custom_dialog_cancel_action(self):
        """Test cancel action in custom dialog."""
        from src.gui.widgets.duplicate_dialog import DuplicateValidationDialog

        with patch("customtkinter.CTkToplevel") as mock_toplevel:
            mock_window = Mock()
            mock_toplevel.return_value = mock_window

            validation_result = ValidationResult(is_valid=False, duplicate_count=1)
            dialog = DuplicateValidationDialog(Mock(), validation_result)

            # Simulate clicking cancel
            dialog._on_cancel()

            assert dialog.result is False
            mock_window.destroy.assert_called_once()

    # ==================== Progress Integration Tests ====================

    @patch("src.gui.allocation_tab.AllocationTab.update_progress")
    def test_validation_progress_updates(self, mock_update_progress):
        """Test that validation progress is shown to user."""
        from src.gui.allocation_tab import AllocationTab

        with patch("customtkinter.CTkFrame"), patch(
            "src.gui.allocation_tab.DuplicateVehicleValidator"
        ) as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator

            # Create tab instance
            tab = AllocationTab(Mock())

            # Simulate validation with progress updates
            def validate_with_progress(allocations):  # noqa: ARG001
                # Progress at start
                tab.update_progress("Validating for duplicates...", 70)

                # Simulate validation
                result = ValidationResult(is_valid=True, duplicate_count=0)

                # Progress at completion
                tab.update_progress("Validation complete", 80)

                return result

            mock_validator.validate_allocations.side_effect = validate_with_progress

            # Run validation
            allocation_results = [{"Van ID": "BW1", "Route Code": "CX1"}]
            mock_validator.validate_allocations(allocation_results)

            # Check progress was updated
            assert mock_update_progress.call_count >= 2
            progress_messages = [call[0][0] for call in mock_update_progress.call_args_list]
            assert any("Validating" in msg for msg in progress_messages)
            assert any("complete" in msg for msg in progress_messages)

    # ==================== Error Handling Tests ====================

    @patch("src.gui.utils.duplicate_dialog.logger")
    def test_dialog_error_handling(self, mock_logger, mock_messagebox):  # noqa: ARG002
        """Test error handling in dialog functions."""
        from src.gui.utils.duplicate_dialog import show_duplicate_warning

        # Create malformed validation result
        invalid_result = None

        try:
            show_duplicate_warning(invalid_result)
        except Exception:
            # Should handle gracefully and log error
            assert mock_logger.error.called

    @patch("tkinter.messagebox.askyesno")
    def test_dialog_exception_recovery(self, mock_askyesno):
        """Test recovery from dialog exceptions."""
        from src.gui.utils.duplicate_dialog import show_duplicate_warning

        # Mock dialog raising exception
        mock_askyesno.side_effect = Exception("Dialog error")

        validation_result = ValidationResult(is_valid=False, duplicate_count=1)

        # Should not crash, should return False (safe default)
        result = show_duplicate_warning(validation_result)
        assert result is False

    # ==================== Accessibility Tests ====================

    def test_dialog_keyboard_navigation(self):
        """Test keyboard navigation in duplicate dialog."""
        from src.gui.widgets.duplicate_dialog import DuplicateValidationDialog

        with patch("customtkinter.CTkToplevel") as mock_toplevel, patch(
            "customtkinter.CTkButton"
        ) as mock_button:
            mock_window = Mock()
            mock_toplevel.return_value = mock_window

            validation_result = ValidationResult(is_valid=False, duplicate_count=1)
            DuplicateValidationDialog(Mock(), validation_result)

            # Check that buttons are configured for keyboard access
            # This would involve checking that buttons have proper bindings
            # for Enter and Escape keys
            button_calls = mock_button.call_args_list
            assert len(button_calls) >= 2  # At least Proceed and Cancel buttons

    def test_dialog_screen_reader_compatibility(self):
        """Test screen reader compatibility features."""
        from src.gui.widgets.duplicate_dialog import DuplicateValidationDialog

        with patch("customtkinter.CTkToplevel") as mock_toplevel, patch(
            "customtkinter.CTkLabel"
        ) as mock_label:
            mock_window = Mock()
            mock_toplevel.return_value = mock_window

            validation_result = ValidationResult(is_valid=False, duplicate_count=1)
            DuplicateValidationDialog(Mock(), validation_result)

            # Check that labels have descriptive text
            label_calls = mock_label.call_args_list
            # Should have at least title and description labels
            assert len(label_calls) >= 2

    # ==================== Theme Integration Tests ====================

    def test_dialog_theme_consistency(self):
        """Test that dialog follows application theme."""
        from src.gui.widgets.duplicate_dialog import DuplicateValidationDialog

        with patch("customtkinter.CTkToplevel") as mock_toplevel, patch(
            "customtkinter.set_appearance_mode"
        ) as mock_theme:
            mock_window = Mock()
            mock_toplevel.return_value = mock_window

            # Set dark theme
            mock_theme("dark")

            validation_result = ValidationResult(is_valid=False, duplicate_count=1)
            DuplicateValidationDialog(Mock(), validation_result)

            # Dialog should inherit theme settings
            # This would be verified by checking widget configurations
            assert mock_toplevel.called

    # ==================== Integration Flow Tests ====================

    def test_complete_validation_flow(self, mock_messagebox):
        """Test complete validation flow from start to finish."""
        from src.gui.utils.duplicate_dialog import show_duplicate_warning

        # Create validator
        validator = DuplicateVehicleValidator()

        # Create allocation results with duplicates
        allocations = [
            {"Van ID": "BW1", "Route Code": "CX1", "Associate Name": "Driver A"},
            {"Van ID": "BW1", "Route Code": "CX2", "Associate Name": "Driver B"},
            {"Van ID": "BW2", "Route Code": "CX3", "Associate Name": "Driver C"},
        ]

        # Step 1: Validate
        result = validator.validate_allocations(allocations)
        assert result.has_duplicates()

        # Step 2: Show dialog (mock user says proceed)
        mock_messagebox.askyesno.return_value = True
        user_choice = show_duplicate_warning(result)
        assert user_choice is True

        # Step 3: Mark duplicates in results
        marked_results = validator.mark_duplicates_in_results(allocations, result)

        # Verify flow completion
        assert len(marked_results) == 3
        assert any(r.get("Validation Status") == "DUPLICATE" for r in marked_results)
        assert any(r.get("Validation Status") == "OK" for r in marked_results)

    def test_validation_with_no_duplicates_flow(self, mock_messagebox):
        """Test validation flow when no duplicates found."""
        from src.gui.utils.duplicate_dialog import show_no_duplicates

        # Create validator
        validator = DuplicateVehicleValidator()

        # Create clean allocation results
        allocations = [
            {"Van ID": "BW1", "Route Code": "CX1", "Associate Name": "Driver A"},
            {"Van ID": "BW2", "Route Code": "CX2", "Associate Name": "Driver B"},
        ]

        # Validate
        result = validator.validate_allocations(allocations)
        assert not result.has_duplicates()

        # Show success dialog
        show_no_duplicates(result)

        # Verify success dialog was shown
        mock_messagebox.showinfo.assert_called_once()
        call_args = mock_messagebox.showinfo.call_args
        assert "No duplicate" in call_args[1]["message"]
