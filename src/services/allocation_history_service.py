"""Persistent allocation history service for tracking allocations across sessions.

This service provides centralized storage and retrieval of allocation history,
supporting both GASCompatibleAllocator and AllocationEngine workflows.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from src.core.base_service import BaseService
from src.models.allocation import AllocationResult


class AllocationHistoryService(BaseService):
    """Service for persisting allocation history to disk.

    Features:
    - JSON-based storage in config/allocation_history.json
    - Automatic rotation (configurable max entries and retention days)
    - Cross-engine support (GAS and general allocation engines)
    - Thread-safe operations
    """

    DEFAULT_MAX_ENTRIES = 100
    DEFAULT_RETENTION_DAYS = 90
    HISTORY_FILE = Path("config/allocation_history.json")

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize allocation history service.

        Args:
            config: Optional configuration dict with keys:
                - max_entries: Maximum number of history entries (default: 100)
                - retention_days: Days to retain history (default: 90)
                - auto_cleanup: Auto-clean old entries on save (default: True)
                - detailed_storage: Store full results vs summary (default: False)
        """
        super().__init__(config or {})

        # Configuration
        self.max_entries = self.config.get("max_entries", self.DEFAULT_MAX_ENTRIES)
        self.retention_days = self.config.get("retention_days", self.DEFAULT_RETENTION_DAYS)
        self.auto_cleanup = self.config.get("auto_cleanup", True)
        self.detailed_storage = self.config.get("detailed_storage", False)

        # Ensure config directory exists
        self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file if it doesn't exist
        if not self.HISTORY_FILE.exists():
            self._write_history([])

    def initialize(self) -> None:
        """Initialize the service (required by BaseService)."""
        logger.info(
            f"AllocationHistoryService initialized (max_entries={self.max_entries}, "
            f"retention_days={self.retention_days})"
        )

        # Auto-cleanup on initialization if enabled
        if self.auto_cleanup:
            removed = self.clear_old_entries()
            if removed > 0:
                logger.info(f"Cleaned up {removed} old history entries")

    def validate(self) -> bool:
        """Validate service configuration.

        Returns:
            True if configuration is valid.
        """
        if self.max_entries < 1:
            logger.error("max_entries must be >= 1")
            return False

        if self.retention_days < 1:
            logger.error("retention_days must be >= 1")
            return False

        return True

    def cleanup(self) -> None:
        """Cleanup service resources."""
        logger.debug("AllocationHistoryService cleanup complete")

    def save_allocation(
        self,
        result: AllocationResult,
        engine_name: str,
        files: dict[str, str] | None = None,
        duplicate_conflicts: int = 0,
        error: str | None = None,
    ) -> None:
        """Save allocation result to persistent history.

        Args:
            result: AllocationResult from allocation engine
            engine_name: Name of engine used ("GASCompatibleAllocator" or "AllocationEngine")
            files: Dict of file paths used (day_of_ops, daily_routes, vehicle_status)
            duplicate_conflicts: Number of duplicate vehicle conflicts detected
            error: Error message if allocation failed
        """
        try:
            # Load existing history
            history = self._read_history()

            # Extract metrics from result
            total_routes = None
            allocated_count = None
            unallocated_count = None
            allocation_rate = None
            total_drivers = None
            active_drivers = None
            processing_time = None

            # Handle metadata first
            metadata = getattr(result, "metadata", {}) or {}
            if metadata:
                total_routes = metadata.get("total_routes")
                allocated_count = metadata.get("allocated_count", metadata.get("total_assigned"))
                unallocated_count = metadata.get(
                    "unallocated_count", metadata.get("total_unassigned")
                )
                allocation_rate = metadata.get("allocation_rate")
                total_drivers = metadata.get("total_drivers")
                active_drivers = metadata.get("active_drivers")
                processing_time = metadata.get("processing_time_seconds")

            # Metrics object fallback
            metrics_obj = getattr(result, "metrics", None)
            if metrics_obj is not None:
                total_routes = (
                    total_routes
                    if total_routes is not None
                    else getattr(metrics_obj, "total_vehicles", None)
                )
                allocated_count = (
                    allocated_count
                    if allocated_count is not None
                    else getattr(metrics_obj, "allocated_vehicles", None)
                )
                unallocated_count = (
                    unallocated_count
                    if unallocated_count is not None
                    else getattr(metrics_obj, "unallocated_vehicles", None)
                )
                allocation_rate = (
                    allocation_rate
                    if allocation_rate is not None
                    else (float(getattr(metrics_obj, "allocation_rate", 0)) * 100)
                )
                total_drivers = (
                    total_drivers
                    if total_drivers is not None
                    else getattr(metrics_obj, "total_drivers", None)
                )
                active_drivers = (
                    active_drivers
                    if active_drivers is not None
                    else getattr(metrics_obj, "active_drivers", None)
                )
                processing_time = (
                    processing_time
                    if processing_time is not None
                    else getattr(metrics_obj, "processing_time", None)
                )

            # Fall back to allocations data when needed
            if hasattr(result, "allocations") and result.allocations:
                if total_routes is None:
                    total_routes = len(result.allocations)
                if allocated_count is None:
                    allocated_count = sum(len(vids) for vids in result.allocations.values())
                if active_drivers is None:
                    active_drivers = len([vids for vids in result.allocations.values() if vids])
                if total_drivers is None:
                    total_drivers = len(result.allocations)
                if unallocated_count is None and hasattr(result, "unallocated_vehicles"):
                    unallocated_count = len(result.unallocated_vehicles)

            if unallocated_count is None and hasattr(result, "unallocated_vehicles"):
                unallocated_count = len(result.unallocated_vehicles)

            if allocated_count is None:
                allocated_count = 0
            if total_routes is None:
                total_routes = 0
            if unallocated_count is None:
                unallocated_count = 0
            if total_drivers is None:
                total_drivers = 0
            if active_drivers is None:
                active_drivers = 0

            if allocation_rate is None:
                denominator = allocated_count + unallocated_count
                allocation_rate = (allocated_count / denominator * 100) if denominator > 0 else 0.0

            if processing_time is None:
                processing_time = 0.0

            # Create history entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "engine": engine_name,
                "request_id": result.request_id if hasattr(result, "request_id") else "UNKNOWN",
                "status": result.status.value
                if hasattr(result.status, "value")
                else str(result.status)
                if hasattr(result, "status")
                else "UNKNOWN",
                "total_routes": total_routes,
                "allocated_count": allocated_count,
                "unallocated_count": unallocated_count,
                "allocation_rate": round(allocation_rate, 2),
                "files": files or {},
                "duplicate_conflicts": duplicate_conflicts,
                "error": error,
                "total_drivers": int(total_drivers),
                "active_drivers": int(active_drivers),
                "processing_time_seconds": float(processing_time),
            }

            # Optionally store detailed results
            if self.detailed_storage and hasattr(result, "metadata"):
                detailed = result.metadata.get("detailed_results", [])
                # Limit detailed storage size (first 50 results)
                entry["detailed_results"] = detailed[:50] if detailed else []

            # Add to history (newest first)
            history.insert(0, entry)

            # Auto-cleanup if enabled
            if self.auto_cleanup:
                history = self._apply_retention_rules(history)

            # Write back to disk
            self._write_history(history)

            logger.info(
                f"Saved allocation to history: {entry['request_id']} "
                f"({allocated_count}/{total_routes} allocated, {allocation_rate:.1f}%)"
            )

        except Exception as e:
            logger.error(f"Failed to save allocation history: {e}")
            # Don't raise - history saving should not block allocations

    def get_history(
        self, limit: int = 10, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve allocation history with optional filtering.

        Args:
            limit: Maximum number of entries to return (default: 10)
            filters: Optional filters:
                - status: Filter by status ("SUCCESS", "ERROR", etc.)
                - engine: Filter by engine name
                - date_from: Filter by date (ISO format string)
                - date_to: Filter by date (ISO format string)
                - has_duplicates: Filter entries with duplicate conflicts
                - has_errors: Filter entries with errors

        Returns:
            List of history entries formatted for GUI display (newest first).
        """
        try:
            history = self._read_history()

            # Apply filters if provided
            if filters:
                history = self._apply_filters(history, filters)

            # Format entries for GUI display
            formatted_history = []
            for entry in history[:limit]:
                dup_count, dup_details = self._parse_duplicate_conflicts(
                    entry.get("duplicate_conflicts")
                )
                formatted_entry = {
                    "allocation_id": entry.get("request_id", "UNKNOWN"),
                    "timestamp": entry.get("timestamp", ""),
                    "engine_name": entry.get("engine", "Unknown"),
                    "status": entry.get("status", "UNKNOWN"),
                    "metrics": {
                        "total_routes": entry.get("total_routes", 0),
                        "allocated_vehicles": entry.get("allocated_count", 0),
                        "unallocated_vehicles": entry.get("unallocated_count", 0),
                        "success_rate": entry.get("allocation_rate", 0.0)
                        / 100.0,  # Convert to 0-1 range
                        "processing_time": entry.get("processing_time_seconds", 0.0),
                    },
                    "files": entry.get("files", {}),
                    "duplicate_conflicts": dup_count,
                    "duplicate_conflict_details": dup_details,
                    "error": entry.get("error"),
                    "total_routes": entry.get("total_routes", 0),
                    "allocated_count": entry.get("allocated_count", 0),
                    "allocation_rate": entry.get("allocation_rate", 0.0),
                    "total_drivers": entry.get("total_drivers", 0),
                    "active_drivers": entry.get("active_drivers", 0),
                    "processing_time_seconds": entry.get("processing_time_seconds", 0.0),
                }
                formatted_entry["duplicate_conflicts_count"] = dup_count
                formatted_history.append(formatted_entry)

            return formatted_history

        except Exception as e:
            logger.error(f"Failed to read allocation history: {e}")
            return []

    def get_latest_summary(self) -> dict[str, Any] | None:
        """Return the most recent history entry (formatted)."""
        history = self.get_history(limit=1)
        return history[0] if history else None

    def get_statistics(self, days: int = 7) -> dict[str, Any]:
        """Get allocation statistics for recent history.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dict with statistics:
                - total_allocations: Total number of allocations
                - avg_allocation_rate: Average allocation rate
                - total_routes: Total routes allocated
                - success_count: Number of successful allocations
                - error_count: Number of failed allocations
                - duplicate_count: Total duplicate conflicts
        """
        try:
            # Get history for specified days
            cutoff = datetime.now() - timedelta(days=days)
            history = self._read_history()

            # Filter by date
            recent = [e for e in history if datetime.fromisoformat(e["timestamp"]) >= cutoff]

            if not recent:
                return {
                    "total_allocations": 0,
                    "success_rate": 0.0,
                    "avg_allocation_rate": 0.0,
                    "total_routes_allocated": 0,
                    "total_vehicles_allocated": 0,
                    "allocations_with_duplicates": 0,
                    "allocations_with_errors": 0,
                }

            # Calculate statistics
            total_allocations = len(recent)
            avg_rate = sum(e["allocation_rate"] for e in recent) / total_allocations
            total_routes = sum(e["total_routes"] for e in recent)
            total_allocated = sum(e["allocated_count"] for e in recent)
            success_count = sum(1 for e in recent if e["error"] is None)
            error_count = sum(1 for e in recent if e["error"] is not None)
            duplicate_count = sum(
                self._duplicate_conflict_count(e.get("duplicate_conflicts")) for e in recent
            )

            return {
                "total_allocations": total_allocations,
                "success_rate": round(success_count / total_allocations, 3)
                if total_allocations > 0
                else 0.0,
                "avg_allocation_rate": round(avg_rate, 2),
                "total_routes_allocated": total_routes,
                "total_vehicles_allocated": total_allocated,
                "allocations_with_duplicates": duplicate_count,
                "allocations_with_errors": error_count,
            }

        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
            return {}

    def clear_old_entries(self) -> int:
        """Remove entries older than retention_days.

        Returns:
            Number of entries removed.
        """
        try:
            history = self._read_history()
            original_count = len(history)

            # Apply retention rules
            history = self._apply_retention_rules(history)

            # Write back
            self._write_history(history)

            removed = original_count - len(history)
            if removed > 0:
                logger.info(f"Removed {removed} old history entries")

            return removed

        except Exception as e:
            logger.error(f"Failed to clear old entries: {e}")
            return 0

    def clear_all(self) -> None:
        """Clear all history entries (use with caution)."""
        try:
            self._write_history([])
            logger.warning("Cleared all allocation history")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")

    # -------- Private Methods --------

    def _duplicate_conflict_count(self, value: Any) -> int:
        """Return a normalized duplicate conflict count from stored data."""
        count, _ = self._parse_duplicate_conflicts(value)
        return count

    def _parse_duplicate_conflicts(self, value: Any) -> tuple[int, list[Any]]:
        """Normalize duplicate conflict representations to count + details."""
        if value is None:
            return 0, []

        if isinstance(value, int):
            return max(value, 0), []

        if isinstance(value, list | tuple | set):
            details = [item for item in value if item is not None]
            return len(details), details

        if isinstance(value, dict):
            count = value.get("count")
            details_source = value.get("details") or value.get("items")
            details: list[Any] = []
            if isinstance(details_source, list | tuple | set):
                details = [item for item in details_source if item is not None]
            elif details_source is not None:
                details = [details_source]
            elif value:
                details = [value]

            if isinstance(count, int):
                return max(count, 0), details

            if details:
                return len(details), details

            return len(value), [value]

        # Fallback for string or other scalar representations
        return 1, [value]

    def _read_history(self) -> list[dict[str, Any]]:
        """Read history from disk."""
        try:
            if not self.HISTORY_FILE.exists():
                return []

            with open(self.HISTORY_FILE, encoding="utf-8") as f:
                data = json.load(f)

            # Handle legacy format or corrupted data
            if not isinstance(data, list):
                logger.warning("Invalid history format, resetting")
                return []

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted history file: {e}, resetting")
            return []
        except Exception as e:
            logger.error(f"Failed to read history: {e}")
            return []

    def _write_history(self, history: list[dict[str, Any]]) -> None:
        """Write history to disk."""
        try:
            with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to write history: {e}")
            raise

    def _apply_retention_rules(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply retention rules (max entries and date cutoff)."""
        # Filter by date
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        history = [e for e in history if datetime.fromisoformat(e["timestamp"]) >= cutoff]

        # Limit by max entries
        if len(history) > self.max_entries:
            history = history[: self.max_entries]

        return history

    def _apply_filters(
        self, history: list[dict[str, Any]], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Apply filters to history entries."""
        filtered = history

        # Status filter
        if "status" in filters:
            status = filters["status"].upper()
            filtered = [e for e in filtered if e["status"] == status]

        # Engine filter
        if "engine" in filters:
            engine = filters["engine"]
            filtered = [e for e in filtered if e["engine"] == engine]

        # Date range filters
        if "date_from" in filters:
            date_from = datetime.fromisoformat(filters["date_from"])
            filtered = [e for e in filtered if datetime.fromisoformat(e["timestamp"]) >= date_from]

        if "date_to" in filters:
            date_to = datetime.fromisoformat(filters["date_to"])
            filtered = [e for e in filtered if datetime.fromisoformat(e["timestamp"]) <= date_to]

        # Duplicate conflicts filter
        if filters.get("has_duplicates"):
            filtered = [
                e
                for e in filtered
                if self._duplicate_conflict_count(e.get("duplicate_conflicts")) > 0
            ]

        # Errors filter
        if filters.get("has_errors"):
            filtered = [e for e in filtered if e.get("error") is not None]

        return filtered
