"""
Core QR Code Generation Module for Railway Track Fittings
Generates QR codes with railway-specific data format
"""

import qrcode
from PIL import Image
import os
from datetime import datetime, date
import sys

# Add project root to path to find the config module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    QR_ERROR_CORRECTION, QR_BORDER, QR_BOX_SIZE,
    QR_FILL_COLOR, QR_BACK_COLOR, OUTPUT_DIR, RAILWAY_REGIONS, COMPONENT_TYPES
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
                           component_type, installation_date, serial_number=None):
        """
        Generate QR code for railway component
        """
        # FULLY IMPLEMENTED VALIDATION
        validation_error = self._validate_inputs(
            region, division, track_id, km_marker, component_type, installation_date, serial_number
        )
        if validation_error:
            raise ValueError(validation_error)
        
        # Format the date as YYYYMMDD for the QR code string
        date_str = installation_date.strftime('%Y%m%d')
        track_id_str = f"{track_id:03d}"
        km_marker_str = f"{km_marker:06d}"
        serial_str = f"{serial_number:06d}"

        # Create QR data string with the new date format
        qr_data = f"IR-{region}-{division}-{track_id_str}-{km_marker_str}-{component_type}-{date_str}-{serial_str}"

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{QR_ERROR_CORRECTION}'),
            box_size=15,
            border=QR_BORDER,
        )

        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color=QR_FILL_COLOR, back_color=QR_BACK_COLOR)
        filename = f"{qr_data}.png"
        return qr_image, qr_data, filename

    def _validate_inputs(self, region, division, track_id, km_marker,
                        component_type, installation_date, serial_number):
        """
        Validate input parameters. Returns an error message string or None if valid.
        """
        if not isinstance(region, str) or region not in RAILWAY_REGIONS:
            return f"Invalid region: {region}"
        if not isinstance(division, str) or len(division) < 2:
            return f"Invalid division: {division}"
        if not isinstance(track_id, int) or not (1 <= track_id <= 999):
            return f"Track ID must be between 1 and 999, got {track_id}"
        if not isinstance(km_marker, int) or not (0 <= km_marker <= 999999):
            return f"KM marker must be between 0 and 999999, got {km_marker}"
        if component_type not in COMPONENT_TYPES:
            return f"Invalid component type: {component_type}"
        if not isinstance(installation_date, date):
             return f"Installation date is not a valid date object: {installation_date}"
        if serial_number is not None and (not isinstance(serial_number, int) or not (1 <= serial_number <= 999999)):
            return f"Serial number must be between 1 and 999999, got {serial_number}"
        return None # Return None if all checks pass

    def save_qr_code(self, qr_image, filename, output_dir=None):
        """Save QR code image to file"""
        if output_dir is None:
            output_dir = f"{OUTPUT_DIR}/qr_codes"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        qr_image.save(filepath, 'PNG', dpi=(300, 300))
        return filepath

    def generate_and_save(self, region, division, track_id, km_marker,
                         component_type, installation_date, serial_number=None, output_dir=None):
        """
        Generate QR code and save to file in one operation
        """
        qr_image, qr_data, filename = self.generate_railway_qr(
            region, division, track_id, km_marker, component_type, installation_date, serial_number
        )
        filepath = self.save_qr_code(qr_image, filename, output_dir)
        return filepath, qr_data