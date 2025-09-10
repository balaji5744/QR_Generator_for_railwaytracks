"""
Batch Processing Module for Railway QR Code System
Handles bulk QR code generation and processing
"""

import os
import csv
import zipfile
import uuid
from datetime import datetime
from typing import List, Dict, Tuple
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qr_generator import RailwayQRGenerator
from data_validator import RailwayDataValidator
from database_manager import RailwayDatabaseManager
from config import OUTPUT_DIR


class RailwayBatchProcessor:
    """Handles batch processing of railway QR codes"""
    
    def __init__(self):
        self.qr_generator = RailwayQRGenerator()
        self.validator = RailwayDataValidator()
        self.db_manager = RailwayDatabaseManager()
    
    def generate_batch_qr(self, components_list: List[Dict], 
                         output_directory: str = None) -> Dict:
        """
        Generate multiple QR codes at once
        
        Parameters:
        - components_list: list of component dictionaries
        - output_directory: str (where to save QR images)
        
        Returns:
        - result: dict with success_count, failed_components, report_file
        """
        
        if output_directory is None:
            output_directory = f"{OUTPUT_DIR}/qr_codes"
        
        # Ensure output directory exists
        os.makedirs(output_directory, exist_ok=True)
        
        # Generate batch ID for tracking
        batch_id = str(uuid.uuid4())[:8]
        
        # Validate all components first
        valid_components, invalid_components = self.validator.validate_batch_data(components_list)
        
        # Check for duplicate serial numbers
        duplicates = self.validator.check_duplicate_serial_numbers(valid_components)
        
        if duplicates:
            print(f"Warning: Found {len(duplicates)} duplicate serial numbers")
            for dup in duplicates:
                print(f"  - {dup['message']}")
        
        # Process valid components
        successful_generations = []
        failed_generations = []
        
        for i, component in enumerate(valid_components):
            try:
                # Generate QR code
                qr_image, qr_data, filename = self.qr_generator.generate_railway_qr(
                    component['region'],
                    component['division'],
                    component['track_id'],
                    component['km_marker'],
                    component['component_type'],
                    component['year'],
                    component['serial_number']
                )
                
                # Save QR code
                filepath = self.qr_generator.save_qr_code(qr_image, filename, output_directory)
                
                # Save to database
                component_specs = {
                    'material': component.get('material'),
                    'size': component.get('size'),
                    'manufacturer': component.get('manufacturer'),
                    'status': component.get('status', 'ACTIVE')
                }
                
                db_success = self.db_manager.save_component_data(qr_data, component_specs)
                
                # Log generation
                self.db_manager.log_generation(
                    qr_data, 'batch', batch_id, filepath
                )
                
                successful_generations.append({
                    'index': i,
                    'component': component,
                    'qr_data': qr_data,
                    'filepath': filepath,
                    'db_saved': db_success
                })
                
            except Exception as e:
                failed_generations.append({
                    'index': i,
                    'component': component,
                    'error': str(e)
                })
        
        # Generate report
        report_file = self._generate_batch_report(
            batch_id, successful_generations, failed_generations, 
            invalid_components, duplicates, output_directory
        )
        
        return {
            'batch_id': batch_id,
            'success_count': len(successful_generations),
            'failed_count': len(failed_generations) + len(invalid_components),
            'successful_generations': successful_generations,
            'failed_generations': failed_generations,
            'invalid_components': invalid_components,
            'duplicates': duplicates,
            'report_file': report_file
        }
    
    def _generate_batch_report(self, batch_id: str, successful_generations: List[Dict],
                              failed_generations: List[Dict], invalid_components: List[Dict],
                              duplicates: List[Dict], output_directory: str) -> str:
        """Generate detailed batch report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"batch_report_{batch_id}_{timestamp}.csv"
        report_path = os.path.join(f"{OUTPUT_DIR}/reports", report_filename)
        
        # Ensure reports directory exists
        os.makedirs(f"{OUTPUT_DIR}/reports", exist_ok=True)
        
        # Prepare report data
        report_data = []
        
        # Add successful generations
        for item in successful_generations:
            report_data.append({
                'Status': 'SUCCESS',
                'QR_Data': item['qr_data'],
                'File_Path': item['filepath'],
                'Region': item['component']['region'],
                'Division': item['component']['division'],
                'Track_ID': item['component']['track_id'],
                'KM_Marker': item['component']['km_marker'],
                'Component_Type': item['component']['component_type'],
                'Year': item['component']['year'],
                'Serial_Number': item['component']['serial_number'],
                'Material': item['component'].get('material', ''),
                'Size': item['component'].get('size', ''),
                'Manufacturer': item['component'].get('manufacturer', ''),
                'DB_Saved': item['db_saved'],
                'Error': ''
            })
        
        # Add failed generations
        for item in failed_generations:
            report_data.append({
                'Status': 'FAILED',
                'QR_Data': '',
                'File_Path': '',
                'Region': item['component'].get('region', ''),
                'Division': item['component'].get('division', ''),
                'Track_ID': item['component'].get('track_id', ''),
                'KM_Marker': item['component'].get('km_marker', ''),
                'Component_Type': item['component'].get('component_type', ''),
                'Year': item['component'].get('year', ''),
                'Serial_Number': item['component'].get('serial_number', ''),
                'Material': item['component'].get('material', ''),
                'Size': item['component'].get('size', ''),
                'Manufacturer': item['component'].get('manufacturer', ''),
                'DB_Saved': False,
                'Error': item['error']
            })
        
        # Add invalid components
        for item in invalid_components:
            report_data.append({
                'Status': 'INVALID',
                'QR_Data': '',
                'File_Path': '',
                'Region': item['component'].get('region', ''),
                'Division': item['component'].get('division', ''),
                'Track_ID': item['component'].get('track_id', ''),
                'KM_Marker': item['component'].get('km_marker', ''),
                'Component_Type': item['component'].get('component_type', ''),
                'Year': item['component'].get('year', ''),
                'Serial_Number': item['component'].get('serial_number', ''),
                'Material': item['component'].get('material', ''),
                'Size': item['component'].get('size', ''),
                'Manufacturer': item['component'].get('manufacturer', ''),
                'DB_Saved': False,
                'Error': item['error']
            })
        
        # Write CSV report
        df = pd.DataFrame(report_data)
        df.to_csv(report_path, index=False)
        
        return report_path
    
    def create_zip_archive(self, qr_files: List[str], output_path: str) -> bool:
        """
        Create ZIP archive of QR code files
        
        Parameters:
        - qr_files: list of QR code file paths
        - output_path: str (output ZIP file path)
        
        Returns:
        - success: bool
        """
        
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in qr_files:
                    if os.path.exists(file_path):
                        # Add file to zip with just the filename
                        zipf.write(file_path, os.path.basename(file_path))
            
            return True
            
        except Exception as e:
            print(f"Error creating ZIP archive: {e}")
            return False
    
    def load_components_from_csv(self, csv_file: str) -> List[Dict]:
        """
        Load component data from CSV file
        
        Parameters:
        - csv_file: str (path to CSV file)
        
        Returns:
        - components: list of component dicts
        """
        
        try:
            df = pd.read_csv(csv_file)
            components = df.to_dict('records')
            
            # Convert numeric columns
            for component in components:
                if 'track_id' in component:
                    component['track_id'] = int(component['track_id'])
                if 'km_marker' in component:
                    component['km_marker'] = int(component['km_marker'])
                if 'year' in component:
                    component['year'] = int(component['year'])
                if 'serial_number' in component:
                    component['serial_number'] = int(component['serial_number'])
            
            return components
            
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            return []
    
    def generate_auto_serial_batch(self, base_components: List[Dict]) -> List[Dict]:
        """
        Generate batch with automatic serial numbers
        
        Parameters:
        - base_components: list of component dicts (without serial numbers)
        
        Returns:
        - components: list with auto-assigned serial numbers
        """
        
        components = []
        
        for base_component in base_components:
            # Get next serial number
            next_serial = self.db_manager.get_next_serial_number(
                base_component['region'],
                base_component['division'],
                base_component['component_type'],
                base_component['year']
            )
            
            # Create component with serial number
            component = base_component.copy()
            component['serial_number'] = next_serial
            components.append(component)
        
        return components
    
    def create_printable_sheet(self, qr_files: List[str], output_path: str, 
                              rows: int = 5, cols: int = 4) -> bool:
        """
        Create printable sheet with multiple QR codes
        
        Parameters:
        - qr_files: list of QR code file paths
        - output_path: str (output image path)
        - rows: int (number of rows)
        - cols: int (number of columns)
        
        Returns:
        - success: bool
        """
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Calculate sheet dimensions
            qr_size = 200  # Size of each QR code in pixels
            margin = 50
            spacing = 20
            
            sheet_width = cols * qr_size + (cols - 1) * spacing + 2 * margin
            sheet_height = rows * qr_size + (rows - 1) * spacing + 2 * margin
            
            # Create sheet
            sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
            draw = ImageDraw.Draw(sheet)
            
            # Try to load a font
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            # Place QR codes on sheet
            for i, qr_file in enumerate(qr_files[:rows * cols]):
                if not os.path.exists(qr_file):
                    continue
                
                # Calculate position
                row = i // cols
                col = i % cols
                
                x = margin + col * (qr_size + spacing)
                y = margin + row * (qr_size + spacing)
                
                # Load and resize QR code
                qr_img = Image.open(qr_file)
                qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
                
                # Paste QR code
                sheet.paste(qr_img, (x, y))
                
                # Add filename below QR code
                filename = os.path.basename(qr_file).replace('.png', '')
                text_bbox = draw.textbbox((0, 0), filename, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = x + (qr_size - text_width) // 2
                text_y = y + qr_size + 5
                
                draw.text((text_x, text_y), filename, fill='black', font=font)
            
            # Save sheet
            sheet.save(output_path, 'PNG', dpi=(300, 300))
            
            return True
            
        except Exception as e:
            print(f"Error creating printable sheet: {e}")
            return False


if __name__ == "__main__":
    # Test the batch processor
    processor = RailwayBatchProcessor()
    
    # Create test components
    test_components = [
        {
            'region': 'WR',
            'division': 'BCT',
            'track_id': 21,
            'km_marker': 114320,
            'component_type': 'BOLT',
            'year': 2024,
            'serial_number': 1001,
            'material': 'Steel',
            'size': 'M20'
        },
        {
            'region': 'CR',
            'division': 'CSMT',
            'track_id': 105,
            'km_marker': 89450,
            'component_type': 'CLIP',
            'year': 2024,
            'serial_number': 2001,
            'material': 'Steel',
            'size': 'Standard'
        }
    ]
    
    # Test batch generation
    result = processor.generate_batch_qr(test_components)
    
    print(f"Batch ID: {result['batch_id']}")
    print(f"Success: {result['success_count']}")
    print(f"Failed: {result['failed_count']}")
    print(f"Report: {result['report_file']}")
