import os
from datetime import datetime
import sys
import shutil
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, send_from_directory, abort)
from werkzeug.utils import secure_filename
# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import your project modules
from qr_generator import RailwayQRGenerator
from database_manager import RailwayDatabaseManager
from batch_processor import RailwayBatchProcessor
from quality_checker import RailwayQRQualityChecker
from config import RAILWAY_REGIONS, COMPONENT_TYPES



# --- App Setup ---
app = Flask(__name__)
app.secret_key = 'your_super_secret_key_for_sih2025'

# --- Configuration ---
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['QR_CODES_FOLDER'] = os.path.join(app.config['OUTPUT_FOLDER'], 'qr_codes')
app.config['REPORTS_FOLDER'] = os.path.join(app.config['OUTPUT_FOLDER'], 'reports')

# --- Ensure Directories Exist ---
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_CODES_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# --- Helper Functions ---
def get_db_manager():
    return RailwayDatabaseManager()

def get_qr_generator():
    return RailwayQRGenerator()

def get_batch_processor():
    return RailwayBatchProcessor()

def get_quality_checker():
    return RailwayQRQualityChecker()

# --- Routes ---


from src.data_validator import RailwayDataValidator
import cv2

# ... (rest of your app.py code)

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    """Handles scanning and decoding of a QR code image."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Decode the QR code
            image = cv2.imread(filepath)
            detector = cv2.QRCodeDetector()
            data, bbox, straight_qrcode = detector.detectAndDecode(image)
            
            if data:
                validator = RailwayDataValidator()
                is_valid, parsed_data, error_message = validator.validate_qr_format(data)
                
                if is_valid:
                    return render_template('scan.html', decoded_data=parsed_data, uploaded_image=filename)
                else:
                    flash(f'Invalid Railway QR Code format: {error_message}', 'warning')
            else:
                flash('Could not decode QR Code from the image.', 'danger')

        except Exception as e:
            flash(f'An error occurred during scanning: {e}', 'danger')

    return render_template('scan.html')


@app.route('/')
def index():
    """Renders the home page."""
    return render_template('index.html')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """Handles single QR code generation."""
    if request.method == 'POST':
        try:
            db_manager = get_db_manager()
            generator = get_qr_generator()

            # Get form data
            region = request.form['region']
            division = request.form['division']
            component_type = request.form['component_type']
            track_id = int(request.form['track_id'])
            km_marker = int(request.form['km_marker'])
            
            # Convert installation date string from form to a date object
            installation_date_str = request.form['installation_date']
            installation_date_obj = datetime.strptime(installation_date_str, '%Y-%m-%d').date()

            # Use the string version (YYYY-MM-DD) for tracking serial numbers
            tracking_date = installation_date_str

            # Auto-generate serial number
            serial_number = db_manager.get_next_serial_number(region, division, component_type, tracking_date)
            
            # Call the corrected generate_and_save function
            filepath, qr_data = generator.generate_and_save(
                region=region,
                division=division,
                track_id=track_id,
                km_marker=km_marker,
                component_type=component_type,
                installation_date=installation_date_obj, # Pass the date object here
                serial_number=serial_number
            )
            
            component_specs = {
                'material': request.form['material'],
                'size': request.form['size'],
                'manufacturer': request.form['manufacturer'],
                'status': 'ACTIVE'
            }
            # Make sure to save the string version of the date to the database
            db_manager.save_component_data(qr_data, component_specs, installation_date_str)
            
            flash(f'Successfully generated QR Code: {qr_data}', 'success')
            return render_template('generate.html',
                                   qr_image=os.path.basename(filepath),
                                   qr_data=qr_data,
                                   regions=RAILWAY_REGIONS.keys(),
                                   component_types=COMPONENT_TYPES.keys())
        except Exception as e:
            flash(f'Error generating QR Code: {e}', 'danger')
            
    return render_template('generate.html',
                           regions=RAILWAY_REGIONS.keys(),
                           component_types=COMPONENT_TYPES.keys())

@app.route('/batch', methods=['GET', 'POST'])
def batch():
    """Handles batch processing of QR codes from a CSV file."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '' or not file.filename.endswith('.csv'):
            flash('No selected file or invalid file type (must be .csv)', 'danger')
            return redirect(request.url)
        
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            processor = get_batch_processor()
            components = processor.load_components_from_csv(filepath)
            
            if request.form.get('auto_serial'):
                components = processor.generate_auto_serial_batch(components)

            result = processor.generate_batch_qr(components)
            
            flash(f"Batch process complete! {result['success_count']} successful, {result['failed_count']} failed.", 'info')

            # Optional Quality Check
            quality_report_path = None
            if request.form.get('quality_check') and result['successful_generations']:
                quality_checker = get_quality_checker()
                qr_files = [item['filepath'] for item in result['successful_generations']]
                quality_results = quality_checker.batch_quality_check(qr_files)
                quality_report_path = os.path.basename(result['report_file']).replace('.csv', '_quality.csv')
                quality_checker.generate_quality_report(quality_results, os.path.join(app.config['REPORTS_FOLDER'], quality_report_path))
                flash(f"Quality check complete. Average score: {quality_results['average_quality_score']}", 'info')
            
            return render_template('batch.html',
                                   report_file=os.path.basename(result['report_file']),
                                   quality_report_file=quality_report_path)
        except Exception as e:
            flash(f'An error occurred during batch processing: {e}', 'danger')

    return render_template('batch.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    """Handles AI quality verification of a QR code image."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            quality_checker = get_quality_checker()
            result = quality_checker.verify_qr_quality(filepath)
            suggestions = quality_checker.suggest_improvements(result)
            
            return render_template('verify.html', result=result, suggestions=suggestions, uploaded_image=filename)
        except Exception as e:
            flash(f'An error occurred during verification: {e}', 'danger')

    return render_template('verify.html')

@app.route('/report', methods=['GET', 'POST'])
def report():
    """Displays database statistics and allows report generation."""
    db_manager = get_db_manager()
    
    if request.method == 'POST':
        try:
            filters = {
                'region': request.form.get('region'),
                'division': request.form.get('division'),
                'component_type': request.form.get('component_type'),
                'year': request.form.get('year')
            }
            # Remove empty filters
            filters = {k: v for k, v in filters.items() if v}
            
            output_filename = "filtered_report.csv"
            output_path = os.path.join(app.config['REPORTS_FOLDER'], output_filename)

            if db_manager.export_to_csv(output_path, filters):
                return send_from_directory(app.config['REPORTS_FOLDER'], output_filename, as_attachment=True)
            else:
                flash('No data found for the selected filters.', 'warning')
        except Exception as e:
            flash(f'Error generating report: {e}', 'danger')

    stats = db_manager.get_statistics()
    return render_template('report.html',
                           stats=stats,
                           regions=RAILWAY_REGIONS.keys(),
                           component_types=COMPONENT_TYPES.keys())

# --- File Serving Routes ---
@app.route('/output/qr_codes/<path:filename>')
def serve_qr_code(filename):
    """Serves generated QR code images."""
    return send_from_directory(app.config['QR_CODES_FOLDER'], filename)
    
@app.route('/output/reports/<path:filename>')
def serve_report(filename):
    """Serves generated report files."""
    return send_from_directory(app.config['REPORTS_FOLDER'], filename, as_attachment=True)
    
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Serves uploaded files for display."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)