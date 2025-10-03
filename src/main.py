"""Main application entry point for Resource Management System."""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional
from loguru import logger
import click
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.allocation_engine import AllocationEngine
from src.services.excel_service import ExcelService
from src.services.border_formatting_service import BorderFormattingService
from src.models.allocation import (
    Vehicle, Driver, AllocationRequest,
    VehicleType, Priority
)


# Load environment variables
load_dotenv()

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/resource_allocation_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG"
)


class ResourceAllocationApp:
    """Main application class for Resource Management System."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the application.
        
        Args:
            config_path: Path to configuration file.
        """
        self.config = self._load_config(config_path)
        self.allocation_engine = None
        self.excel_service = None
        self.border_service = None
        
    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration from file or environment.
        
        Args:
            config_path: Path to configuration file.
        
        Returns:
            Configuration dictionary.
        """
        config = {
            "max_vehicles_per_driver": 3,
            "min_vehicles_per_driver": 1,
            "priority_weight_factor": 1.5,
            "allocation_threshold": 0.8,
            "excel_visible": False,
            "display_alerts": False,
            "use_xlwings": True,
        }
        
        # Load from config file if provided
        if config_path and Path(config_path).exists():
            import json
            with open(config_path) as f:
                config.update(json.load(f))
        
        return config
    
    def initialize_services(self):
        """Initialize all services."""
        logger.info("Initializing services...")
        
        # Initialize allocation engine
        self.allocation_engine = AllocationEngine(self.config)
        self.allocation_engine.initialize()
        
        # Initialize Excel service
        self.excel_service = ExcelService(self.config)
        self.excel_service.initialize()
        
        # Initialize border formatting service
        self.border_service = BorderFormattingService(self.config)
        self.border_service.initialize()
        
        logger.info("Services initialized successfully")
    
    def cleanup_services(self):
        """Clean up all services."""
        if self.excel_service:
            self.excel_service.cleanup()
        if self.allocation_engine:
            self.allocation_engine.cleanup()
        if self.border_service:
            self.border_service.cleanup()
    
    def run_allocation(
        self,
        input_file: str,
        output_file: str,
        allocation_date: Optional[date] = None,
        open_output: bool = False
    ):
        """Run the allocation process.
        
        Args:
            input_file: Path to input Excel file.
            output_file: Path to output Excel file.
            allocation_date: Date for allocation (defaults to today).
        """
        try:
            logger.info(f"Starting allocation process")
            logger.info(f"Input: {input_file}, Output: {output_file}")
            
            # Initialize services
            self.initialize_services()
            
            # Load input data
            vehicles, drivers = self._load_input_data(input_file)
            
            # Create allocation request
            request = AllocationRequest(
                vehicles=vehicles,
                drivers=drivers,
                allocation_date=allocation_date or date.today(),
                priority=Priority.MEDIUM,
                requested_by="System"
            )
            
            # Optimize and perform allocation
            optimized_request = self.allocation_engine.optimize_allocation(request)
            result = self.allocation_engine.allocate(optimized_request)
            
            # Validate result
            if not self.allocation_engine.validate_allocation(result):
                logger.error("Allocation validation failed")
                return False
            
            # Write output
            self._write_output(output_file, result, allocation_date or date.today())

            # Optionally open the output file (CLI flag)
            if open_output:
                self._open_file_cross_platform(output_file)
            
            # Log summary
            summary = result.get_allocation_summary()
            logger.info(f"Allocation completed successfully")
            logger.info(f"Total drivers: {summary['total_drivers']}")
            logger.info(f"Allocated vehicles: {summary['total_allocated_vehicles']}")
            logger.info(f"Unallocated vehicles: {summary['total_unallocated_vehicles']}")
            logger.info(f"Allocation rate: {summary['allocation_rate']:.2%}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during allocation: {str(e)}")
            raise
        finally:
            self.cleanup_services()
    
    def _load_input_data(self, input_file: str) -> tuple[list[Vehicle], list[Driver]]:
        """Load vehicles and drivers from input file.
        
        Args:
            input_file: Path to input Excel file.
        
        Returns:
            Tuple of (vehicles, drivers).
        """
        logger.info(f"Loading input data from {input_file}")
        
        # Open workbook
        self.excel_service.open_workbook(input_file)
        
        # Read vehicles data
        vehicles_df = self.excel_service.read_data("Vehicles", as_dataframe=True)
        vehicles = []
        for _, row in vehicles_df.iterrows():
            vehicle = Vehicle(
                vehicle_number=row.get("Vehicle Number", ""),
                vehicle_type=VehicleType(row.get("Type", "standard").lower()),
                location=row.get("Location", "Main"),
                status=row.get("Status", "available"),
                priority=int(row.get("Priority", 50)),
                capacity=row.get("Capacity"),
                notes=row.get("Notes")
            )
            vehicles.append(vehicle)
        
        # Read drivers data
        drivers_df = self.excel_service.read_data("Drivers", as_dataframe=True)
        drivers = []
        for _, row in drivers_df.iterrows():
            driver = Driver(
                employee_id=row.get("Employee ID", ""),
                name=row.get("Name", ""),
                location=row.get("Location", "Main"),
                status=row.get("Status", "active"),
                priority=Priority(row.get("Priority", "medium").lower()),
                experience_years=int(row.get("Experience", 0)),
                license_type=row.get("License Type", "standard"),
                max_vehicles=int(row.get("Max Vehicles", 3)),
                notes=row.get("Notes")
            )
            drivers.append(driver)
        
        logger.info(f"Loaded {len(vehicles)} vehicles and {len(drivers)} drivers")
        return vehicles, drivers
    
    def _write_output(self, output_file: str, result, allocation_date: date):
        """Write allocation results to output file.
        
        Args:
            output_file: Path to output Excel file.
            result: Allocation result.
            allocation_date: Date of allocation.
        """
        logger.info(f"Writing output to {output_file}")
        
        # Create new workbook
        self.excel_service.create_workbook()
        
        # Create allocation sheet
        sheet = self.excel_service.create_sheet("Allocations")
        
        # Write allocation data
        self.excel_service.write_allocation_result("Allocations", result, start_row=3)
        
        # Apply daily section formatting
        self.border_service.create_daily_section(
            sheet=sheet,
            start_row=1,
            start_col=1,
            end_row=20,
            end_col=5,
            section_date=allocation_date,
            title="Vehicle Allocation"
        )
        
        # Create summary sheet
        summary_sheet = self.excel_service.create_sheet("Summary")
        summary_data = {
            "Request ID": result.request_id,
            "Status": result.status,
            "Timestamp": result.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Total Drivers": len(result.allocations),
            "Total Allocated": sum(len(v) for v in result.allocations.values()),
            "Total Unallocated": len(result.unallocated_vehicles),
            "Processing Time": f"{result.processing_time:.2f}s" if result.processing_time else "N/A"
        }
        
        self.excel_service.write_data("Summary", summary_data, start_row=1, start_col=1)
        
        # Save workbook
        self.excel_service.save_workbook(output_file)
        logger.info(f"Output saved to {output_file}")

    def _open_file_cross_platform(self, path: str):
        """Attempt to open a file with the OS default application.

        Non-fatal on failure; logs an info/warning.
        """
        try:
            import os, platform, time
            sysname = platform.system()
            if sysname == 'Windows':
                try:
                    os.startfile(path)  # type: ignore[attr-defined]
                except Exception:
                    # Retry briefly in case of transient locks
                    time.sleep(0.5)
                    os.startfile(path)  # type: ignore[attr-defined]
            elif sysname == 'Darwin':
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
            logger.info(f"Opened output file: {path}")
        except Exception as e:
            logger.warning(f"Could not open output file '{path}': {e}")
    
    def create_sample_data(self, output_file: str):
        """Create sample input data file.
        
        Args:
            output_file: Path to save sample data.
        """
        logger.info(f"Creating sample data file: {output_file}")
        
        # Initialize services
        self.initialize_services()
        
        try:
            # Create workbook
            self.excel_service.create_workbook()
            
            # Create vehicles sheet
            vehicles_data = []
            for i in range(1, 21):
                vehicles_data.append({
                    "Vehicle Number": f"VEH{i:03d}",
                    "Type": ["standard", "premium", "economy"][i % 3],
                    "Location": ["Main", "North", "South"][i % 3],
                    "Status": "available",
                    "Priority": 50 + (i % 3) * 10,
                    "Capacity": 4 + (i % 2) * 2,
                    "Notes": f"Vehicle {i}"
                })
            
            import pandas as pd
            vehicles_df = pd.DataFrame(vehicles_data)
            self.excel_service.create_sheet("Vehicles")
            self.excel_service.write_data("Vehicles", vehicles_df)
            
            # Create drivers sheet
            drivers_data = []
            for i in range(1, 11):
                drivers_data.append({
                    "Employee ID": f"EMP{i:03d}",
                    "Name": f"Driver {i}",
                    "Location": ["Main", "North", "South"][i % 3],
                    "Status": "active",
                    "Priority": ["low", "medium", "high"][i % 3],
                    "Experience": i % 10,
                    "License Type": "standard",
                    "Max Vehicles": 3,
                    "Notes": f"Driver {i} notes"
                })
            
            drivers_df = pd.DataFrame(drivers_data)
            self.excel_service.create_sheet("Drivers")
            self.excel_service.write_data("Drivers", drivers_df)
            
            # Save workbook
            self.excel_service.save_workbook(output_file)
            logger.info(f"Sample data saved to {output_file}")
            
        finally:
            self.cleanup_services()


@click.group()
def cli():
    """Resource Management System CLI."""
    pass


@cli.command()
@click.option('--input', '-i', 'input_file', required=True, help='Input Excel file')
@click.option('--output', '-o', 'output_file', required=True, help='Output Excel file')
@click.option('--date', '-d', 'allocation_date', help='Allocation date (YYYY-MM-DD)')
@click.option('--config', '-c', 'config_file', help='Configuration file')
@click.option('--open-output/--no-open-output', default=False, help='Open the output file after allocation completes')
def allocate(input_file, output_file, allocation_date, config_file, open_output):
    """Run vehicle allocation."""
    app = ResourceAllocationApp(config_file)
    
    # Parse date if provided
    if allocation_date:
        allocation_date = datetime.strptime(allocation_date, "%Y-%m-%d").date()
    
    success = app.run_allocation(input_file, output_file, allocation_date, open_output=open_output)
    
    if success:
        click.echo(click.style("✓ Allocation completed successfully", fg="green"))
    else:
        click.echo(click.style("✗ Allocation failed", fg="red"))
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', 'output_file', default='sample_data.xlsx', help='Output file')
def create_sample(output_file):
    """Create sample input data."""
    app = ResourceAllocationApp()
    app.create_sample_data(output_file)
    click.echo(click.style(f"✓ Sample data created: {output_file}", fg="green"))


@cli.command()
def version():
    """Show version information."""
    from src import __version__
    click.echo(f"Resource Management System v{__version__}")


if __name__ == "__main__":
    cli()
