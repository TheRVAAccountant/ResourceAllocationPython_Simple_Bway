"""Data models representing DSP scorecard performance information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ScorecardMetadata:
    """High-level metadata extracted from a scorecard PDF."""

    station: Optional[str]
    dsp_name: Optional[str]
    week_number: Optional[int]
    year: Optional[int]


@dataclass(slots=True)
class DAWeeklyPerformance:
    """Normalized Delivery Associate current-week performance metrics."""

    rank: int
    name: str
    transporter_id: str
    overall_tier: str
    delivered: Optional[int]
    key_focus_area: Optional[str]
    fico_score: Optional[str]
    seatbelt_off_rate: Optional[float]
    speeding_event_rate: Optional[float]
    distractions_rate: Optional[float]
    following_distance_rate: Optional[float]
    sign_signal_violations: Optional[float]
    cdf_dpmo: Optional[float]
    ced_dpmo: Optional[float]
    dcr_percent: Optional[float]
    dsb_count: Optional[float]
    pod_percent: Optional[float]
    psb_status: Optional[str]
    dsb_events: Optional[int]
    pod_opportunities: Optional[int]
