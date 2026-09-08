"""Domain models for Manufacturing — auto-generated from ontology."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

class Person(BaseModel):
    """Entity model for Person."""

    name: str = Field(...)
    email: str | None = None
    role: str | None = None
    description: str | None = None

class Organization(BaseModel):
    """Entity model for Organization."""

    name: str = Field(...)
    description: str | None = None
    industry: str | None = None

class Location(BaseModel):
    """Entity model for Location."""

    name: str = Field(...)
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None

class Event(BaseModel):
    """Entity model for Event."""

    name: str = Field(...)
    date: datetime | None = None
    description: str | None = None

class Object(BaseModel):
    """Entity model for Object."""

    name: str = Field(...)
    description: str | None = None

class MachineMachineTypeEnum(str, Enum):
    CNC = "cnc"
    PRESS = "press"
    LATHE = "lathe"
    WELDER = "welder"
    ASSEMBLER = "assembler"
    CONVEYOR = "conveyor"
    ROBOT = "robot"
    PACKAGING = "packaging"

class MachineStatusEnum(str, Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    DECOMMISSIONED = "decommissioned"

class Machine(BaseModel):
    """Entity model for Machine."""

    machine_id: str = Field(...)
    name: str = Field(...)
    machine_type: MachineMachineTypeEnum | None = None
    manufacturer: str | None = None
    install_date: date | None = None
    status: MachineStatusEnum | None = None
    operating_hours: int | None = None

class PartCategoryEnum(str, Enum):
    RAW_MATERIAL = "raw_material"
    COMPONENT = "component"
    SUBASSEMBLY = "subassembly"
    FINISHED_GOOD = "finished_good"

class Part(BaseModel):
    """Entity model for Part."""

    part_number: str = Field(...)
    name: str = Field(...)
    category: PartCategoryEnum | None = None
    unit_cost: float | None = None
    stock_quantity: int | None = None
    minimum_stock: int | None = None
    specification: str | None = None

class WorkOrderPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class WorkOrderStatusEnum(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"

class WorkOrder(BaseModel):
    """Entity model for WorkOrder."""

    work_order_id: str = Field(...)
    description: str = Field(...)
    priority: WorkOrderPriorityEnum | None = None
    status: WorkOrderStatusEnum | None = None
    start_date: datetime | None = None
    due_date: datetime | None = None
    quantity: int = Field(...)

class WorkCenterStatusEnum(str, Enum):
    AVAILABLE = "available"
    CONSTRAINED = "constrained"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"

class WorkCenter(BaseModel):
    """Entity model for WorkCenter."""

    work_center_id: str = Field(...)
    name: str = Field(...)
    capacity_per_hour: int | None = None
    status: WorkCenterStatusEnum | None = None

class ProductionEventStatusEnum(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    CANCELLED = "cancelled"

class ProductionEvent(BaseModel):
    """Entity model for ProductionEvent."""

    production_event_id: str = Field(...)
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    status: ProductionEventStatusEnum | None = None

class BillOfMaterialsStatusEnum(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    OBSOLETE = "obsolete"

class BillOfMaterials(BaseModel):
    """Entity model for BillOfMaterials."""

    bill_of_materials_id: str = Field(...)
    name: str = Field(...)
    status: BillOfMaterialsStatusEnum | None = None

class MaterialRequirement(BaseModel):
    """Entity model for MaterialRequirement."""

    material_requirement_id: str = Field(...)
    quantity: float = Field(...)
    unit_of_measure: str = Field(...)

class ScheduleSlotPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ScheduleSlot(BaseModel):
    """Entity model for ScheduleSlot."""

    schedule_slot_id: str = Field(...)
    planned_start: datetime = Field(...)
    planned_end: datetime = Field(...)
    priority: ScheduleSlotPriorityEnum | None = None

class SupplyCommitmentStatusEnum(str, Enum):
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    DELAYED = "delayed"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"

class SupplyCommitment(BaseModel):
    """Entity model for SupplyCommitment."""

    supply_commitment_id: str = Field(...)
    commitment_date: date = Field(...)
    lead_time_days: int | None = None
    status: SupplyCommitmentStatusEnum | None = None

class SupplierStatusEnum(str, Enum):
    APPROVED = "approved"
    PROBATIONARY = "probationary"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"

class Supplier(BaseModel):
    """Entity model for Supplier."""

    supplier_id: str = Field(...)
    name: str = Field(...)
    country: str | None = None
    lead_time_days: int | None = None
    quality_rating: float | None = None
    status: SupplierStatusEnum | None = None

class QualityReportResultEnum(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL_PASS = "conditional_pass"

class QualityReport(BaseModel):
    """Entity model for QualityReport."""

    report_id: str = Field(...)
    inspection_date: datetime = Field(...)
    inspector: str | None = None
    result: QualityReportResultEnum | None = None
    defect_count: int | None = None
    defect_type: str | None = None
    notes: str | None = None

class ProductionLineStatusEnum(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    RETOOLING = "retooling"

class ProductionLineShiftPatternEnum(str, Enum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    CONTINUOUS = "continuous"

class ProductionLine(BaseModel):
    """Entity model for ProductionLine."""

    line_id: str = Field(...)
    name: str = Field(...)
    capacity_per_hour: int | None = None
    efficiency_rating: float | None = None
    status: ProductionLineStatusEnum | None = None
    shift_pattern: ProductionLineShiftPatternEnum | None = None

class CDSView(BaseModel):
    """Entity model for CDSView."""

    view_uri: str = Field(...)
    name: str = Field(...)
    technical_name: str = Field(...)
    short_description: str | None = None
    source_system: str | None = None

class CDSField(BaseModel):
    """Entity model for CDSField."""

    field_uri: str = Field(...)
    name: str = Field(...)
    field_name: str = Field(...)
    field_type: str | None = None
    definition: str | None = None
    reference_field: str | None = None

class BusinessConcept(BaseModel):
    """Entity model for BusinessConcept."""

    concept_uri: str = Field(...)
    name: str = Field(...)
    notation: str | None = None
    scope_note: str | None = None

class TaxonomyConceptGovernanceStatusEnum(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"

class TaxonomyConcept(BaseModel):
    """Entity model for TaxonomyConcept."""

    concept_uri: str = Field(...)
    pref_label: str = Field(...)
    alt_labels: str | None = None
    notation: str | None = None
    scope_note: str | None = None
    governance_status: TaxonomyConceptGovernanceStatusEnum | None = None

class SourceDataset(BaseModel):
    """Entity model for SourceDataset."""

    source_uri: str = Field(...)
    name: str = Field(...)
    source_commit: str | None = None
    license: str | None = None
    import_timestamp: datetime | None = None
    row_count: int | None = None

class SalesDocument(BaseModel):
    """Entity model for SalesDocument."""

    sales_document: str = Field(...)
    name: str = Field(...)
    sales_organization: str | None = None
    sales_document_type: str | None = None
    distribution_channel: str | None = None
    division: str | None = None
    transaction_currency: str | None = None
    incoterms_classification: str | None = None
    creation_timestamp: datetime | None = None

