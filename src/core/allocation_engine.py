"""Core allocation engine for resource distribution."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field, validator

from src.core.base_service import BaseService, error_handler, timer
from src.models.allocation import AllocationRequest, AllocationResult, Driver, Vehicle
from src.services.allocation_history_service import AllocationHistoryService


class AllocationRule(BaseModel):
    """Represents an allocation rule."""

    name: str
    priority: int = Field(ge=0, le=100)
    condition: str
    action: str
    enabled: bool = True

    @validator("priority")
    def validate_priority(cls, v):
        """Validate priority is within range."""
        if not 0 <= v <= 100:
            raise ValueError("Priority must be between 0 and 100")
        return v


class AllocationMetrics(BaseModel):
    """Metrics for allocation performance."""

    total_vehicles: int = 0
    allocated_vehicles: int = 0
    unallocated_vehicles: int = 0
    total_drivers: int = 0
    active_drivers: int = 0
    allocation_rate: Decimal = Decimal("0.0")
    average_vehicles_per_driver: Decimal = Decimal("0.0")
    processing_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class AllocationEngine(BaseService):
    """Engine for managing vehicle allocation to drivers.

    This class implements the core business logic for allocating
    vehicles to drivers based on various rules and constraints.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the allocation engine.

        Args:
            config: Configuration dictionary.
        """
        super().__init__(config)
        self.rules: list[AllocationRule] = []
        self.metrics = AllocationMetrics()
        self.allocation_history: list[AllocationResult] = []

        # Initialize history service
        self.history_service = AllocationHistoryService()
        self.history_service.initialize()

        # Configuration parameters
        self.max_vehicles_per_driver = self.get_config("max_vehicles_per_driver", 3)
        self.min_vehicles_per_driver = self.get_config("min_vehicles_per_driver", 1)
        self.priority_weight = self.get_config("priority_weight_factor", 1.5)
        self.allocation_threshold = self.get_config("allocation_threshold", 0.8)

    def initialize(self) -> None:
        """Initialize the allocation engine."""
        logger.info("Initializing Allocation Engine")
        self._load_allocation_rules()
        self._initialized = True

    def validate(self) -> bool:
        """Validate the engine configuration.

        Returns:
            True if configuration is valid.
        """
        if self.max_vehicles_per_driver < self.min_vehicles_per_driver:
            logger.error("Max vehicles per driver less than minimum")
            return False

        if self.allocation_threshold < 0 or self.allocation_threshold > 1:
            logger.error("Allocation threshold must be between 0 and 1")
            return False

        return True

    def _load_allocation_rules(self) -> None:
        """Load allocation rules from configuration."""
        # Default rules - in production, these would come from config/database
        default_rules = [
            AllocationRule(
                name="Priority Assignment",
                priority=100,
                condition="driver.priority == 'high'",
                action="allocate_first",
            ),
            AllocationRule(
                name="Experience Based",
                priority=80,
                condition="driver.experience_years > 5",
                action="allocate_premium_vehicles",
            ),
            AllocationRule(
                name="Balanced Distribution",
                priority=50,
                condition="True",
                action="distribute_evenly",
            ),
            AllocationRule(
                name="Location Based",
                priority=60,
                condition="driver.location == vehicle.location",
                action="prefer_same_location",
            ),
        ]

        self.rules = sorted(default_rules, key=lambda r: r.priority, reverse=True)
        logger.info(f"Loaded {len(self.rules)} allocation rules")

    @timer
    @error_handler
    def allocate(self, request: AllocationRequest) -> AllocationResult:
        """Perform vehicle allocation based on the request.

        Args:
            request: The allocation request containing vehicles and drivers.

        Returns:
            The allocation result with assignments.
        """
        logger.info(
            f"Starting allocation for {len(request.vehicles)} vehicles "
            f"and {len(request.drivers)} drivers"
        )

        start_time = datetime.now()

        # Initialize allocation tracking
        available_vehicles = request.vehicles.copy()
        available_drivers = request.drivers.copy()
        allocations = {}
        unallocated_vehicles = []

        # Apply rules in priority order
        for rule in self.rules:
            if not rule.enabled:
                continue

            logger.debug(f"Applying rule: {rule.name} (priority: {rule.priority})")

            if rule.action == "allocate_first":
                allocations, available_vehicles, available_drivers = self._allocate_priority(
                    allocations, available_vehicles, available_drivers, rule
                )
            elif rule.action == "allocate_premium_vehicles":
                allocations, available_vehicles, available_drivers = self._allocate_premium(
                    allocations, available_vehicles, available_drivers, rule
                )
            elif rule.action == "distribute_evenly":
                allocations, available_vehicles, available_drivers = self._distribute_evenly(
                    allocations, available_vehicles, available_drivers
                )
            elif rule.action == "prefer_same_location":
                allocations, available_vehicles, available_drivers = self._allocate_by_location(
                    allocations, available_vehicles, available_drivers
                )

        # Handle remaining unallocated vehicles
        unallocated_vehicles = available_vehicles

        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        self._update_metrics(request, allocations, unallocated_vehicles, processing_time)

        # Create result
        result = AllocationResult(
            request_id=request.request_id,
            allocations=allocations,
            unallocated_vehicles=[v.vehicle_id for v in unallocated_vehicles],
            metrics=self.metrics,
            status="completed" if not unallocated_vehicles else "partial",
            timestamp=datetime.now(),
        )

        # Store in history
        self.allocation_history.append(result)

        # Save to persistent history service
        try:
            self.history_service.save_allocation(
                result=result,
                engine_name="AllocationEngine",
                files={},  # Legacy engine - no file tracking
                duplicate_conflicts=[],
                error=None,
            )
        except Exception as e:
            logger.error(f"Failed to save allocation to history: {e}")

        logger.info(
            f"Allocation completed: {len(allocations)} assignments, "
            f"{len(unallocated_vehicles)} unallocated"
        )

        return result

    def _allocate_priority(
        self,
        allocations: dict,
        vehicles: list[Vehicle],
        drivers: list[Driver],
        _rule: AllocationRule,
    ) -> tuple[dict, list[Vehicle], list[Driver]]:
        """Allocate vehicles to priority drivers first.

        Args:
            allocations: Current allocations dictionary.
            vehicles: Available vehicles.
            drivers: Available drivers.
            rule: The allocation rule.

        Returns:
            Updated allocations, vehicles, and drivers.
        """
        priority_drivers = [d for d in drivers if d.priority == "high"]

        for driver in priority_drivers:
            if not vehicles:
                break

            max_allowed = min(self.max_vehicles_per_driver, len(vehicles))

            driver_vehicles = []
            for _ in range(max_allowed):
                if vehicles:
                    vehicle = vehicles.pop(0)
                    driver_vehicles.append(vehicle.vehicle_id)

            if driver_vehicles:
                allocations[driver.driver_id] = driver_vehicles
                drivers.remove(driver)

        return allocations, vehicles, drivers

    def _allocate_premium(
        self,
        allocations: dict,
        vehicles: list[Vehicle],
        drivers: list[Driver],
        _rule: AllocationRule,
    ) -> tuple[dict, list[Vehicle], list[Driver]]:
        """Allocate premium vehicles to experienced drivers.

        Args:
            allocations: Current allocations dictionary.
            vehicles: Available vehicles.
            drivers: Available drivers.
            rule: The allocation rule.

        Returns:
            Updated allocations, vehicles, and drivers.
        """
        experienced_drivers = [d for d in drivers if d.experience_years > 5]
        premium_vehicles = [v for v in vehicles if v.vehicle_type == "premium"]

        for driver in experienced_drivers:
            if not premium_vehicles:
                break

            if driver.driver_id not in allocations:
                allocations[driver.driver_id] = []

            vehicle = premium_vehicles.pop(0)
            allocations[driver.driver_id].append(vehicle.vehicle_id)
            vehicles.remove(vehicle)

            if len(allocations[driver.driver_id]) >= self.max_vehicles_per_driver:
                drivers.remove(driver)

        return allocations, vehicles, drivers

    def _distribute_evenly(
        self, allocations: dict, vehicles: list[Vehicle], drivers: list[Driver]
    ) -> tuple[dict, list[Vehicle], list[Driver]]:
        """Distribute vehicles evenly among drivers.

        Args:
            allocations: Current allocations dictionary.
            vehicles: Available vehicles.
            drivers: Available drivers.

        Returns:
            Updated allocations, vehicles, and drivers.
        """
        if not drivers or not vehicles:
            return allocations, vehicles, drivers

        vehicles_per_driver = max(self.min_vehicles_per_driver, len(vehicles) // len(drivers))
        vehicles_per_driver = min(vehicles_per_driver, self.max_vehicles_per_driver)

        for driver in drivers[:]:
            if not vehicles:
                break

            if driver.driver_id not in allocations:
                allocations[driver.driver_id] = []

            current_count = len(allocations[driver.driver_id])
            needed = vehicles_per_driver - current_count

            for _ in range(min(needed, len(vehicles))):
                vehicle = vehicles.pop(0)
                allocations[driver.driver_id].append(vehicle.vehicle_id)

            if len(allocations[driver.driver_id]) >= vehicles_per_driver:
                drivers.remove(driver)

        return allocations, vehicles, drivers

    def _allocate_by_location(
        self, allocations: dict, vehicles: list[Vehicle], drivers: list[Driver]
    ) -> tuple[dict, list[Vehicle], list[Driver]]:
        """Allocate vehicles based on location matching.

        Args:
            allocations: Current allocations dictionary.
            vehicles: Available vehicles.
            drivers: Available drivers.

        Returns:
            Updated allocations, vehicles, and drivers.
        """
        for driver in drivers[:]:
            if not vehicles:
                break

            # Find vehicles in the same location
            same_location = [v for v in vehicles if v.location == driver.location]

            if same_location:
                if driver.driver_id not in allocations:
                    allocations[driver.driver_id] = []

                max_allowed = self.max_vehicles_per_driver - len(allocations[driver.driver_id])

                for vehicle in same_location[:max_allowed]:
                    allocations[driver.driver_id].append(vehicle.vehicle_id)
                    vehicles.remove(vehicle)

                if len(allocations[driver.driver_id]) >= self.max_vehicles_per_driver:
                    drivers.remove(driver)

        return allocations, vehicles, drivers

    def _update_metrics(
        self,
        request: AllocationRequest,
        allocations: dict,
        unallocated: list[Vehicle],
        processing_time: float,
    ) -> None:
        """Update allocation metrics.

        Args:
            request: The original allocation request.
            allocations: The final allocations.
            unallocated: List of unallocated vehicles.
            processing_time: Time taken to process allocation.
        """
        total_vehicles = len(request.vehicles)
        allocated_vehicles = sum(len(v) for v in allocations.values())

        self.metrics = AllocationMetrics(
            total_vehicles=total_vehicles,
            allocated_vehicles=allocated_vehicles,
            unallocated_vehicles=len(unallocated),
            total_drivers=len(request.drivers),
            active_drivers=len(allocations),
            allocation_rate=Decimal(str(allocated_vehicles / total_vehicles))
            if total_vehicles > 0
            else Decimal("0"),
            average_vehicles_per_driver=Decimal(str(allocated_vehicles / len(allocations)))
            if allocations
            else Decimal("0"),
            processing_time=processing_time,
            timestamp=datetime.now(),
        )

    def get_metrics(self) -> AllocationMetrics:
        """Get current allocation metrics.

        Returns:
            The current metrics.
        """
        return self.metrics

    def get_history(self, limit: int | None = None) -> list[AllocationResult]:
        """Get allocation history.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of allocation results.
        """
        if limit:
            return self.allocation_history[-limit:]
        return self.allocation_history

    def optimize_allocation(self, request: AllocationRequest) -> AllocationRequest:
        """Optimize the allocation request before processing.

        Args:
            request: The allocation request to optimize.

        Returns:
            Optimized allocation request.
        """
        logger.info("Optimizing allocation request")

        # Sort vehicles by priority and type
        request.vehicles.sort(key=lambda v: (v.priority, v.vehicle_type), reverse=True)

        # Sort drivers by priority and experience
        request.drivers.sort(key=lambda d: (d.priority == "high", d.experience_years), reverse=True)

        return request

    def validate_allocation(self, result: AllocationResult) -> bool:
        """Validate an allocation result.

        Args:
            result: The allocation result to validate.

        Returns:
            True if the allocation is valid.
        """
        # Check for duplicate vehicle assignments
        all_vehicles = []
        for vehicles in result.allocations.values():
            all_vehicles.extend(vehicles)

        if len(all_vehicles) != len(set(all_vehicles)):
            logger.error("Duplicate vehicle assignments detected")
            return False

        # Check vehicle count constraints
        for driver_id, vehicles in result.allocations.items():
            if len(vehicles) > self.max_vehicles_per_driver:
                logger.error(f"Driver {driver_id} has too many vehicles")
                return False

        return True
