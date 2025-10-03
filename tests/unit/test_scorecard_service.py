"""Tests for ScorecardService parsing logic."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCORECARD_PATH = PROJECT_ROOT / "inputs" / "US_BWAY_DVA2_Week37_2025_en_DSPScorecard.pdf"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

for module_name in list(sys.modules.keys()):
    if module_name == "src" or module_name.startswith("src."):
        del sys.modules[module_name]

from src.services.scorecard_service import ScorecardService


def test_scorecard_service_parses_metadata_and_rows():
    settings = {"scorecard_pdf_path": str(SCORECARD_PATH)}
    service = ScorecardService(settings=settings)

    data = service.load_scorecard()
    assert data is not None

    meta = data.metadata
    assert meta.station == "DVA2"
    assert meta.dsp_name == "BWAY"
    assert meta.week_number == 37
    assert meta.year == 2025

    assert len(data.associates) >= 40
    first = data.associates[0]
    assert first.name == "Ashley Norris"
    assert first.overall_tier == "Fantastic"
    assert first.dcr_percent is not None and abs(first.dcr_percent - 100.0) < 0.1
