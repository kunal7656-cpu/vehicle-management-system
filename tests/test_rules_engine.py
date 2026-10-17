
from datetime import date

from backend.rules_engine import check_maintenance_due


def test_maintenance_due_by_kilometres():
    result = check_maintenance_due(
        current_odometer_km=20000,
        last_service_odometer_km=10000,
        last_service_date=date(2026, 1, 1),
        interval_km=10000,
        interval_months=12,
        today=date(2026, 6, 1),
    )

    assert result["maintenance_due"] is True
    assert result["km_due"] is True
    assert result["date_due"] is False
    assert result["next_due_km"] == 20000


def test_maintenance_due_by_date():
    result = check_maintenance_due(
        current_odometer_km=15000,
        last_service_odometer_km=10000,
        last_service_date=date(2025, 10, 1),
        interval_km=10000,
        interval_months=12,
        today=date(2026, 10, 17),
    )

    assert result["maintenance_due"] is True
    assert result["date_due"] is True


def test_maintenance_not_due():
    result = check_maintenance_due(
        current_odometer_km=12000,
        last_service_odometer_km=10000,
        last_service_date=date(2026, 6, 1),
        interval_km=10000,
        interval_months=12,
        today=date(2026, 10, 17),
    )

    assert result["maintenance_due"] is False
    assert result["km_due"] is False
    assert result["date_due"] is False


def test_maintenance_due_when_both_limits_reached():
    result = check_maintenance_due(
        current_odometer_km=20000,
        last_service_odometer_km=10000,
        last_service_date=date(2025, 10, 1),
        interval_km=10000,
        interval_months=12,
        today=date(2026, 10, 17),
    )

    assert result["maintenance_due"] is True
    assert result["km_due"] is True
    assert result["date_due"] is True
