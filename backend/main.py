from backend.routes.maintenance import router as maintenance_router
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Vehicle
from backend.schemas import VehicleCreate, VehicleResponse
from backend.routes.service import router as service_router
from backend.routes.inspection import router as inspection_router 
from backend.routes.work_orders import router as work_orders_router

app = FastAPI(
    title="Army Vehicle Maintenance Portal",
    description="Vehicle registration and maintenance management system",
    version="1.0.0"
)
app.include_router(maintenance_router)
app.include_router(service_router)
app.include_router(inspection_router)
app.include_router(work_orders_router)

@app.get("/")
def home():
    return {
        "message": "Army Vehicle Maintenance Portal is running!",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/vehicles/", response_model=VehicleResponse, status_code=201)
def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db)
):
    existing_vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.registration_number
            == vehicle_data.registration_number
        )
        .first()
    )

    if existing_vehicle:
        raise HTTPException(
            status_code=409,
            detail="This vehicle registration number already exists."
        )

    new_vehicle = Vehicle(**vehicle_data.model_dump())

    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return new_vehicle


@app.get("/vehicles/", response_model=list[VehicleResponse])
def get_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).order_by(Vehicle.id).all()
