
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Vehicle, WorkOrder

router = APIRouter(
    prefix="/work-orders",
    tags=["Work Orders"]
)


class WorkOrderCreate(BaseModel):
    vehicle_id: int = Field(gt=0)
    component_name: str = Field(min_length=1, max_length=100)
    issue_description: str = Field(min_length=1)
    priority: str = "Medium"
    status: str = "Pending"
    due_date: date | None = None
    assigned_to: str | None = None
    remarks: str | None = None


class WorkOrderUpdate(BaseModel):
    status: str | None = None
    action_taken: str | None = None
    completion_date: date | None = None
    remarks: str | None = None


@router.post("/", status_code=201)
def create_work_order(
    order_data: WorkOrderCreate,
    db: Session = Depends(get_db)
):
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == order_data.vehicle_id)
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found."
        )

    new_order = WorkOrder(**order_data.model_dump())

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {
        "message": "Work order created successfully",
        "id": new_order.id,
        "vehicle_id": new_order.vehicle_id,
        "component_name": new_order.component_name,
        "priority": new_order.priority,
        "status": new_order.status
    }


@router.get("/")
def get_work_orders(
    vehicle_id: int | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(WorkOrder)

    if vehicle_id is not None:
        query = query.filter(
            WorkOrder.vehicle_id == vehicle_id
        )

    return query.order_by(
        WorkOrder.id.desc()
    ).all()


@router.put("/{work_order_id}")
def update_work_order(
    work_order_id: int,
    update_data: WorkOrderUpdate,
    db: Session = Depends(get_db)
):
    work_order = (
        db.query(WorkOrder)
        .filter(WorkOrder.id == work_order_id)
        .first()
    )

    if not work_order:
        raise HTTPException(
            status_code=404,
            detail="Work order not found."
        )

    update_values = update_data.model_dump(
        exclude_unset=True
    )

    if (
        update_values.get("status") == "Completed"
        and "completion_date" not in update_values
    ):
        update_values["completion_date"] = date.today()

    for field, value in update_values.items():
        setattr(work_order, field, value)

    db.commit()
    db.refresh(work_order)

    return {
        "message": "Work order updated successfully",
        "id": work_order.id,
        "status": work_order.status,
        "completion_date": work_order.completion_date,
        "action_taken": work_order.action_taken
    }


@router.post("/from-maintenance/{vehicle_id}")
def create_work_orders_from_maintenance(
    vehicle_id: int,
    db: Session = Depends(get_db)
):
    from backend.routes.maintenance import (
        check_vehicle_maintenance
    )

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

    maintenance_result = check_vehicle_maintenance(
        vehicle_id=vehicle_id,
        today=None,
        db=db
    )

    created_orders = []
    skipped_orders = []

    for item in maintenance_result["maintenance_checks"]:

        # Create work orders only for explicitly due items.
        if item.get("maintenance_due") is not True:
            continue

        component_name = item["component_name"]

        # Prevent duplicate active work orders.
        existing_order = (
            db.query(WorkOrder)
            .filter(
                WorkOrder.vehicle_id == vehicle_id,
                WorkOrder.component_name.ilike(
                    component_name
                ),
                WorkOrder.status.in_(
                    ["Pending", "In Progress"]
                )
            )
            .first()
        )

        if existing_order:
            skipped_orders.append({
                "component_name": component_name,
                "reason": "An active work order already exists.",
                "existing_work_order_id": existing_order.id
            })
            continue

        reasons = item.get("reasons") or []

        reason_text = (
            ", ".join(reasons)
            if reasons
            else item.get("reason", "Maintenance is due")
        )

        new_order = WorkOrder(
            vehicle_id=vehicle_id,
            component_name=component_name,
            issue_description=(
                f"Scheduled maintenance due: "
                f"{item['service_task']}. "
                f"Reasons: {reason_text}"
            ),
            priority="High",
            status="Pending"
        )

        db.add(new_order)

        # Flush assigns an ID without committing each order.
        db.flush()

        created_orders.append({
            "work_order_id": new_order.id,
            "component_name": new_order.component_name,
            "status": new_order.status
        })

    db.commit()

    return {
        "message": "Maintenance work orders processed",
        "vehicle_id": vehicle_id,
        "created_count": len(created_orders),
        "created_work_orders": created_orders,
        "skipped_count": len(skipped_orders),
        "skipped_work_orders": skipped_orders
    }
