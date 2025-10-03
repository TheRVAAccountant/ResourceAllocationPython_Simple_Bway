"""Data models representing DSP scorecard performance information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScorecardMetadata:
    """High-level metadata extracted from a scorecard PDF."""

    station: str | None
    dsp_name: str | None
    week_number: int | None
    year: int | None


@dataclass(slots=True)
class DAWeeklyPerformance:
    """Normalized Delivery Associate current-week performance metrics."""

    rank: int
    name: str
    transporter_id: str
    overall_tier: str
    delivered: int | None
    key_focus_area: str | None
    fico_score: str | None
    seatbelt_off_rate: float | None
    speeding_event_rate: float | None
    distractions_rate: float | None
    following_distance_rate: float | None
    sign_signal_violations: float | None
    cdf_dpmo: float | None
    ced_dpmo: float | None
    dcr_percent: float | None
    dsb_count: float | None
    pod_percent: float | None
    psb_status: str | None
    dsb_events: int | None
    pod_opportunities: int | None
