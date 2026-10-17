
from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    registration_number: str = Field(min_length=1, max_length=50)
    vehicle_name: str = Field(min_length=1, max_length=100)
    vehicle_type: str = "SUV"
    manufacturer: str = "Mahindra"
    model: str = "Scorpio"
    manufacture_year: int | None = Field(default=None, ge=1900, le=2100)
    unit_name: str | None = None
    current_odometer_km: int = Field(default=0, ge=0)
    last_service_date: date | None = None
    next_service_due_date: date | None = None
    status: str = "Active"


class VehicleResponse(VehicleCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
