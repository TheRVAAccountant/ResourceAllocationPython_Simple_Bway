"""Service for parsing DSP scorecard PDFs and extracting DA performance data."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import pdfplumber
from loguru import logger

from src.models.scorecard import DAWeeklyPerformance, ScorecardMetadata


@dataclass
class ScorecardData:
    """Container for extracted scorecard information."""

    metadata: ScorecardMetadata
    associates: List[DAWeeklyPerformance]


class ScorecardService:
    """Load and parse scorecard PDFs for display in the GUI."""

    def __init__(
        self,
        settings: Optional[dict] = None,
        *,
        settings_file: Path = Path("config/settings.json"),
    ) -> None:
        self._settings = settings or self._load_settings(settings_file)
        self._settings_file = settings_file

    # ------------------------------------------------------------------
    def _load_settings(self, settings_file: Path) -> dict:
        try:
            if settings_file.exists():
                with open(settings_file, "r", encoding="utf-8") as handle:
                    return json.load(handle) or {}
        except Exception as exc:
            logger.debug(f"ScorecardService settings load failed: {exc}")
        return {}

    def update_settings(self, settings: Optional[dict]) -> None:
        self._settings = settings or {}

    # ------------------------------------------------------------------
    def resolve_scorecard_path(self, explicit_path: Optional[str] = None) -> Optional[Path]:
        """Return the first existing scorecard PDF path."""
        candidates: Iterable[Optional[str]] = (
            explicit_path,
            self._settings.get("scorecard_pdf_path") if self._settings else None,
            str(Path("inputs") / "US_BWAY_DVA2_Week37_2025_en_DSPScorecard.pdf"),
        )
        for candidate in candidates:
            if not candidate:
                continue
            p = Path(candidate).expanduser()
            if p.exists():
                return p
        return None

    # ------------------------------------------------------------------
    def load_scorecard(self, path: Optional[str] = None) -> Optional[ScorecardData]:
        scorecard_path = self.resolve_scorecard_path(path)
        if not scorecard_path:
            logger.debug("ScorecardService could not resolve scorecard PDF path")
            return None

        try:
            with pdfplumber.open(scorecard_path) as pdf:
                metadata = self._extract_metadata(pdf)
                associates = self._extract_da_table(pdf)
        except Exception as exc:
            logger.error(f"Failed to parse scorecard {scorecard_path}: {exc}")
            return None

        return ScorecardData(metadata=metadata, associates=associates)

    # ------------------------------------------------------------------
    def _extract_metadata(self, pdf: pdfplumber.PDF) -> ScorecardMetadata:
        station = None
        dsp_name = None
        week_number = None
        year = None

        pattern = re.compile(
            r"^(?P<dsp>.+?)\s+at\s+(?P<station>[A-Z0-9]+)(?:\s*-\s*Week\s+(?P<week>\d+))?",
            re.MULTILINE,
        )

        for page in pdf.pages:
            text = page.extract_text() or ""
            if dsp_name is None:
                match = pattern.search(text)
                if match:
                    dsp_name = match.group("dsp").strip()
                    station = match.group("station").strip()
                    if match.group("week"):
                        week_number = int(match.group("week"))
                    else:
                        week_match = re.search(r"Week\s+(\d+)", text)
                        if week_match:
                            week_number = int(week_match.group(1))
            if year is None:
                year_match = re.search(r"Week\s+\d+\s*(20\d{2})", text)
                if year_match:
                    year = int(year_match.group(1))
                else:
                    any_year = re.search(r"(20\d{2})", text)
                    if any_year:
                        year = int(any_year.group(1))
            if dsp_name and station and week_number and year:
                break

        return ScorecardMetadata(
            station=station,
            dsp_name=dsp_name,
            week_number=week_number,
            year=year,
        )

    # ------------------------------------------------------------------
    def _extract_da_table(self, pdf: pdfplumber.PDF) -> List[DAWeeklyPerformance]:
        rows: List[DAWeeklyPerformance] = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            if "DA Current Week Performance" not in text:
                continue

            for table in page.extract_tables():
                if not table:
                    continue
                header_row = self._find_header_row(table)
                if header_row is None:
                    continue
                column_names = self._expand_header(header_row)
                for row in table:
                    if not row:
                        continue
                    if not row[0] or not row[0].strip().isdigit():
                        continue
                    record = self._row_to_performance(row, column_names)
                    if record:
                        rows.append(record)

        rows.sort(key=lambda r: r.rank)
        return rows

    @staticmethod
    def _find_header_row(table: List[List[Optional[str]]]) -> Optional[List[Optional[str]]]:
        for row in table:
            if row and row[0] and row[0].strip() == "#":
                return row
        return None

    @staticmethod
    def _expand_header(header: List[Optional[str]]) -> List[str]:
        expanded: List[str] = []
        current = ""
        for cell in header:
            if cell is None:
                expanded.append(current)
            else:
                current = cell.replace("\n", " ").strip()
                expanded.append(current)
        return expanded

    # ------------------------------------------------------------------
    def _row_to_performance(
        self, row: List[Optional[str]], column_names: List[str]
    ) -> Optional[DAWeeklyPerformance]:
        try:
            rank = int((self._cell(row, column_names, "#") or "0").strip() or "0")
            name = (self._cell(row, column_names, "Name") or "").strip()
            transporter_id = (self._cell(row, column_names, "Transporter ID") or "").strip()
            if not name or not transporter_id:
                return None

            return DAWeeklyPerformance(
                rank=rank,
                name=name,
                transporter_id=transporter_id,
                overall_tier=(self._cell(row, column_names, "Overall Tier") or "").strip(),
                delivered=self._parse_int(self._cell(row, column_names, "Delivered")),
                key_focus_area=self._normalize_text(
                    self._cell(row, column_names, "Key Focus Area")
                ),
                fico_score=self._normalize_text(self._cell(row, column_names, "Fico Score")),
                seatbelt_off_rate=self._parse_float(
                    self._cell(row, column_names, "Seatbelt Off Rate")
                ),
                speeding_event_rate=self._parse_float(
                    self._cell(row, column_names, "Speeding Event Rate")
                ),
                distractions_rate=self._parse_float(
                    self._cell(row, column_names, "Distractions Rate")
                ),
                following_distance_rate=self._parse_float(
                    self._cell(row, column_names, "Following Distance Rate")
                ),
                sign_signal_violations=self._parse_float(
                    self._cell(row, column_names, "Sign/Signal Violations Rate")
                ),
                cdf_dpmo=self._parse_float(self._cell(row, column_names, "CDF DPMO")),
                ced_dpmo=self._parse_float(self._cell(row, column_names, "CED")),
                dcr_percent=self._parse_percent(self._cell(row, column_names, "DCR")),
                dsb_count=self._parse_float(self._cell(row, column_names, "DSB")),
                pod_percent=self._parse_percent(self._cell(row, column_names, "POD")),
                psb_status=self._normalize_text(self._cell(row, column_names, "PSB")),
                dsb_events=self._parse_int(self._cell(row, column_names, "DSB DNR")),
                pod_opportunities=self._parse_int(self._cell(row, column_names, "POD Opps.")),
            )
        except Exception as exc:
            logger.debug(f"Failed to convert scorecard row: {exc} | row={row}")
            return None

    @staticmethod
    def _cell(row: List[Optional[str]], columns: List[str], key: str) -> Optional[str]:
        for idx, name in enumerate(columns):
            if name == key:
                if idx < len(row):
                    return row[idx]
                return None
        return None

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_text(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @staticmethod
    def _parse_int(value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        try:
            cleaned = value.replace(",", "").strip()
            if not cleaned or cleaned.lower() in {"coming soon", "n/a", "na"}:
                return None
            return int(float(cleaned))
        except Exception:
            return None

    @staticmethod
    def _parse_float(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        cleaned = value.replace(",", "").strip()
        if not cleaned or cleaned.lower() in {"coming soon", "n/a", "na"}:
            return None
        try:
            return float(cleaned)
        except Exception:
            return None

    @staticmethod
    def _parse_percent(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        cleaned = value.strip().replace("%", "")
        if not cleaned or cleaned.lower() in {"coming soon"}:
            return None
        try:
            return float(cleaned)
        except Exception:
            return None
