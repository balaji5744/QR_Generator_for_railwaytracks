"""
Data Validation Module for Railway QR Code System
Validates QR data format and component specifications
"""

import re
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAILWAY_REGIONS, RAILWAY_DIVISIONS, COMPONENT_TYPES


class RailwayDataValidator:
    """Validates railway component data and QR code formats"""
    
    def __init__(self):
        self.qr_pattern = re.compile(
            r'^IR-([A-Z]{2})-([A-Z0-9]{2,5})-(\d{3})-(\d{6})-([A-Z]+)-(\d{4})-(\d{6})$'
        )
    
    def validate_qr_format(self, qr_data):
        """
        Validate QR code data format
        
        Parameters:
        - qr_data: str (QR code data string)
        
        Returns:
        - is_valid: bool
        - parsed_data: dict (parsed components if valid)
        - error_message: str (error description if invalid)
        """
        
        if not isinstance(qr_data, str):
            return False, None, "QR data must be a string"
        
        match = self.qr_pattern.match(qr_data)
        if not match:
            return False, None, "QR data format is invalid"
        
        # Extract components
        region, division, track_id, km_marker, component_type, year, serial_number = match.groups()
        
        # Validate individual components
        validation_result = self.validate_components(
            region, division, int(track_id), int(km_marker), 
            component_type, int(year), int(serial_number)
        )
        
        if not validation_result['is_valid']:
            return False, None, validation_result['error_message']
        
        # Return parsed data
        parsed_data = {
            'region': region,
            'division': division,
            'track_id': int(track_id),
            'km_marker': int(km_marker),
            'component_type': component_type,
            'year': int(year),
            'serial_number': int(serial_number),
            'full_data': qr_data
        }
        
        return True, parsed_data, None
    
    def validate_components(self, region, division, track_id, km_marker, 
                           component_type, year, serial_number):
        """
        Validate individual component parameters
        
        Returns:
        - dict with 'is_valid', 'error_message' keys
        """
        
        # Validate region
        if region not in RAILWAY_REGIONS:
            return {
                'is_valid': False,
                'error_message': f"Invalid region: {region}. Must be one of {list(RAILWAY_REGIONS.keys())}"
            }
        
        # Validate division
        if region in RAILWAY_DIVISIONS:
            if division not in RAILWAY_DIVISIONS[region]:
                return {
                    'is_valid': False,
                    'error_message': f"Invalid division: {division} for region {region}"
                }
        
        # Validate track_id
        if not (1 <= track_id <= 999):
            return {
                'is_valid': False,
                'error_message': f"Track ID must be between 1 and 999, got {track_id}"
            }
        
        # Validate km_marker
        if not (0 <= km_marker <= 999999):
            return {
                'is_valid': False,
                'error_message': f"KM marker must be between 0 and 999999, got {km_marker}"
            }
        
        # Validate component_type
        if component_type not in COMPONENT_TYPES:
            return {
                'is_valid': False,
                'error_message': f"Invalid component type: {component_type}. Must be one of {list(COMPONENT_TYPES.keys())}"
            }
        
        # Validate year
        current_year = datetime.now().year
        if not (2020 <= year <= current_year + 5):
            return {
                'is_valid': False,
                'error_message': f"Year must be between 2020 and {current_year + 5}, got {year}"
            }
        
        # Validate serial_number
        if not (1 <= serial_number <= 999999):
            return {
                'is_valid': False,
                'error_message': f"Serial number must be between 1 and 999999, got {serial_number}"
            }
        
        return {'is_valid': True, 'error_message': None}
    
    def validate_batch_data(self, components_list):
        """
        Validate a list of component data
        
        Parameters:
        - components_list: list of dicts with component data
        
        Returns:
        - valid_components: list of valid components
        - invalid_components: list of invalid components with errors
        """
        
        valid_components = []
        invalid_components = []
        
        for i, component in enumerate(components_list):
            try:
                # Check required fields
                required_fields = ['region', 'division', 'track_id', 'km_marker', 
                                 'component_type', 'year', 'serial_number']
                
                missing_fields = [field for field in required_fields if field not in component]
                if missing_fields:
                    invalid_components.append({
                        'index': i,
                        'component': component,
                        'error': f"Missing required fields: {missing_fields}"
                    })
                    continue
                
                # Validate components
                validation_result = self.validate_components(
                    component['region'], component['division'], component['track_id'],
                    component['km_marker'], component['component_type'], 
                    component['year'], component['serial_number']
                )
                
                if validation_result['is_valid']:
                    valid_components.append(component)
                else:
                    invalid_components.append({
                        'index': i,
                        'component': component,
                        'error': validation_result['error_message']
                    })
                    
            except Exception as e:
                invalid_components.append({
                    'index': i,
                    'component': component,
                    'error': f"Validation error: {str(e)}"
                })
        
        return valid_components, invalid_components
    
    def check_duplicate_serial_numbers(self, components_list):
        """
        Check for duplicate serial numbers within the same category
        
        Parameters:
        - components_list: list of component dicts
        
        Returns:
        - duplicates: list of duplicate entries
        """
        
        # Group by category (region, division, component_type, year)
        categories = {}
        duplicates = []
        
        for i, component in enumerate(components_list):
            category_key = (
                component['region'], 
                component['division'], 
                component['component_type'], 
                component['year']
            )
            
            if category_key not in categories:
                categories[category_key] = []
            
            categories[category_key].append({
                'index': i,
                'component': component,
                'serial_number': component['serial_number']
            })
        
        # Find duplicates within each category
        for category, items in categories.items():
            serial_numbers = [item['serial_number'] for item in items]
            seen_serials = set()
            
            for item in items:
                if item['serial_number'] in seen_serials:
                    duplicates.append({
                        'category': category,
                        'duplicate_item': item,
                        'message': f"Duplicate serial number {item['serial_number']} in category {category}"
                    })
                else:
                    seen_serials.add(item['serial_number'])
        
        return duplicates


def validate_qr_format(qr_data):
    """Standalone function for QR format validation"""
    validator = RailwayDataValidator()
    return validator.validate_qr_format(qr_data)


if __name__ == "__main__":
    # Test the validator
    validator = RailwayDataValidator()
    
    # Test valid QR data
    test_qr = "IR-WR-BCT-021-114320-BOLT-2024-001234"
    is_valid, parsed_data, error = validator.validate_qr_format(test_qr)
    
    print(f"Testing QR: {test_qr}")
    print(f"Valid: {is_valid}")
    if is_valid:
        print(f"Parsed data: {parsed_data}")
    else:
        print(f"Error: {error}")
    
    # Test invalid QR data
    invalid_qr = "INVALID-FORMAT"
    is_valid, parsed_data, error = validator.validate_qr_format(invalid_qr)
    
    print(f"\nTesting invalid QR: {invalid_qr}")
    print(f"Valid: {is_valid}")
    if not is_valid:
        print(f"Error: {error}")
