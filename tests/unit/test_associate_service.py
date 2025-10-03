"""Unit tests for AssociateService."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Remove any previously imported `src` modules so pytest uses this repository copy
for module_name in list(sys.modules.keys()):
    if module_name == "src" or module_name.startswith("src."):
        del sys.modules[module_name]

from src.services.associate_service import AssociateService


def _write_sample_csv(path: Path, *, today: date) -> None:
    soon = (today + timedelta(days=15)).strftime("%m/%d/%Y")
    later = (today + timedelta(days=160)).strftime("%m/%d/%Y")
    rows = [
        {
            "Name and ID": "Alice Example",
            "TransporterID": "T123",
            "Position": "Driver",
            "Qualifications": "CDL, Step Van",
            "ID expiration": soon,
            "Personal Phone Number": "8045551234",
            "Work Phone Number": "18045551234",
            "Email": "alice@example.com",
            "Status": "ACTIVE",
        },
        {
            "Name and ID": "Bob Example",
            "TransporterID": "T456",
            "Position": "Helper",
            "Qualifications": "Standard Parcel",
            "ID expiration": later,
            "Personal Phone Number": "8045555678",
            "Work Phone Number": "",
            "Email": "bob@example.com",
            "Status": "INACTIVE",
        },
    ]
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)


def test_associate_service_parses_csv(tmp_path):
    today = date.today()
    csv_path = tmp_path / "associates.csv"
    _write_sample_csv(csv_path, today=today)

    service = AssociateService(settings={"associate_data_path": str(csv_path)}, expiration_warning_days=90)
    records = service.load_associates()

    assert len(records) == 2
    records_by_name = {record.name: record for record in records}

    alice = records_by_name["Alice Example"]
    assert alice.transporter_id == "T123"
    assert alice.qualifications == ["CDL", "Step Van"]
    assert alice.is_active is True
    assert alice.is_expiring_soon is True
    assert alice.is_expired is False
    assert alice.days_until_expiration is not None
    assert "804555" in alice.personal_phone

    bob = records_by_name["Bob Example"]
    assert bob.is_active is False
    assert bob.is_expiring_soon is False
    assert bob.status == "INACTIVE"
    assert bob.personal_phone.endswith("5678")


def test_associate_service_missing_path_returns_empty(tmp_path):
    service = AssociateService(settings={"associate_data_path": str(tmp_path / "missing.csv")})
    records = service.load_associates()
    fallback_path = Path("inputs") / "AssociateData.csv"
    if fallback_path.exists():
        assert len(records) > 0
    else:
        assert records == []
