"""Read-only service for Data Management tab to load vehicle/driver datasets.

This service aligns the GUI with the GAS-compatible workflow by loading
Vehicles from the Daily Summary Log ("Vehicle Status" sheet) and, when
available, enrichment from the "Vehicle Log" sheet. It is intentionally
non-invasive and does not write to Excel files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Optional

import pandas as pd
from loguru import logger


@dataclass
class _CacheEntry:
    df: pd.DataFrame
    ts: float


class DataManagementService:
    """Lightweight Excel reader with short-lived caching for UI responsiveness."""

    def __init__(self, cache_ttl_seconds: int = 15):
        self.cache_ttl = cache_ttl_seconds
        self._cache: dict[str, _CacheEntry] = {}

    # ---------- Path resolution ----------
    def resolve_daily_summary_path(self, explicit_path: Optional[str] = None) -> Optional[str]:
        """Resolve a usable Daily Summary Log path.

        Priority: explicit -> config/settings.json default (if enabled) -> inputs/Daily Summary Log 2025.xlsx
        """
        if explicit_path:
            p = Path(explicit_path)
            if p.exists():
                return str(p)

        settings_path = Path("config/settings.json")
        try:
            if settings_path.exists():
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("use_default_daily_summary"):
                    path = data.get("default_daily_summary_path", "")
                    if path and Path(path).exists():
                        return str(Path(path))
        except Exception as e:
            logger.debug(f"DataManagementService settings read failed: {e}")

        candidate = Path("inputs") / "Daily Summary Log 2025.xlsx"
        if candidate.exists():
            return str(candidate)
        return None

    # ---------- Readers ----------
    def load_vehicle_status(self, daily_summary_path: Optional[str]) -> Optional[pd.DataFrame]:
        """Load Vehicle Status sheet as DataFrame (raw columns).

        Returns None on failure. Short-lived cache keyed by file path.
        """
        path = self.resolve_daily_summary_path(daily_summary_path)
        if not path:
            return None

        key = f"veh_status::{path}"
        now = time()
        entry = self._cache.get(key)
        if entry and (now - entry.ts) < self.cache_ttl:
            return entry.df

        try:
            df = pd.read_excel(path, sheet_name="Vehicle Status")
            self._cache[key] = _CacheEntry(df=df, ts=now)
            return df
        except Exception as e:
            logger.debug(f"Failed to read Vehicle Status from {path}: {e}")
            return None

    def load_vehicle_log(self, daily_summary_path: Optional[str]) -> Optional[pd.DataFrame]:
        """Load Vehicle Log sheet as DataFrame (if present)."""
        path = self.resolve_daily_summary_path(daily_summary_path)
        if not path:
            return None

        key = f"veh_log::{path}"
        now = time()
        entry = self._cache.get(key)
        if entry and (now - entry.ts) < self.cache_ttl:
            return entry.df

        try:
            df = pd.read_excel(path, sheet_name="Vehicle Log")
            self._cache[key] = _CacheEntry(df=df, ts=now)
            return df
        except Exception as e:
            logger.debug(f"Vehicle Log not available or failed to read from {path}: {e}")
            return None
