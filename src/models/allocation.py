"""Allocation data models."""

from datetime import datetime, date
from typing import Optional, Any
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class AllocationStatus(str, Enum):
    """Allocation status enumeration."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VehicleType(str, Enum):
    """Vehicle type enumeration."""
    
    STANDARD = "standard"
    PREMIUM = "premium"
    ECONOMY = "economy"
    LUXURY = "luxury"
    SUV = "suv"
    TRUCK = "truck"
    VAN = "van"


class Priority(str, Enum):
    """Priority level enumeration."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Vehicle(BaseModel):
    """Represents a vehicle in the allocation system."""
    
    vehicle_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_number: str
    vehicle_type: VehicleType = VehicleType.STANDARD
    location: str
    status: str = "available"
    priority: int = Field(default=50, ge=0, le=100)
    capacity: Optional[int] = None
    fuel_level: Optional[Decimal] = None
    mileage: Optional[int] = None
    last_service_date: Optional[date] = None
    assigned_driver: Optional[str] = None
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @validator("vehicle_number")
    def validate_vehicle_number(cls, v):
        """Validate vehicle number format."""
        if not v or len(v) < 3:
            raise ValueError("Vehicle number must be at least 3 characters")
        return v.upper()
    
    @validator("fuel_level")
    def validate_fuel_level(cls, v):
        """Validate fuel level is between 0 and 100."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Fuel level must be between 0 and 100")
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class Driver(BaseModel):
    """Represents a driver in the allocation system."""
    
    driver_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    name: str
    location: str
    status: str = "active"
    priority: Priority = Priority.MEDIUM
    experience_years: int = Field(default=0, ge=0)
    license_type: str = "standard"
    certifications: list[str] = Field(default_factory=list)
    assigned_vehicles: list[str] = Field(default_factory=list)
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    max_vehicles: int = 3
    preferred_vehicle_types: list[VehicleType] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @validator("name")
    def validate_name(cls, v):
        """Validate driver name."""
        if not v or len(v.strip()) < 2:
            raise ValueError("Driver name must be at least 2 characters")
        return v.strip()
    
    @validator("employee_id")
    def validate_employee_id(cls, v):
        """Validate employee ID."""
        if not v:
            raise ValueError("Employee ID is required")
        return v.upper()
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class AllocationRequest(BaseModel):
    """Represents an allocation request."""
    
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicles: list[Vehicle]
    drivers: list[Driver]
    allocation_date: date = Field(default_factory=date.today)
    priority: Priority = Priority.MEDIUM
    requested_by: Optional[str] = None
    notes: Optional[str] = None
    constraints: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator("vehicles")
    def validate_vehicles(cls, v):
        """Validate vehicles list."""
        if not v:
            raise ValueError("At least one vehicle is required")
        return v
    
    @validator("drivers")
    def validate_drivers(cls, v):
        """Validate drivers list."""
        if not v:
            raise ValueError("At least one driver is required")
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class AllocationResult(BaseModel):
    """Represents the result of an allocation."""
    
    request_id: str
    allocations: dict[str, list[str]]  # driver_id -> list of vehicle_ids
    unallocated_vehicles: list[str]
    metrics: Optional[Any] = None  # AllocationMetrics from engine
    status: AllocationStatus = AllocationStatus.PENDING
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @validator("allocations")
    def validate_allocations(cls, v):
        """Validate allocations structure."""
        for driver_id, vehicles in v.items():
            if not isinstance(vehicles, list):
                raise ValueError(f"Vehicles for driver {driver_id} must be a list")
            if len(vehicles) != len(set(vehicles)):
                raise ValueError(f"Duplicate vehicles assigned to driver {driver_id}")
        return v
    
    def get_allocation_summary(self) -> dict[str, Any]:
        """Get a summary of the allocation result.
        
        Returns:
            Dictionary containing allocation summary.
        """
        total_allocated = sum(len(vehicles) for vehicles in self.allocations.values())
        return {
            "request_id": self.request_id,
            "status": self.status,
            "total_drivers": len(self.allocations),
            "total_allocated_vehicles": total_allocated,
            "total_unallocated_vehicles": len(self.unallocated_vehicles),
            "allocation_rate": total_allocated / (total_allocated + len(self.unallocated_vehicles))
            if (total_allocated + len(self.unallocated_vehicles)) > 0 else 0,
            "timestamp": self.timestamp,
            "has_errors": len(self.errors) > 0,
            "has_warnings": len(self.warnings) > 0,
        }
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class AllocationHistory(BaseModel):
    """Represents allocation history entry."""
    
    history_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    result: AllocationResult
    action: str  # "created", "modified", "cancelled", etc.
    performed_by: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }