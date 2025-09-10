"""
Core QR Code Generation Module for Railway Track Fittings
Generates QR codes with railway-specific data format
"""

import qrcode
from PIL import Image
import os
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    QR_ERROR_CORRECTION, QR_BORDER, QR_BOX_SIZE, 
    QR_FILL_COLOR, QR_BACK_COLOR, QR_SIZES, OUTPUT_DIR
)


class RailwayQRGenerator:
    """Main class for generating railway component QR codes"""
    
    def __init__(self):
        self.ensure_output_dirs()
    
    def ensure_output_dirs(self):
        """Ensure output directories exist"""
        os.makedirs(f"{OUTPUT_DIR}/qr_codes", exist_ok=True)
        os.makedirs(f"{OUTPUT_DIR}/reports", exist_ok=True)
    
    def generate_railway_qr(self, region, division, track_id, km_marker, 
                           component_type, year, serial_number=None):
        """
        Generate QR code for railway component
        
        Parameters:
        - region: str (e.g., 'WR', 'CR', 'NR')
        - division: str (e.g., 'BCT', 'CSMT', 'DLI') 
        - track_id: int (1-999)
        - km_marker: int (kilometer + offset as 6 digits, e.g., 114320)
        - component_type: str ('BOLT', 'CLIP', 'PLATE', 'SLEEPER')
        - year: int (2024, 2025, etc.)
        - serial_number: int (auto-generate if None)
        
        Returns:
        - qr_image: PIL Image object
        - qr_data: str (the encoded data)
        - filename: str (suggested filename)
        """
        
        # Validate inputs
        if not self._validate_inputs(region, division, track_id, km_marker, 
                                   component_type, year, serial_number):
            raise ValueError("Invalid input parameters")
        
        # Format track_id and km_marker
        track_id_str = f"{track_id:03d}"
        km_marker_str = f"{km_marker:06d}"
        year_str = str(year)
        serial_str = f"{serial_number:06d}" if serial_number else "000000"
        
        # Create QR data string
        qr_data = f"IR-{region}-{division}-{track_id_str}-{km_marker_str}-{component_type}-{year_str}-{serial_str}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{QR_ERROR_CORRECTION}'),
            box_size=QR_BOX_SIZE,
            border=QR_BORDER,
        )
        
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR image
        qr_image = qr.make_image(fill_color=QR_FILL_COLOR, back_color=QR_BACK_COLOR)
        
        # Resize based on component type
        qr_image = self._resize_for_component(qr_image, component_type)
        
        # Generate filename
        filename = f"{qr_data}.png"
        
        return qr_image, qr_data, filename
    
    def _validate_inputs(self, region, division, track_id, km_marker, 
                        component_type, year, serial_number):
        """Validate input parameters"""
        
        # Check region
        if not isinstance(region, str) or len(region) != 2:
            return False
            
        # Check division
        if not isinstance(division, str) or len(division) < 2:
            return False
            
        # Check track_id
        if not isinstance(track_id, int) or track_id < 1 or track_id > 999:
            return False
            
        # Check km_marker
        if not isinstance(km_marker, int) or km_marker < 0 or km_marker > 999999:
            return False
            
        # Check component_type
        if component_type not in ['BOLT', 'CLIP', 'PLATE', 'SLEEPER', 'FISH', 'ANCHOR', 'SPIKE', 'WASHER']:
            return False
            
        # Check year
        current_year = datetime.now().year
        if not isinstance(year, int) or year < 2020 or year > current_year + 5:
            return False
            
        # Check serial_number if provided
        if serial_number is not None:
            if not isinstance(serial_number, int) or serial_number < 1 or serial_number > 999999:
                return False
                
        return True
    
    def _resize_for_component(self, qr_image, component_type):
        """Resize QR code based on component type"""
        
        # Get base size from config
        target_size_mm = QR_SIZES.get(component_type, 10)
        
        # Convert mm to pixels (assuming 300 DPI for laser marking)
        dpi = 300
        target_size_pixels = int((target_size_mm / 25.4) * dpi)
        
        # Resize image
        qr_image = qr_image.resize((target_size_pixels, target_size_pixels), Image.Resampling.LANCZOS)
        
        return qr_image
    
    def save_qr_code(self, qr_image, filename, output_dir=None):
        """Save QR code image to file"""
        
        if output_dir is None:
            output_dir = f"{OUTPUT_DIR}/qr_codes"
            
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        qr_image.save(filepath, 'PNG', dpi=(300, 300))
        
        return filepath
    
    def generate_and_save(self, region, division, track_id, km_marker, 
                         component_type, year, serial_number=None, output_dir=None):
        """
        Generate QR code and save to file in one operation
        
        Returns:
        - filepath: str (path to saved file)
        - qr_data: str (the encoded data)
        """
        
        qr_image, qr_data, filename = self.generate_railway_qr(
            region, division, track_id, km_marker, component_type, year, serial_number
        )
        
        filepath = self.save_qr_code(qr_image, filename, output_dir)
        
        return filepath, qr_data


def generate_railway_qr(region, division, track_id, km_marker, 
                       component_type, year, serial_number=None):
    """
    Standalone function for generating railway QR codes
    Convenience function that creates a generator instance
    """
    generator = RailwayQRGenerator()
    return generator.generate_railway_qr(
        region, division, track_id, km_marker, component_type, year, serial_number
    )


if __name__ == "__main__":
    # Test the QR generator
    generator = RailwayQRGenerator()
    
    # Generate sample QR codes
    test_cases = [
        ('WR', 'BCT', 21, 114320, 'BOLT', 2024, 1234),
        ('CR', 'CSMT', 105, 89450, 'CLIP', 2024, 5678),
        ('NR', 'DLI', 67, 234100, 'PLATE', 2024, 9012),
    ]
    
    print("Generating test QR codes...")
    for case in test_cases:
        try:
            filepath, qr_data = generator.generate_and_save(*case)
            print(f"✓ Generated: {qr_data}")
            print(f"  Saved to: {filepath}")
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    print("\nTest completed!")
