# ==============================================================================
# A CLEANED AND CORRECTED VERSION OF YOUR APP.PY
# ==============================================================================

import os
import sys
import shutil
from datetime import datetime
import numpy as np
import cv2

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, send_from_directory, abort, Response)
from werkzeug.utils import secure_filename

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import your project modules
from qr_generator import RailwayQRGenerator
from database_manager import RailwayDatabaseManager
from batch_processor import RailwayBatchProcessor
from quality_checker import RailwayQRQualityChecker
from config import RAILWAY_REGIONS, COMPONENT_TYPES
from data_validator import RailwayDataValidator
from damage_detector import DamageDetector

# --- App Setup ---
app = Flask(__name__)
# It's better to use a real random key, but this is fine for the hackathon
app.secret_key = os.environ.get('SECRET_KEY', 'your_super_secret_key_for_sih2025')
detector = DamageDetector()  # Initialize the detector

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

# --- Routes ---

@app.route('/')
def index():
    """Renders the home page with database statistics."""
    db_manager = get_db_manager()
    stats = db_manager.get_statistics()
    return render_template('index.html', stats=stats)


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """Handles single QR code generation."""
    if request.method == 'POST':
        try:
            db_manager = get_db_manager()
            generator = get_qr_generator()

            region = request.form['region']
            division = request.form['division']
            component_type = request.form['component_type']
            track_id = int(request.form['track_id'])
            km_marker = int(request.form['km_marker'])
            
            installation_date_str = request.form['installation_date']
            installation_date_obj = datetime.strptime(installation_date_str, '%Y-%m-%d').date()
            tracking_date = installation_date_str

            serial_number = db_manager.get_next_serial_number(region, division, component_type, tracking_date)
            
            filepath, qr_data = generator.generate_and_save(
                region=region, division=division, track_id=track_id, km_marker=km_marker,
                component_type=component_type, installation_date=installation_date_obj,
                serial_number=serial_number
            )
            
            component_specs = {
                'material': request.form['material'], 'size': request.form['size'],
                'manufacturer': request.form['manufacturer'], 'status': 'ACTIVE'
            }
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
            flash('No CSV file selected', 'danger')
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

            quality_report_path = None
            if request.form.get('quality_check') and result['successful_generations']:
                quality_checker = get_quality_checker()
                qr_files = [item['filepath'] for item in result['successful_generations']]
                quality_results = quality_checker.batch_quality_check(qr_files)
                quality_report_name = os.path.basename(result['report_file']).replace('.csv', '_quality.csv')
                quality_report_path = os.path.join(app.config['REPORTS_FOLDER'], quality_report_name)
                quality_checker.generate_quality_report(quality_results, quality_report_path)
                flash(f"Quality check complete. Average score: {quality_results['average_quality_score']}", 'info')
            
            return render_template('batch.html',
                                   report_file=os.path.basename(result['report_file']),
                                   quality_report_file=os.path.basename(quality_report_path) if quality_report_path else None)
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
            
            image = cv2.imread(filepath)
            qr_detector = cv2.QRCodeDetector()
            data, _, _ = qr_detector.detectAndDecode(image)
            
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


@app.route('/report', methods=['GET', 'POST'])
def report():
    """Displays database statistics and allows report generation."""
    db_manager = get_db_manager()
    
    if request.method == 'POST':
        try:
            filters = {
                'region': request.form.get('region'),
                'component_type': request.form.get('component_type'),
                'year': request.form.get('year')
            }
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


# --- Live Detection Routes ---
def generate_frames():
    """Generator function to process video and yield frames from the webcam."""
    # --- THIS IS THE ONLY CHANGE ---
    # Use 0 for the default webcam instead of a file path
    cap = cv2.VideoCapture(0)
    print("✅ Trying to open webcam...")

    if not cap.isOpened():
        print("❌ Error: Could not open webcam.")

    while True:
        if cap and cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("⚠️ Warning: Could not read frame from webcam.")
                continue # Skip this frame
        else:
            # This part will run if the webcam couldn't be opened
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "Webcam Not Found", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        processed_frame = detector.process_frame(frame)
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/live_feed')
def live_feed():
    return render_template('live_feed.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# --- File Serving Routes ---
@app.route('/output/qr_codes/<path:filename>')
def serve_qr_code(filename):
    return send_from_directory(app.config['QR_CODES_FOLDER'], filename)
    
@app.route('/output/reports/<path:filename>')
def serve_report(filename):
    return send_from_directory(app.config['REPORTS_FOLDER'], filename, as_attachment=True)
    
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)