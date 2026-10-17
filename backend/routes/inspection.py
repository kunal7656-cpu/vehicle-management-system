
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Vehicle, Inspection

router = APIRouter(prefix="/inspections", tags=["Inspections"])


class InspectionCreate(BaseModel):
    vehicle_id: int = Field(gt=0)
    component_name: str = Field(min_length=1, max_length=100)
    inspection_date: date
    condition: str = Field(min_length=1, max_length=50)
    defect_description: str | None = None
    inspection_decision: str = Field(min_length=1, max_length=100)
    recommended_action: str | None = None
    inspected_by: str | None = None


@router.post("/", status_code=201)
def create_inspection(
    inspection_data: InspectionCreate,
    db: Session = Depends(get_db)
):
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == inspection_data.vehicle_id)
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found."
        )

    new_inspection = Inspection(**inspection_data.model_dump())

    db.add(new_inspection)
    db.commit()
    db.refresh(new_inspection)

    return {
        "message": "Inspection record created successfully",
        "id": new_inspection.id,
        "vehicle_id": new_inspection.vehicle_id,
        "component_name": new_inspection.component_name,
        "inspection_decision": new_inspection.inspection_decision
    }


@router.get("/")
def get_inspections(
    vehicle_id: int | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Inspection)

    if vehicle_id is not None:
        query = query.filter(Inspection.vehicle_id == vehicle_id)

    return query.order_by(Inspection.id.desc()).all()
