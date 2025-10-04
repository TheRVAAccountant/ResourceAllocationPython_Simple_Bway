"""Duplicate validation dialog utilities for GUI integration."""

import tkinter as tk

from loguru import logger

from src.services.duplicate_validator import ValidationResult

# Ensure ``tkinter.messagebox`` exists even in headless environments so pytest patches work.
try:  # pragma: no cover - defensive in case tkinter behaves differently
    from tkinter import messagebox as _messagebox
except ImportError:  # pragma: no cover - tkinter missing would already break GUI usage
    _messagebox = None

if _messagebox is not None and not hasattr(tk, "messagebox"):
    tk.messagebox = _messagebox


def _get_messagebox():
    """Return the active tkinter messagebox module (patched or real)."""
    if hasattr(tk, "messagebox"):
        return tk.messagebox
    return _messagebox


def _normalize_assignments(duplicate) -> list:
    """Safely extract assignment objects from a duplicate entry."""
    raw_assignments = getattr(duplicate, "assignments", []) or []

    if isinstance(raw_assignments, dict):
        raw_assignments = raw_assignments.values()

    try:
        return list(raw_assignments)
    except Exception:  # pragma: no cover - defensive against mocks in tests
        return []


def show_duplicate_warning(validation_result: ValidationResult) -> bool:
    """
    Show duplicate vehicle assignment warning dialog.

    Args:
        validation_result: ValidationResult containing duplicate information.

    Returns:
        True if user chooses to proceed, False if user cancels.
    """
    try:
        if not validation_result or not validation_result.has_duplicates():
            return True

        duplicates = validation_result.duplicates or {}
        messagebox = _get_messagebox()

        # Build warning message
        message = (
            f"⚠️ Found {validation_result.duplicate_count} vehicles assigned "
            f"to multiple routes:\n\n"
        )

        for vehicle_id, duplicate in duplicates.items():
            assignments = _normalize_assignments(duplicate)
            routes = [getattr(a, "route_code", "Unknown") for a in assignments]
            drivers = [getattr(a, "driver_name", "Unknown") for a in assignments]
            message += (
                f"• Vehicle {vehicle_id}: Routes {', '.join(routes)} "
                f"(Drivers: {', '.join(drivers)})\n"
            )

        message += "\n❓ Do you want to proceed with the allocation anyway?\n"
        message += "\n✅ Click 'Yes' to continue and mark duplicates in results"
        message += "\n❌ Click 'No' to cancel and review assignments"

        if messagebox is None:
            logger.warning("tkinter.messagebox unavailable; defaulting to proceed=False")
            return False

        # Show dialog
        return messagebox.askyesno(
            title="Duplicate Vehicle Assignments Detected", message=message, icon="warning"
        )

    except Exception as e:
        logger.error(f"Error showing duplicate warning dialog: {e}")
        return False  # Safe default - don't proceed on error


def show_duplicate_details(validation_result: ValidationResult) -> None:
    """
    Show detailed duplicate information dialog.

    Args:
        validation_result: ValidationResult containing duplicate information.
    """
    try:
        if not validation_result or not validation_result.has_duplicates():
            return

        duplicates = validation_result.duplicates or {}
        messagebox = _get_messagebox()

        # Build detailed message
        message = "Duplicate Vehicle Assignment Details\n"
        message += "=" * 40 + "\n\n"

        for vehicle_id, duplicate in duplicates.items():
            conflict_level = getattr(duplicate, "conflict_level", "warning") or "warning"
            assignments = _normalize_assignments(duplicate)

            message += f"Vehicle: {vehicle_id}\n"
            message += f"Conflict Level: {str(conflict_level).upper()}\n"
            message += f"Number of Assignments: {len(assignments)}\n\n"

            message += "Assignments:\n"
            for i, assignment in enumerate(assignments, 1):
                message += f"  {i}. Route: {getattr(assignment, 'route_code', 'Unknown')}\n"
                message += f"     Driver: {getattr(assignment, 'driver_name', 'Unknown')}\n"
                message += f"     Service: {getattr(assignment, 'service_type', 'Unknown')}\n"
                message += f"     Wave: {getattr(assignment, 'wave', 'Unknown')}\n"
                message += f"     Location: {getattr(assignment, 'staging_location', 'Unknown')}\n"

                timestamp = getattr(assignment, "assignment_timestamp", None)
                if timestamp is not None and hasattr(timestamp, "strftime"):
                    formatted_time = timestamp.strftime("%H:%M:%S")
                else:
                    formatted_time = "Unknown"
                message += f"     Time: {formatted_time}\n\n"

            resolution = getattr(duplicate, "resolution_suggestion", None)
            if resolution:
                message += f"Suggested Resolution:\n{resolution}\n"

            message += "-" * 40 + "\n\n"

        if messagebox is None:
            logger.warning("tkinter.messagebox unavailable; skipping duplicate details dialog")
            return

        # Show info dialog
        messagebox.showinfo(title="Duplicate Details", message=message)

    except Exception as e:
        logger.error(f"Error showing duplicate details dialog: {e}")


def show_no_duplicates(_validation_result: ValidationResult) -> None:
    """
    Show success dialog when no duplicates are found.

    Args:
        validation_result: ValidationResult with no duplicates.
    """
    try:
        message = "✅ Validation Complete!\n\n"
        message += "No duplicate vehicle assignments detected.\n"
        message += "All vehicles are assigned to unique routes."

        messagebox = _get_messagebox()

        if messagebox is None:
            logger.warning("tkinter.messagebox unavailable; skipping no-duplicates dialog")
            return

        messagebox.showinfo(title="Validation Complete - No Duplicates", message=message)

    except Exception as e:
        logger.error(f"Error showing no duplicates dialog: {e}")


def format_duplicate_summary(validation_result: ValidationResult) -> str:
    """
    Format duplicate validation result as summary string.

    Args:
        validation_result: ValidationResult to format.

    Returns:
        Formatted summary string.
    """
    if not validation_result.has_duplicates():
        return "✅ No duplicate assignments detected"

    duplicates = validation_result.duplicates or {}

    summary = f"⚠️ {validation_result.duplicate_count} duplicate assignment(s) found:\n"

    for vehicle_id, duplicate in duplicates.items():
        assignments = _normalize_assignments(duplicate)
        routes = [getattr(a, "route_code", "Unknown") for a in assignments]
        summary += f"• {vehicle_id}: {', '.join(routes)}\n"

    return summary
