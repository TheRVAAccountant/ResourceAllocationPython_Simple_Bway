"""Unit tests for pandas Series handling in GASCompatibleAllocator."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from datetime import date

from src.core.gas_compatible_allocator import GASCompatibleAllocator
from src.models.allocation import AllocationResult


class TestGASCompatibleAllocatorPandasFix:
    """Test that GASCompatibleAllocator correctly handles pandas Series objects."""
    
    def test_vehicle_log_dict_with_series_values(self):
        """Test that vehicle_log_dict is created correctly when DataFrame contains Series objects."""
        # Create test data that might cause Series issues
        test_data = pd.DataFrame({
            'Van ID': ['BW1', 'BW2', pd.Series(['BW3']), 'BW4'],  # Mix of strings and Series
            'VIN': ['VIN001', pd.Series(['VIN002']), np.nan, 'VIN004'],
            'GeoTab': ['GT001', 'GT002', pd.Series(['GT003']), ''],  # Mix of strings and Series
            'Branded or Rental': [pd.Series(['Branded']), 'Rental', '', 'Branded']
        })
        
        allocator = GASCompatibleAllocator()
        allocator.vehicle_log_data = test_data
        
        # Mock other required data
        allocator.allocation_results = [
            {
                'Route Code': 'CX1',
                'Van ID': 'BW1',
                'Associate Name': 'Test Driver',
                'Van Type': 'Large'
            }
        ]
        allocator.assigned_van_ids = ['BW1']
        allocator.unassigned_vehicles = pd.DataFrame()
        
        # Create the allocation result
        result = allocator.create_allocation_result()
        
        # Mock the writer
        writer_mock = MagicMock()
        writer_mock.initialize.return_value = None
        writer_mock.validate.return_value = True
        writer_mock.append_to_existing_file.return_value = True
        
        # This should work without pandas Series errors
        with pytest.MonkeyPatch.context() as m:
            m.setattr('src.core.gas_compatible_allocator.DailyDetailsWriter', lambda: writer_mock)
            
            # Should not raise any errors
            allocator.write_results_to_excel(result, 'test_output.xlsx')
            
            # Verify the writer was called with proper vehicle_log_dict
            assert writer_mock.append_to_existing_file.called
            call_args = writer_mock.append_to_existing_file.call_args
            vehicle_log_dict = call_args.kwargs.get('vehicle_log_dict', {})
            
            # Verify all values in vehicle_log_dict are strings, not Series
            for van_id, info in vehicle_log_dict.items():
                assert isinstance(info['vin'], str)
                assert isinstance(info['geotab'], str)
                assert isinstance(info['brand_or_rental'], str)
                assert not isinstance(info['vin'], pd.Series)
                assert not isinstance(info['geotab'], pd.Series)
    
    def test_vehicle_status_fallback_with_series(self):
        """Test Vehicle Status fallback handles Series objects correctly."""
        # Create test Vehicle Status data with Series objects
        test_data = pd.DataFrame({
            'Van ID': ['BW1', pd.Series(['BW2']), 'BW3'],
            'Type': [pd.Series(['Large']), 'Extra Large', 'Step Van'],
            'Opnal? Y/N': ['Y', 'Y', 'Y'],
            'VIN': [pd.Series(['VIN001']), 'VIN002', np.nan],
            'GeoTab Code': ['GT001', pd.Series(['GT002']), '']
        })
        
        allocator = GASCompatibleAllocator()
        allocator.vehicle_status_data = test_data
        allocator.vehicle_log_data = None  # Force Vehicle Status fallback
        
        # Mock other required data
        allocator.allocation_results = []
        allocator.assigned_van_ids = []
        allocator.unassigned_vehicles = pd.DataFrame()
        
        # Create the allocation result
        result = allocator.create_allocation_result()
        
        # Mock the writer
        writer_mock = MagicMock()
        writer_mock.initialize.return_value = None
        writer_mock.validate.return_value = True
        writer_mock.append_to_existing_file.return_value = True
        
        # This should work without pandas Series errors
        with pytest.MonkeyPatch.context() as m:
            m.setattr('src.core.gas_compatible_allocator.DailyDetailsWriter', lambda: writer_mock)
            
            # Should not raise any errors
            allocator.write_results_to_excel(result, 'test_output.xlsx')
            
            # Verify the vehicle_log_dict was created from Vehicle Status
            call_args = writer_mock.append_to_existing_file.call_args
            vehicle_log_dict = call_args.kwargs.get('vehicle_log_dict', {})
            
            # Should have entries for all vehicles
            assert len(vehicle_log_dict) == 3
            
            # Verify all values are strings
            for van_id, info in vehicle_log_dict.items():
                assert isinstance(info['vin'], str)
                assert isinstance(info['geotab'], str)
                assert isinstance(info['vehicle_type'], str)
    
    def test_edge_cases_in_series_extraction(self):
        """Test edge cases like empty Series, None values, etc."""
        test_data = pd.DataFrame({
            'Van ID': ['BW1', pd.Series([]), None, pd.Series(['BW4', 'BW5'])],  # Empty Series, None, Multi-value Series
            'VIN': [pd.Series([None]), '', pd.Series([]), 'VIN004'],
            'GeoTab': [None, pd.Series([np.nan]), '', 'GT004'],
            'Branded or Rental': ['', None, pd.Series([]), pd.Series(['Multi', 'Value'])]
        })
        
        allocator = GASCompatibleAllocator()
        allocator.vehicle_log_data = test_data
        
        # Build vehicle_log_dict using the actual method logic
        vehicle_log_dict = {}
        
        def extract_value(val):
            """Extract scalar value from potentially Series object."""
            if isinstance(val, pd.Series):
                return val.iloc[0] if len(val) > 0 else ""
            return val
        
        for _, vehicle in allocator.vehicle_log_data.iterrows():
            van_id_val = extract_value(vehicle.get("Van ID", ""))
            van_id = str(van_id_val).strip() if pd.notna(van_id_val) else ""
            if not van_id:
                continue
                
            vin_val = extract_value(vehicle.get("VIN", ""))
            geotab_val = extract_value(vehicle.get("GeoTab", ""))
            brand_rental_val = extract_value(vehicle.get("Branded or Rental", ""))
            
            vehicle_log_dict[van_id] = {
                "vin": str(vin_val).strip() if pd.notna(vin_val) else "",
                "geotab": str(geotab_val).strip() if pd.notna(geotab_val) else "",
                "brand_or_rental": str(brand_rental_val).strip() if pd.notna(brand_rental_val) else "",
                "vehicle_type": ""
            }
        
        # Should handle all edge cases gracefully
        assert 'BW1' in vehicle_log_dict
        assert 'BW4' in vehicle_log_dict  # Multi-value Series should use first value
        
        # Empty Series and None values should result in empty strings
        for info in vehicle_log_dict.values():
            assert isinstance(info['vin'], str)
            assert isinstance(info['geotab'], str)
            assert isinstance(info['brand_or_rental'], str)