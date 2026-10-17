
from datetime import date
from dateutil.relativedelta import relativedelta


def check_maintenance_due(
    current_odometer_km: int,
    last_service_odometer_km: int | None,
    last_service_date: date | None,
    interval_km: int,
    interval_months: int,
    today: date | None = None
) -> dict:
    """
    Check whether maintenance is due by kilometres or time.
    These checks use configured rules, not an official vehicle schedule.
    """
    today = today or date.today()

    km_due = False
    date_due = False
    next_due_km = None
    next_due_date = None

    if interval_km > 0 and last_service_odometer_km is not None:
        next_due_km = last_service_odometer_km + interval_km
        km_due = current_odometer_km >= next_due_km

    if interval_months > 0 and last_service_date is not None:
        next_due_date = last_service_date + relativedelta(
            months=interval_months
        )
        date_due = today >= next_due_date

    maintenance_due = km_due or date_due

    reasons = []
    if km_due:
        reasons.append("Kilometre interval reached")
    if date_due:
        reasons.append("Time interval reached")

    return {
        "maintenance_due": maintenance_due,
        "km_due": km_due,
        "date_due": date_due,
        "next_due_km": next_due_km,
        "next_due_date": (
            next_due_date.isoformat() if next_due_date else None
        ),
        "reasons": reasons
    }
