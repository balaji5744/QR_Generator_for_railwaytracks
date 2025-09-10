"""
Unit Tests for Railway QR Code Generation System
"""

import unittest
import os
import sys
import tempfile
import shutil

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from qr_generator import RailwayQRGenerator
from data_validator import RailwayDataValidator
from database_manager import RailwayDatabaseManager


class TestRailwayQRGenerator(unittest.TestCase):
    """Test cases for QR code generation"""
    
    def setUp(self):
        self.generator = RailwayQRGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_generate_railway_qr_valid(self):
        """Test generating QR code with valid parameters"""
        qr_image, qr_data, filename = self.generator.generate_railway_qr(
            'WR', 'BCT', 21, 114320, 'BOLT', 2024, 1234
        )
        
        self.assertIsNotNone(qr_image)
        self.assertEqual(qr_data, 'IR-WR-BCT-021-114320-BOLT-2024-001234')
        self.assertEqual(filename, 'IR-WR-BCT-021-114320-BOLT-2024-001234.png')
    
    def test_generate_railway_qr_invalid_region(self):
        """Test generating QR code with invalid region"""
        with self.assertRaises(ValueError):
            self.generator.generate_railway_qr(
                'INVALID', 'BCT', 21, 114320, 'BOLT', 2024, 1234
            )
    
    def test_generate_railway_qr_invalid_track_id(self):
        """Test generating QR code with invalid track ID"""
        with self.assertRaises(ValueError):
            self.generator.generate_railway_qr(
                'WR', 'BCT', 1000, 114320, 'BOLT', 2024, 1234
            )
    
    def test_save_qr_code(self):
        """Test saving QR code to file"""
        qr_image, qr_data, filename = self.generator.generate_railway_qr(
            'WR', 'BCT', 21, 114320, 'BOLT', 2024, 1234
        )
        
        filepath = self.generator.save_qr_code(qr_image, filename, self.temp_dir)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertEqual(os.path.basename(filepath), filename)


class TestRailwayDataValidator(unittest.TestCase):
    """Test cases for data validation"""
    
    def setUp(self):
        self.validator = RailwayDataValidator()
    
    def test_validate_qr_format_valid(self):
        """Test validating valid QR format"""
        qr_data = "IR-WR-BCT-021-114320-BOLT-2024-001234"
        is_valid, parsed_data, error = self.validator.validate_qr_format(qr_data)
        
        self.assertTrue(is_valid)
        self.assertIsNotNone(parsed_data)
        self.assertIsNone(error)
        self.assertEqual(parsed_data['region'], 'WR')
        self.assertEqual(parsed_data['division'], 'BCT')
        self.assertEqual(parsed_data['track_id'], 21)
    
    def test_validate_qr_format_invalid(self):
        """Test validating invalid QR format"""
        qr_data = "INVALID-FORMAT"
        is_valid, parsed_data, error = self.validator.validate_qr_format(qr_data)
        
        self.assertFalse(is_valid)
        self.assertIsNone(parsed_data)
        self.assertIsNotNone(error)
    
    def test_validate_components_valid(self):
        """Test validating valid components"""
        result = self.validator.validate_components(
            'WR', 'BCT', 21, 114320, 'BOLT', 2024, 1234
        )
        
        self.assertTrue(result['is_valid'])
        self.assertIsNone(result['error_message'])
    
    def test_validate_components_invalid_region(self):
        """Test validating invalid region"""
        result = self.validator.validate_components(
            'INVALID', 'BCT', 21, 114320, 'BOLT', 2024, 1234
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Invalid region', result['error_message'])


class TestRailwayDatabaseManager(unittest.TestCase):
    """Test cases for database management"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = RailwayDatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_save_component_data(self):
        """Test saving component data to database"""
        qr_data = "IR-WR-BCT-021-114320-BOLT-2024-001234"
        component_specs = {
            'material': 'Steel',
            'size': 'M20',
            'manufacturer': 'Test Co.'
        }
        
        success = self.db_manager.save_component_data(qr_data, component_specs)
        self.assertTrue(success)
    
    def test_get_next_serial_number(self):
        """Test getting next serial number"""
        serial = self.db_manager.get_next_serial_number('WR', 'BCT', 'BOLT', 2024)
        self.assertEqual(serial, 1)
        
        # Get next serial number
        serial2 = self.db_manager.get_next_serial_number('WR', 'BCT', 'BOLT', 2024)
        self.assertEqual(serial2, 2)
    
    def test_search_components(self):
        """Test searching components"""
        # Save a component first
        qr_data = "IR-WR-BCT-021-114320-BOLT-2024-001234"
        component_specs = {'material': 'Steel'}
        self.db_manager.save_component_data(qr_data, component_specs)
        
        # Search for it
        components = self.db_manager.search_components({'region': 'WR'})
        self.assertEqual(len(components), 1)
        self.assertEqual(components[0]['qr_data'], qr_data)


if __name__ == '__main__':
    unittest.main()
