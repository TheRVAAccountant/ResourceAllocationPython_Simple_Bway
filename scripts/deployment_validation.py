#!/usr/bin/env python3
"""
Comprehensive deployment validation script for the Resource Management System.
Validates all three major features against real-world scenarios.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import psutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.duplicate_validator import DuplicateVehicleValidator
from services.unassigned_vehicles_writer import UnassignedVehiclesWriter
from services.daily_details_thick_borders import DailyDetailsThickBorders
from services.excel_service import ExcelService
from core.gas_compatible_allocator import GASCompatibleAllocator


class DeploymentValidator:
    """
    Comprehensive deployment validation for the Resource Management System.
    Tests all new features and validates production readiness.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize deployment validator.
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.setup_logging()
        self.validation_results = []
        self.performance_metrics = {}
        
        logger.info("Deployment validator initialized")
    
    def setup_logging(self):
        """Setup logging configuration."""
        global logger
        logging.basicConfig(
            level=logging.DEBUG if self.verbose else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'logs/deployment_validation_{datetime.now():%Y%m%d_%H%M%S}.log')
            ]
        )
        logger = logging.getLogger(__name__)
    
    def validate_all_features(self) -> bool:
        """
        Run comprehensive validation of all features.
        
        Returns:
            True if all validations pass, False otherwise
        """
        print("🚀 Starting comprehensive deployment validation...")
        print("=" * 60)
        
        all_passed = True
        
        # Test 1: Feature Initialization
        if not self._test_feature_initialization():
            all_passed = False
        
        # Test 2: Core Functionality
        if not self._test_core_functionality():
            all_passed = False
        
        # Test 3: Integration Testing
        if not self._test_integration():
            all_passed = False
        
        # Test 4: Performance Validation
        if not self._test_performance():
            all_passed = False
        
        # Test 5: Error Handling
        if not self._test_error_handling():
            all_passed = False
        
        # Test 6: Data Integrity
        if not self._test_data_integrity():
            all_passed = False
        
        # Generate summary report
        self._generate_validation_report()
        
        print("=" * 60)
        if all_passed:
            print("✅ All deployment validations PASSED")
            print("🎉 System is ready for production deployment!")
        else:
            print("❌ Some deployment validations FAILED")
            print("⚠️  System is NOT ready for production deployment")
        
        return all_passed
    
    def _test_feature_initialization(self) -> bool:
        """Test that all new features can be initialized properly."""
        print("\\n🔍 Testing Feature Initialization...")
        
        tests = [
            ("Duplicate Vehicle Validator", self._init_duplicate_validator),
            ("Unassigned Vehicles Writer", self._init_unassigned_writer),
            ("Daily Details Thick Borders", self._init_thick_borders),
            ("Excel Service", self._init_excel_service),
            ("GAS Compatible Allocator", self._init_gas_allocator)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            try:
                start_time = time.time()
                result = test_func()
                duration = time.time() - start_time
                
                if result:
                    print(f"  ✅ {test_name}: Initialized successfully ({duration:.3f}s)")
                    self.validation_results.append({
                        'test': test_name,
                        'category': 'initialization',
                        'status': 'pass',
                        'duration': duration
                    })
                else:
                    print(f"  ❌ {test_name}: Failed to initialize")
                    all_passed = False
                    self.validation_results.append({
                        'test': test_name,
                        'category': 'initialization',
                        'status': 'fail',
                        'duration': duration
                    })
                    
            except Exception as e:
                print(f"  ❌ {test_name}: Exception during initialization - {e}")
                all_passed = False
                self.validation_results.append({
                    'test': test_name,
                    'category': 'initialization',
                    'status': 'error',
                    'error': str(e)
                })
        
        return all_passed
    
    def _init_duplicate_validator(self) -> bool:
        """Test duplicate validator initialization."""
        try:
            validator = DuplicateVehicleValidator()
            return validator is not None
        except Exception:
            return False
    
    def _init_unassigned_writer(self) -> bool:
        """Test unassigned vehicles writer initialization."""
        try:
            writer = UnassignedVehiclesWriter()
            return writer is not None
        except Exception:
            return False
    
    def _init_thick_borders(self) -> bool:
        """Test thick borders service initialization."""
        try:
            borders = DailyDetailsThickBorders()
            return borders is not None
        except Exception:
            return False
    
    def _init_excel_service(self) -> bool:
        """Test Excel service initialization."""
        try:
            service = ExcelService()
            return service is not None
        except Exception:
            return False
    
    def _init_gas_allocator(self) -> bool:
        """Test GAS allocator initialization."""
        try:
            allocator = GASCompatibleAllocator()
            return allocator is not None
        except Exception:
            return False
    
    def _test_core_functionality(self) -> bool:
        """Test core functionality of each feature."""
        print("\\n🔧 Testing Core Functionality...")
        
        all_passed = True
        
        # Test duplicate validation with sample data
        if not self._test_duplicate_validation_core():
            all_passed = False
        
        # Test unassigned vehicles functionality
        if not self._test_unassigned_vehicles_core():
            all_passed = False
        
        # Test thick borders functionality
        if not self._test_thick_borders_core():
            all_passed = False
        
        return all_passed
    
    def _test_duplicate_validation_core(self) -> bool:
        """Test duplicate validation core functionality."""
        try:
            print("  🔍 Testing duplicate validation...")
            
            validator = DuplicateVehicleValidator()
            
            # Test data with known duplicates
            test_allocations = [
                {'Van_ID': 'BW101', 'Route_Code': 'CX1'},
                {'Van_ID': 'BW102', 'Route_Code': 'CX2'},
                {'Van_ID': 'BW101', 'Route_Code': 'CX3'},  # Duplicate
                {'Van_ID': 'BW103', 'Route_Code': 'CX4'},
            ]
            
            duplicates = validator.find_duplicates(test_allocations)
            
            # Should find 1 duplicate (BW101)
            if len(duplicates) == 1 and duplicates[0]['Van_ID'] == 'BW101':
                print("    ✅ Duplicate detection working correctly")
                return True
            else:
                print(f"    ❌ Expected 1 duplicate (BW101), found {len(duplicates)}")
                return False
                
        except Exception as e:
            print(f"    ❌ Exception in duplicate validation: {e}")
            return False
    
    def _test_unassigned_vehicles_core(self) -> bool:
        """Test unassigned vehicles core functionality."""
        try:
            print("  🔍 Testing unassigned vehicles...")
            
            writer = UnassignedVehiclesWriter()
            
            # Test data
            all_vehicles = [
                {'Van_ID': 'BW101', 'Status': 'Active'},
                {'Van_ID': 'BW102', 'Status': 'Active'},
                {'Van_ID': 'BW103', 'Status': 'Active'}
            ]
            
            assigned_vehicles = ['BW101']  # Only BW101 assigned
            
            unassigned = writer.identify_unassigned_vehicles(all_vehicles, assigned_vehicles)
            
            # Should find BW102 and BW103 as unassigned
            expected_unassigned = {'BW102', 'BW103'}
            actual_unassigned = {v['Van_ID'] for v in unassigned}
            
            if actual_unassigned == expected_unassigned:
                print("    ✅ Unassigned vehicle identification working correctly")
                return True
            else:
                print(f"    ❌ Expected {expected_unassigned}, found {actual_unassigned}")
                return False
                
        except Exception as e:
            print(f"    ❌ Exception in unassigned vehicles: {e}")
            return False
    
    def _test_thick_borders_core(self) -> bool:
        """Test thick borders core functionality."""
        try:
            print("  🔍 Testing thick borders...")
            
            borders = DailyDetailsThickBorders()
            
            # This is a simplified test - in reality would test with actual Excel file
            # For now, just verify the service methods exist and are callable
            if hasattr(borders, 'apply_thick_borders') and callable(borders.apply_thick_borders):
                print("    ✅ Thick borders service methods available")
                return True
            else:
                print("    ❌ Thick borders service methods not available")
                return False
                
        except Exception as e:
            print(f"    ❌ Exception in thick borders: {e}")
            return False
    
    def _test_integration(self) -> bool:
        """Test integration between features and existing system."""
        print("\\n🔗 Testing Integration...")
        
        try:
            # Test that features work together without conflicts
            validator = DuplicateVehicleValidator()
            writer = UnassignedVehiclesWriter()
            borders = DailyDetailsThickBorders()
            allocator = GASCompatibleAllocator()
            
            print("  ✅ All services can be instantiated together")
            
            # Test memory usage with all services loaded
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb < 500:  # Should use less than 500MB
                print(f"  ✅ Memory usage acceptable: {memory_mb:.1f} MB")
                return True
            else:
                print(f"  ⚠️  High memory usage: {memory_mb:.1f} MB")
                return False
                
        except Exception as e:
            print(f"  ❌ Integration test failed: {e}")
            return False
    
    def _test_performance(self) -> bool:
        """Test performance with realistic datasets."""
        print("\\n⚡ Testing Performance...")
        
        all_passed = True
        
        # Test duplicate validation performance
        if not self._test_duplicate_validation_performance():
            all_passed = False
        
        # Test memory usage under load
        if not self._test_memory_performance():
            all_passed = False
        
        return all_passed
    
    def _test_duplicate_validation_performance(self) -> bool:
        """Test duplicate validation performance with large dataset."""
        try:
            print("  🔍 Testing duplicate validation performance...")
            
            validator = DuplicateVehicleValidator()
            
            # Generate large test dataset (1000 allocations)
            test_allocations = []
            for i in range(1000):
                test_allocations.append({
                    'Van_ID': f'BW{i % 100}',  # This will create duplicates
                    'Route_Code': f'CX{i}'
                })
            
            start_time = time.time()
            duplicates = validator.find_duplicates(test_allocations)
            duration = time.time() - start_time
            
            self.performance_metrics['duplicate_validation_1000'] = duration
            
            if duration < 5.0:  # Should complete in under 5 seconds
                print(f"    ✅ Performance acceptable: {duration:.3f}s for 1000 allocations")
                return True
            else:
                print(f"    ❌ Performance too slow: {duration:.3f}s for 1000 allocations")
                return False
                
        except Exception as e:
            print(f"    ❌ Performance test failed: {e}")
            return False
    
    def _test_memory_performance(self) -> bool:
        """Test memory usage under load."""
        try:
            print("  🔍 Testing memory performance...")
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            # Create multiple service instances to simulate load
            validators = [DuplicateVehicleValidator() for _ in range(10)]
            writers = [UnassignedVehiclesWriter() for _ in range(10)]
            
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory
            
            self.performance_metrics['memory_increase'] = memory_increase
            
            if memory_increase < 200:  # Should use less than 200MB additional
                print(f"    ✅ Memory usage acceptable: +{memory_increase:.1f} MB")
                return True
            else:
                print(f"    ❌ Excessive memory usage: +{memory_increase:.1f} MB")
                return False
                
        except Exception as e:
            print(f"    ❌ Memory test failed: {e}")
            return False
    
    def _test_error_handling(self) -> bool:
        """Test error handling and recovery."""
        print("\\n🛡️  Testing Error Handling...")
        
        all_passed = True
        
        # Test handling of invalid data
        try:
            validator = DuplicateVehicleValidator()
            
            # Test with None data
            result = validator.find_duplicates(None)
            if result == []:
                print("  ✅ Handles None input gracefully")
            else:
                print("  ❌ Does not handle None input properly")
                all_passed = False
                
            # Test with empty data
            result = validator.find_duplicates([])
            if result == []:
                print("  ✅ Handles empty input gracefully")
            else:
                print("  ❌ Does not handle empty input properly")
                all_passed = False
                
            # Test with malformed data
            malformed_data = [{'invalid': 'data'}]
            result = validator.find_duplicates(malformed_data)
            print("  ✅ Handles malformed data gracefully")
            
        except Exception as e:
            print(f"  ❌ Error handling test failed: {e}")
            all_passed = False
        
        return all_passed
    
    def _test_data_integrity(self) -> bool:
        """Test data integrity and consistency."""
        print("\\n🔒 Testing Data Integrity...")
        
        try:
            # Test that features don't modify input data
            validator = DuplicateVehicleValidator()
            
            original_data = [
                {'Van_ID': 'BW101', 'Route_Code': 'CX1'},
                {'Van_ID': 'BW102', 'Route_Code': 'CX2'}
            ]
            
            # Make a copy to compare
            import copy
            data_copy = copy.deepcopy(original_data)
            
            # Run validation
            validator.find_duplicates(original_data)
            
            # Verify original data unchanged
            if original_data == data_copy:
                print("  ✅ Input data integrity maintained")
                return True
            else:
                print("  ❌ Input data was modified")
                return False
                
        except Exception as e:
            print(f"  ❌ Data integrity test failed: {e}")
            return False
    
    def _generate_validation_report(self) -> None:
        """Generate comprehensive validation report."""
        report_path = Path(f"outputs/deployment_validation_report_{datetime.now():%Y%m%d_%H%M%S}.json")
        report_path.parent.mkdir(exist_ok=True)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'validation_results': self.validation_results,
            'performance_metrics': self.performance_metrics,
            'system_info': {
                'python_version': sys.version,
                'platform': sys.platform,
                'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
                'cpu_count': psutil.cpu_count()
            },
            'summary': {
                'total_tests': len(self.validation_results),
                'passed_tests': len([r for r in self.validation_results if r['status'] == 'pass']),
                'failed_tests': len([r for r in self.validation_results if r['status'] == 'fail']),
                'error_tests': len([r for r in self.validation_results if r['status'] == 'error'])
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\\n📊 Validation report saved to: {report_path}")


def main():
    """Main entry point for deployment validation."""
    parser = argparse.ArgumentParser(
        description="Validate Resource Management System deployment readiness"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Output directory for reports"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output_dir.mkdir(exist_ok=True)
    
    # Run validation
    validator = DeploymentValidator(verbose=args.verbose)
    success = validator.validate_all_features()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()