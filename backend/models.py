from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func
)
from backend.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String(50), unique=True, nullable=False, index=True)
    vehicle_name = Column(String(100), nullable=False)
    vehicle_type = Column(String(50), nullable=False, default="SUV")
    manufacturer = Column(String(100), nullable=False, default="Mahindra")
    model = Column(String(100), nullable=False, default="Scorpio")
    manufacture_year = Column(Integer, nullable=True)
    unit_name = Column(String(150), nullable=True)
    current_odometer_km = Column(Integer, nullable=False, default=0)
    last_service_date = Column(Date, nullable=True)
    next_service_due_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, default="Active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MaintenanceRule(Base):
    __tablename__ = "maintenance_rules"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_model = Column(String(100), nullable=False)
    component_name = Column(String(100), nullable=False)
    service_task = Column(String(200), nullable=False)

    interval_km = Column(Integer, nullable=True)
    interval_months = Column(Integer, nullable=True)

    inspection_required = Column(
        Integer,
        nullable=False,
        default=1
    )

    is_active = Column(
        Integer,
        nullable=False,
        default=1
    )

    notes = Column(String(500), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "vehicle_model",
            "component_name",
            "service_task",
            name="uq_maintenance_rule_model_component_task"
        ),
    )


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    component_name = Column(String(100), nullable=False)
    inspection_date = Column(Date, nullable=False)

    condition = Column(String(50), nullable=False)
    defect_description = Column(String(500), nullable=True)

    inspection_decision = Column(
        String(50),
        nullable=False
    )

    recommended_action = Column(String(300), nullable=True)
    inspected_by = Column(String(100), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class ServiceRecord(Base):
    __tablename__ = "service_records"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    service_date = Column(Date, nullable=False)
    odometer_km = Column(Integer, nullable=False)

    component_name = Column(String(100), nullable=False)
    service_type = Column(String(100), nullable=False)

    work_description = Column(String(500), nullable=True)
    parts_replaced = Column(String(500), nullable=True)

    parts_cost = Column(Integer, nullable=False, default=0)
    labour_cost = Column(Integer, nullable=False, default=0)

    performed_by = Column(String(100), nullable=True)
    remarks = Column(String(500), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    component_name = Column(String(100), nullable=False)
    issue_description = Column(String(500), nullable=False)

    priority = Column(String(30), nullable=False, default="Medium")
    status = Column(String(30), nullable=False, default="Pending")

    created_date = Column(
        Date,
        nullable=False,
        server_default=func.current_date()
    )

    due_date = Column(Date, nullable=True)
    assigned_to = Column(String(100), nullable=True)
    completion_date = Column(Date, nullable=True)

    action_taken = Column(String(500), nullable=True)
    remarks = Column(String(500), nullable=True)
