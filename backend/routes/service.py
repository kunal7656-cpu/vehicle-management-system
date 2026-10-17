
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Vehicle, ServiceRecord

router = APIRouter(
    prefix="/service-records",
    tags=["Service Records"]
)


class ServiceRecordCreate(BaseModel):
    vehicle_id: int = Field(gt=0)
    service_date: date
    odometer_km: int = Field(ge=0)
    component_name: str = Field(min_length=1, max_length=100)
    service_type: str = Field(min_length=1, max_length=100)
    work_description: str
    parts_replaced: str | None = None
    parts_cost: int = Field(default=0, ge=0)
    labour_cost: int = Field(default=0, ge=0)
    performed_by: str | None = None
    remarks: str | None = None


@router.post("/", status_code=201)
def create_service_record(
    record_data: ServiceRecordCreate,
    db: Session = Depends(get_db)
):
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == record_data.vehicle_id
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found."
        )

    if record_data.odometer_km < vehicle.current_odometer_km:
        raise HTTPException(
            status_code=400,
            detail="Service odometer cannot be less than the vehicle's current odometer."
        )

    new_record = ServiceRecord(**record_data.model_dump())

    db.add(new_record)
    vehicle.current_odometer_km = record_data.odometer_km
    vehicle.last_service_date = record_data.service_date

    db.commit()
    db.refresh(new_record)

    return {
        "message": "Service record created successfully",
        "id": new_record.id,
        "vehicle_id": new_record.vehicle_id,
        "component_name": new_record.component_name,
        "service_date": new_record.service_date,
        "odometer_km": new_record.odometer_km
    }


@router.get("/")
def get_service_records(
    vehicle_id: int | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(ServiceRecord)

    if vehicle_id is not None:
        query = query.filter(
            ServiceRecord.vehicle_id == vehicle_id
        )

    return query.order_by(ServiceRecord.id.desc()).all()
