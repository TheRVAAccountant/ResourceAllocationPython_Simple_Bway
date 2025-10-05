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
    def resolve_daily_summary_path(self, explicit_path: str | None = None) -> str | None:
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
                with open(settings_path, encoding="utf-8") as f:
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
    def load_vehicle_status(self, daily_summary_path: str | None) -> pd.DataFrame | None:
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

    def load_vehicle_log(self, daily_summary_path: str | None) -> pd.DataFrame | None:
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

    def load_associate_data(self, csv_path: str | None = None) -> pd.DataFrame | None:
        """Load associate data from CSV with caching.

        Loads driver/helper associate data from AssociateData.csv format with
        proper date parsing and column normalization.

        Args:
            csv_path: Path to AssociateData.csv (defaults to inputs/AssociateData.csv)

        Returns:
            DataFrame with normalized columns or None on failure

        Note:
            - Handles UTF-8 BOM encoding
            - Parses ID expiration dates in MM/DD/YYYY format
            - Caches results for performance
        """
        # Resolve path
        path = Path(csv_path) if csv_path else Path("inputs") / "AssociateData.csv"

        if not path.exists():
            logger.debug(f"Associate data not found at {path}")
            return None

        # Check cache
        key = f"associates::{path}"
        now = time()
        entry = self._cache.get(key)
        if entry and (now - entry.ts) < self.cache_ttl:
            return entry.df

        try:
            # Read with proper encoding and date parsing
            df = pd.read_csv(
                path,
                encoding="utf-8-sig",  # Handle BOM if present
            )

            # Normalize column names (strip whitespace)
            df.columns = df.columns.str.strip()

            # Parse ID expiration date
            if "ID expiration" in df.columns:
                df["ID expiration"] = pd.to_datetime(
                    df["ID expiration"], format="%m/%d/%Y", errors="coerce"
                )

            # Cache and return
            self._cache[key] = _CacheEntry(df=df, ts=now)
            logger.info(f"Loaded {len(df)} associates from {path}")
            return df

        except Exception as e:
            logger.error(f"Failed to load associate data from {path}: {e}")
            return None

    def load_vehicles_data(self, xlsx_path: str | None = None) -> pd.DataFrame | None:
        """Load comprehensive vehicle data from VehiclesData.xlsx.

        Loads fleet inventory with comprehensive vehicle details including VIN,
        make, model, ownership information, and registration data.

        Args:
            xlsx_path: Path to VehiclesData.xlsx (defaults to bway_files/VehiclesData.xlsx)

        Returns:
            DataFrame with normalized columns or None on failure

        Note:
            - Contains 28 columns with full vehicle specifications
            - Parses ownership and registration dates
            - Caches results for performance
        """
        # Resolve path
        if xlsx_path:
            path = Path(xlsx_path)
        else:
            path = Path("bway_files") / "VehiclesData.xlsx"
            if not path.exists():
                path = Path("inputs") / "VehiclesData.xlsx"

        if not path.exists():
            logger.debug(f"Vehicles data not found at {path}")
            return None

        # Check cache
        key = f"vehicles_data::{path}"
        now = time()
        entry = self._cache.get(key)
        if entry and (now - entry.ts) < self.cache_ttl:
            return entry.df

        try:
            # Read comprehensive vehicle data
            df = pd.read_excel(path, sheet_name="Sheet1")

            # Parse date columns
            date_cols = ["ownershipStartDate", "ownershipEndDate", "registrationExpiryDate"]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            # Cache and return
            self._cache[key] = _CacheEntry(df=df, ts=now)
            logger.info(f"Loaded {len(df)} vehicles from {path}")
            return df

        except Exception as e:
            logger.error(f"Failed to load vehicles data from {path}: {e}")
            return None
