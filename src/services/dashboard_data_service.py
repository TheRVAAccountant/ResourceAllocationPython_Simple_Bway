"""Read-only service to provide dashboard metrics from Excel sources.

This service is intentionally non-invasive. It reads the selected Daily
Summary Log (Vehicle Status sheet) and Daily Routes file to compute basic
counts for the dashboard without altering any existing application flow.
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
    value: int
    timestamp: float


class DashboardDataService:
    """Lightweight reader for dashboard metrics.

    - Resolves the Daily Summary Log path from (in order):
      1) Explicit argument
      2) config/settings.json if use_default_daily_summary is true
      3) inputs/Daily Summary Log 2025.xlsx if present
    - Safely reads Excel sheets with defensive fallbacks.
    - Caches results briefly to avoid repeated disk reads while the
      status bar triggers periodic dashboard refreshes.
    """

    def __init__(self, cache_ttl_seconds: int = 15):
        self.cache_ttl = cache_ttl_seconds
        self._veh_cache: dict[str, _CacheEntry] = {}
        self._drv_cache: dict[str, _CacheEntry] = {}

    # ---------- Path resolution ----------
    def resolve_daily_summary_path(self, explicit_path: Optional[str] = None) -> Optional[str]:
        """Resolve a usable Daily Summary Log path."""
        # 1) Explicit
        if explicit_path:
            p = Path(explicit_path)
            if p.exists():
                return str(p)

        # 2) Settings file default
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
            logger.debug(f"DashboardDataService settings read failed: {e}")

        # 3) Conventional inputs location
        candidate = Path("inputs") / "Daily Summary Log 2025.xlsx"
        if candidate.exists():
            return str(candidate)

        return None

    # ---------- Metrics readers ----------
    def total_operational_vehicles(self, daily_summary_path: Optional[str]) -> Optional[int]:
        """Count operational vehicles from Vehicle Status sheet.

        Returns None on any issue (missing file/sheet/columns).
        Caches for a short TTL.
        """
        path = self.resolve_daily_summary_path(daily_summary_path)
        if not path:
            return None

        # Cache check
        now = time()
        cache = self._veh_cache.get(path)
        if cache and (now - cache.timestamp) < self.cache_ttl:
            return cache.value

        try:
            df = pd.read_excel(path, sheet_name="Vehicle Status")
        except Exception as e:
            logger.debug(f"Vehicle Status read failed from {path}: {e}")
            return None

        # Column normalization
        cols = {c.lower().strip(): c for c in df.columns}
        van_col = cols.get("van id") or cols.get("vehicle id")
        type_col = cols.get("type") or cols.get("vehicle type")
        op_col = cols.get("opnal? y/n") or cols.get("operational")

        if not (van_col and op_col):
            logger.debug("Vehicle Status missing required columns (Van ID, Opnal? Y/N)")
            return None

        try:
            oper = df[df[op_col].astype(str).str.upper() == "Y"]
            if van_col not in oper.columns:
                return None
            count = int(oper[van_col].dropna().astype(str).str.strip().nunique())
        except Exception as e:
            logger.debug(f"Vehicle count computation failed: {e}")
            return None

        self._veh_cache[path] = _CacheEntry(value=count, timestamp=now)
        return count

    def total_drivers(self, daily_routes_path: Optional[str]) -> Optional[int]:
        """Count distinct drivers from Daily Routes (Routes sheet)."""
        if not daily_routes_path:
            return None
        p = Path(daily_routes_path)
        if not p.exists():
            return None

        # Cache key by path
        now = time()
        cache = self._drv_cache.get(str(p))
        if cache and (now - cache.timestamp) < self.cache_ttl:
            return cache.value

        try:
            df = pd.read_excel(str(p), sheet_name="Routes")
        except Exception as e:
            logger.debug(f"Daily Routes read failed from {p}: {e}")
            return None

        # Normalize column names
        cols = {c.lower().strip(): c for c in df.columns}
        driver_col = cols.get("driver name") or cols.get("driver")

        if not driver_col:
            return None

        try:
            count = int(
                df[driver_col]
                .dropna()
                .astype(str)
                .str.strip()
                .replace({"": pd.NA})
                .dropna()
                .nunique()
            )
        except Exception as e:
            logger.debug(f"Driver count computation failed: {e}")
            return None

        self._drv_cache[str(p)] = _CacheEntry(value=count, timestamp=now)
        return count
