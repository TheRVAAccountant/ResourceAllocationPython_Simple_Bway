"""Duplicate validation dialog utilities for GUI integration."""

import tkinter as tk
from tkinter import messagebox
from typing import Optional
from loguru import logger

from src.services.duplicate_validator import ValidationResult


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
        
        # Build warning message
        message = f"⚠️ Found {validation_result.duplicate_count} vehicles assigned to multiple routes:\n\n"
        
        for vehicle_id, duplicate in validation_result.duplicates.items():
            routes = [a.route_code for a in duplicate.assignments]
            drivers = [a.driver_name for a in duplicate.assignments]
            message += f"• Vehicle {vehicle_id}: Routes {', '.join(routes)} (Drivers: {', '.join(drivers)})\n"
        
        message += "\n❓ Do you want to proceed with the allocation anyway?\n"
        message += "\n✅ Click 'Yes' to continue and mark duplicates in results"
        message += "\n❌ Click 'No' to cancel and review assignments"
        
        # Show dialog
        return messagebox.askyesno(
            title="Duplicate Vehicle Assignments Detected",
            message=message,
            icon="warning"
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
        
        # Build detailed message
        message = f"Duplicate Vehicle Assignment Details\n"
        message += f"=" * 40 + "\n\n"
        
        for vehicle_id, duplicate in validation_result.duplicates.items():
            message += f"Vehicle: {vehicle_id}\n"
            message += f"Conflict Level: {duplicate.conflict_level.upper()}\n"
            message += f"Number of Assignments: {len(duplicate.assignments)}\n\n"
            
            message += "Assignments:\n"
            for i, assignment in enumerate(duplicate.assignments, 1):
                message += f"  {i}. Route: {assignment.route_code}\n"
                message += f"     Driver: {assignment.driver_name}\n"
                message += f"     Service: {assignment.service_type}\n"
                message += f"     Wave: {assignment.wave}\n"
                message += f"     Location: {assignment.staging_location}\n"
                message += f"     Time: {assignment.assignment_timestamp.strftime('%H:%M:%S')}\n\n"
            
            if duplicate.resolution_suggestion:
                message += f"Suggested Resolution:\n{duplicate.resolution_suggestion}\n"
            
            message += "-" * 40 + "\n\n"
        
        # Show info dialog
        messagebox.showinfo(
            title="Duplicate Assignment Details",
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error showing duplicate details dialog: {e}")


def show_no_duplicates(validation_result: ValidationResult) -> None:
    """
    Show success dialog when no duplicates are found.
    
    Args:
        validation_result: ValidationResult with no duplicates.
    """
    try:
        message = "✅ Validation Complete!\n\n"
        message += "No duplicate vehicle assignments detected.\n"
        message += "All vehicles are assigned to unique routes."
        
        messagebox.showinfo(
            title="Validation Complete - No Duplicates",
            message=message
        )
        
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
    
    summary = f"⚠️ {validation_result.duplicate_count} duplicate assignment(s) found:\n"
    
    for vehicle_id, duplicate in validation_result.duplicates.items():
        routes = [a.route_code for a in duplicate.assignments]
        summary += f"• {vehicle_id}: {', '.join(routes)}\n"
    
    return summary