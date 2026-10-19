
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Vehicle, MaintenanceRule, ServiceRecord
from backend.rules_engine import check_maintenance_due


router = APIRouter(
    prefix="/maintenance-rules",
    tags=["Maintenance Rules"]
)


class MaintenanceRuleCreate(BaseModel):
    vehicle_model: str = Field(min_length=1, max_length=100)
    component_name: str = Field(min_length=1, max_length=100)
    service_task: str = Field(min_length=1, max_length=200)
    interval_km: int = Field(default=0, ge=0)
    interval_months: int = Field(default=0, ge=0)


@router.post("/", status_code=201)
def create_maintenance_rule(
    rule_data: MaintenanceRuleCreate,
    db: Session = Depends(get_db)
):
    if rule_data.interval_km == 0 and rule_data.interval_months == 0:
        raise HTTPException(
            status_code=422,
            detail="Provide a kilometre interval or a month interval."
        )

    rule = MaintenanceRule(
        **rule_data.model_dump(),
        inspection_required=1,
        is_active=1
    )

    try:
        db.add(rule)
        db.commit()
        db.refresh(rule)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This maintenance rule already exists."
        )

    return {
        "message": "Maintenance rule created successfully",
        "id": rule.id
    }


@router.get("/")
def get_maintenance_rules(
    db: Session = Depends(get_db)
):
    return (
        db.query(MaintenanceRule)
        .order_by(MaintenanceRule.id)
        .all()
    )


@router.get("/check/{vehicle_id}")
def check_vehicle_maintenance(
    vehicle_id: int,
    today: date | None = None,
    db: Session = Depends(get_db)
):
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id)
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found."
        )

    rules = (
        db.query(MaintenanceRule)
        .filter(
            MaintenanceRule.vehicle_model == vehicle.model,
            MaintenanceRule.is_active == 1
        )
        .order_by(MaintenanceRule.id)
        .all()
    )

    results = []

    for rule in rules:
        last_service = (
            db.query(ServiceRecord)
            .filter(
                ServiceRecord.vehicle_id == vehicle_id,
                ServiceRecord.component_name.ilike(
                    rule.component_name
                )
            )
            .order_by(
                ServiceRecord.service_date.desc(),
                ServiceRecord.id.desc()
            )
            .first()
        )

        # No service history means the due status cannot
        # be reliably calculated from the last service.
        if last_service is None:
            results.append({
                "rule_id": rule.id,
                "component_name": rule.component_name,
                "service_task": rule.service_task,
                "service_history_available": False,
                "maintenance_due": None,
                "maintenance_status": "History unavailable",
                "reason": (
                    "No matching service record found. "
                    "Add historical service details to calculate "
                    "the maintenance due status."
                ),
                "next_due_km": None,
                "next_due_date": None
            })
            continue

        result = check_maintenance_due(
            current_odometer_km=vehicle.current_odometer_km,
            last_service_odometer_km=last_service.odometer_km,
            last_service_date=last_service.service_date,
            interval_km=rule.interval_km or 0,
            interval_months=rule.interval_months or 0,
            today=today
        )

        is_due = result.get("maintenance_due", False)

        results.append({
            "rule_id": rule.id,
            "component_name": rule.component_name,
            "service_task": rule.service_task,
            "service_history_available": True,
            "maintenance_status": "Due" if is_due else "Not due",
            **result
        })

    return {
        "vehicle_id": vehicle.id,
        "vehicle_model": vehicle.model,
        "current_odometer_km": vehicle.current_odometer_km,
        "maintenance_checks": results
    }
