"""
Batch Processing Module for Railway QR Code System
Handles bulk QR code generation and processing
"""

import os
import uuid
from datetime import datetime
from typing import List, Dict
import pandas as pd

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.qr_generator import RailwayQRGenerator
from src.database_manager import RailwayDatabaseManager
from config import OUTPUT_DIR


class RailwayBatchProcessor:
    """Handles batch processing of railway QR codes"""

    def __init__(self):
        self.qr_generator = RailwayQRGenerator()
        self.db_manager = RailwayDatabaseManager()

    def generate_batch_qr(self, components_list: List[Dict],
                         output_directory: str = None) -> Dict:
        if output_directory is None:
            output_directory = f"{OUTPUT_DIR}/qr_codes"
        os.makedirs(output_directory, exist_ok=True)

        batch_id = str(uuid.uuid4())[:8]
        successful_generations = []
        failed_generations = []

        # --- PRE-PROCESSING VALIDATION ---
        if not components_list:
            # Handle empty CSV case
            report_file = self._generate_batch_report(batch_id, [], [])
            return {
                'batch_id': batch_id, 'success_count': 0, 'failed_count': 0,
                'report_file': report_file, 'successful_generations': [], 'failed_generations': []
            }

        required_columns = ['region', 'division', 'track_id', 'km_marker', 'component_type', 'installation_date']
        first_item_keys = components_list[0].keys()
        missing_cols = [col for col in required_columns if col not in first_item_keys]
        if missing_cols:
            error_message = f"CSV file is missing required columns: {', '.join(missing_cols)}"
            for component in components_list:
                failed_generations.append({'component': component, 'error': error_message})
            report_file = self._generate_batch_report(batch_id, [], failed_generations)
            return {
                'batch_id': batch_id, 'success_count': 0, 'failed_count': len(components_list),
                'report_file': report_file, 'successful_generations': [], 'failed_generations': failed_generations
            }

        # --- ROW-BY-ROW PROCESSING ---
        for i, component in enumerate(components_list):
            try:
                # --- DATA VALIDATION AND TYPE CONVERSION ---
                track_id = int(component['track_id'])
                km_marker = int(component['km_marker'])
                serial_number = int(component['serial_number'])
                
                installation_date_str = str(component['installation_date'])
                try:
                    installation_date_obj = datetime.strptime(installation_date_str, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(f"Invalid date format for '{installation_date_str}'. Expected YYYY-MM-DD.")

                # --- QR GENERATION ---
                qr_image, qr_data, filename = self.qr_generator.generate_railway_qr(
                    component['region'], component['division'], track_id, km_marker,
                    component['component_type'], installation_date_obj, serial_number
                )
                filepath = self.qr_generator.save_qr_code(qr_image, filename, output_directory)

                # --- DATABASE INTERACTION ---
                component_specs = {
                    'material': component.get('material'), 'size': component.get('size'),
                    'manufacturer': component.get('manufacturer'), 'status': 'ACTIVE'
                }
                db_success = self.db_manager.save_component_data(qr_data, component_specs, installation_date_str)
                self.db_manager.log_generation(qr_data, 'batch', batch_id, filepath)

                successful_generations.append({
                    'component': component, 'qr_data': qr_data,
                    'filepath': filepath, 'db_saved': db_success
                })
            except KeyError as e:
                failed_generations.append({'component': component, 'error': f"Missing column in CSV: {e}"})
            except ValueError as e:
                failed_generations.append({'component': component, 'error': f"Invalid data type or format: {e}"})
            except Exception as e:
                failed_generations.append({'component': component, 'error': f"An unexpected error occurred: {e}"})
        
        report_file = self._generate_batch_report(batch_id, successful_generations, failed_generations)
        
        return {
            'batch_id': batch_id, 'success_count': len(successful_generations),
            'failed_count': len(failed_generations), 'successful_generations': successful_generations,
            'failed_generations': failed_generations, 'report_file': report_file
        }

    def _generate_batch_report(self, batch_id: str, successful: List[Dict], failed: List[Dict]) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"batch_report_{batch_id}_{timestamp}.csv"
        report_path = os.path.join(f"{OUTPUT_DIR}/reports", report_filename)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        report_data = []
        for item in successful:
            row = {'Status': 'SUCCESS', 'QR_Data': item['qr_data'], 'File_Path': item['filepath'], 'Error': ''}
            row.update(item['component'])
            report_data.append(row)
        for item in failed:
            row = {'Status': 'FAILED', 'QR_Data': '', 'File_Path': '', 'Error': item['error']}
            row.update(item['component'])
            report_data.append(row)
        if report_data:
            df = pd.DataFrame(report_data)
            df.to_csv(report_path, index=False)
        return report_path

    def load_components_from_csv(self, csv_file: str) -> List[Dict]:
        try:
            df = pd.read_csv(csv_file, dtype=str).fillna('')
            df.columns = df.columns.str.strip()
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading CSV file: {e}")
            return []

    def generate_auto_serial_batch(self, base_components: List[Dict]) -> List[Dict]:
        components_with_serials = []
        for component in base_components:
            new_component = component.copy()
            if 'installation_date' not in new_component:
                 # If date is missing, we can't generate a serial, so we'll let it fail later with a clear message
                new_component['serial_number'] = 'ERROR_DATE_MISSING'
                components_with_serials.append(new_component)
                continue

            tracking_date = str(new_component['installation_date'])
            next_serial = self.db_manager.get_next_serial_number(
                new_component['region'], new_component['division'],
                new_component['component_type'], tracking_date
            )
            new_component['serial_number'] = next_serial
            components_with_serials.append(new_component)
        return components_with_serials
    
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
