"""Service responsible for loading and normalizing associate roster data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional
import json

import pandas as pd
from loguru import logger

from src.models.associate import AssociateRecord


@dataclass
class _AssociateCache:
    """Internal cache representation for loaded associate data."""

    path: Path
    mtime: float
    records: List[AssociateRecord]


class AssociateService:
    """Service that loads associate data from CSV and exposes normalized records."""

    def __init__(
        self,
        settings: Optional[dict] = None,
        *,
        settings_file: Path = Path("config/settings.json"),
        expiration_warning_days: int = 90,
    ) -> None:
        self._settings = settings or self._load_settings(settings_file)
        self._settings_file = settings_file
        self.expiration_warning_days = expiration_warning_days
        self._cache: Optional[_AssociateCache] = None

    # ------------------------------------------------------------------
    # Settings helpers
    def _load_settings(self, settings_file: Path) -> dict:
        try:
            if settings_file.exists():
                with open(settings_file, "r", encoding="utf-8") as handle:
                    return json.load(handle) or {}
        except Exception as exc:
            logger.debug(f"AssociateService settings load failed: {exc}")
        return {}

    def update_settings(self, settings: Optional[dict]) -> None:
        """Replace the active settings dictionary and clear cache."""
        self._settings = settings or {}
        self._cache = None

    # ------------------------------------------------------------------
    # Path resolution
    def resolve_associate_path(self, explicit_path: Optional[str] = None) -> Optional[Path]:
        """Resolve the associate CSV path using explicit value, settings, or default."""
        candidates: Iterable[Optional[str]] = (
            explicit_path,
            self._settings.get("associate_data_path") if self._settings else None,
            str(Path("inputs") / "AssociateData.csv"),
        )
        for candidate in candidates:
            if not candidate:
                continue
            path_obj = Path(candidate).expanduser()
            if path_obj.exists():
                return path_obj
        return None

    # ------------------------------------------------------------------
    # Public API
    def load_associates(self, path: Optional[str] = None, *, force_reload: bool = False) -> List[AssociateRecord]:
        """Load associates from CSV, applying normalization and caching."""
        resolved = self.resolve_associate_path(path)
        if not resolved:
            logger.debug("AssociateService could not resolve associate CSV path")
            self._cache = None
            return []

        try:
            mtime = resolved.stat().st_mtime
        except OSError as exc:
            logger.warning(f"AssociateService unable to stat file {resolved}: {exc}")
            self._cache = None
            return []

        if (
            not force_reload
            and self._cache is not None
            and self._cache.path == resolved
            and self._cache.mtime == mtime
        ):
            return self._cache.records

        try:
            frame = pd.read_csv(resolved, encoding="utf-8-sig")
        except Exception as exc:
            logger.error(f"AssociateService failed to read CSV {resolved}: {exc}")
            self._cache = None
            return []

        records = self._frame_to_records(frame)
        self._cache = _AssociateCache(path=resolved, mtime=mtime, records=records)
        return records

    # ------------------------------------------------------------------
    # Conversion helpers
    def _frame_to_records(self, frame: pd.DataFrame) -> List[AssociateRecord]:
        normalized_columns = {self._normalize_column_name(c): c for c in frame.columns}
        try:
            name_col = normalized_columns["name_and_id"]
            transporter_col = normalized_columns["transporterid"]
            position_col = normalized_columns.get("position")
            qualifications_col = normalized_columns.get("qualifications")
            expiration_col = normalized_columns.get("id_expiration")
            personal_phone_col = normalized_columns.get("personal_phone_number")
            work_phone_col = normalized_columns.get("work_phone_number")
            email_col = normalized_columns.get("email")
            status_col = normalized_columns.get("status")
        except KeyError as exc:
            logger.error(f"AssociateService missing required column: {exc}")
            return []

        today = date.today()
        records: List[AssociateRecord] = []
        for _, row in frame.iterrows():
            name = str(row.get(name_col, "")).strip()
            transporter = str(row.get(transporter_col, "")).strip()
            if not name and not transporter:
                continue

            expiration_raw = row.get(expiration_col) if expiration_col else None
            expiration_date = self._parse_date(expiration_raw)
            delta_days: Optional[int] = None
            is_expired = False
            is_expiring_soon = False
            if expiration_date:
                delta_days = (expiration_date - today).days
                is_expired = delta_days < 0
                is_expiring_soon = 0 <= delta_days <= self.expiration_warning_days

            status_value = str(row.get(status_col, "")).strip().upper() if status_col else ""
            is_active = status_value != "INACTIVE"

            qualifications_raw = row.get(qualifications_col, "") if qualifications_col else ""
            qualifications = [q.strip() for q in str(qualifications_raw).split(",") if q.strip()]

            record = AssociateRecord(
                name=name,
                transporter_id=transporter,
                position=str(row.get(position_col, "")).strip() if position_col else "",
                qualifications=qualifications,
                id_expiration=expiration_date,
                personal_phone=self._normalize_phone(row.get(personal_phone_col)),
                work_phone=self._normalize_phone(row.get(work_phone_col)),
                email=str(row.get(email_col, "")).strip() if email_col else "",
                status=status_value or "ACTIVE",
                days_until_expiration=delta_days,
                is_active=is_active,
                is_expired=is_expired,
                is_expiring_soon=is_expiring_soon,
            )
            records.append(record)

        return records

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_column_name(column: str) -> str:
        return column.lower().strip().replace(" ", "_")

    @staticmethod
    def _normalize_phone(value: Optional[object]) -> str:
        if value is None:
            return ""
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        if not digits:
            return ""
        return digits

    @staticmethod
    def _parse_date(value: Optional[object]) -> Optional[date]:
        if value is None or value == "":
            return None
        try:
            parsed = pd.to_datetime(value, errors="coerce")
            if pd.isna(parsed):
                return None
            return parsed.date()
        except Exception:
            return None
