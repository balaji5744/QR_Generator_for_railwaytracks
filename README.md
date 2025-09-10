# Railway QR Code Generation System

## Smart India Hackathon 2025 Project
**AI-based development of Laser-based QR Code marking on track fittings on Indian Railways**

## Overview

This system generates unique QR codes for railway track components (bolts, clips, plates, sleepers) with the following format:

```
IR-[REGION]-[DIVISION]-[TRACK_ID]-[KM_MARKER]-[COMPONENT_TYPE]-[YEAR]-[SERIAL_NUMBER]

Example: IR-WR-BCT-021-114320-BOLT-2024-001234
```

## Features

### ✅ Core Features (Implemented)
- **QR Code Generation**: Generate QR codes with railway-specific data format
- **Data Validation**: Validate QR data format and component specifications
- **Database Management**: SQLite database for component tracking and serial number management
- **Batch Processing**: Generate multiple QR codes from CSV files
- **Quality Verification**: AI-based quality checking using computer vision
- **CLI Interface**: Command-line interface for easy operation
- **Export & Reports**: CSV reports and ZIP archives

### 🎯 AI-Powered Features
- **Quality Verification**: Analyze generated QR codes for readability
- **Optimal Size Calculator**: Suggest QR size based on component dimensions
- **Batch Validation**: Check if generated QR codes are scannable

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd railway_qr_system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the demo**
```bash
python main.py demo
```

## Usage

### Command Line Interface

#### Generate Single QR Code
```bash
python main.py generate --region WR --division BCT --track 21 --km 114320 --type BOLT --year 2024
```

#### Generate Batch from CSV
```bash
python main.py batch --input components.csv --output ./qr_codes/ --auto-serial --quality-check
```

#### Verify QR Quality
```bash
python main.py verify --path ./qr_codes/IR-WR-BCT-021-114320-BOLT-2024-001234.png --detailed
```

#### Generate Reports
```bash
python main.py report --format csv --output railway_components.csv
```

#### Show Statistics
```bash
python main.py stats
```

### CSV Input Format

Create a CSV file with the following columns:

```csv
region,division,track_id,km_marker,component_type,year,serial_number,material,size,manufacturer
WR,BCT,21,114320,BOLT,2024,1001,Steel,M20,Railway Component Co.
CR,CSMT,105,89450,CLIP,2024,2001,Steel,Standard,Track Solutions Ltd.
NR,DLI,67,234100,PLATE,2024,3001,Steel,Heavy Duty,Northern Rails Inc.
```

## Project Structure

```
railway_qr_system/
├── src/
│   ├── qr_generator.py          # Core QR generation logic
│   ├── data_validator.py        # Validate QR data format
│   ├── database_manager.py      # Database operations
│   ├── quality_checker.py       # AI-based quality verification
│   └── batch_processor.py       # Bulk operations
├── models/
│   └── database.db             # SQLite database
├── output/
│   ├── qr_codes/               # Generated QR images
│   └── reports/                # CSV/PDF reports
├── tests/
│   └── test_qr_generator.py    # Unit tests
├── requirements.txt            # Python dependencies
├── config.py                   # Configuration settings
└── main.py                     # CLI interface
```

## QR Code Specifications

- **Error Correction Level**: H (High - 30% damage tolerance for outdoor use)
- **Size**: Configurable (5mm to 15mm for different components)
- **Format**: PNG with transparent background for laser marking
- **Encoding**: UTF-8
- **Version**: Auto-select based on data length (likely Version 3-5)

## Component Types Supported

- **BOLT**: Track Bolt
- **CLIP**: Rail Clip
- **PLATE**: Fish Plate
- **SLEEPER**: Railway Sleeper
- **FISH**: Fish Plate
- **ANCHOR**: Rail Anchor
- **SPIKE**: Rail Spike
- **WASHER**: Rail Washer

## Railway Regions & Divisions

### Regions
- **WR**: Western Railway
- **CR**: Central Railway
- **NR**: Northern Railway
- **ER**: Eastern Railway
- **SR**: Southern Railway
- And more...

### Sample Divisions
- **WR**: BCT, VAPI, RTM, BRC, ADI, PUNE, KOP
- **CR**: CSMT, LTT, KALYAN, PUNE, NAGPUR, BPL
- **NR**: DLI, AMB, FZR, LDH, UMB, JRC

## Quality Verification

The system performs AI-based quality checks on generated QR codes:

1. **Size Check**: Ensures adequate size for laser marking
2. **Contrast Check**: Verifies black/white contrast
3. **Sharpness Check**: Analyzes image sharpness
4. **Alignment Check**: Validates QR alignment markers
5. **Readability Check**: Tests actual QR code scanning

## Database Schema

### Components Table
- `qr_data`: Unique QR code data
- `region`, `division`, `track_id`, `km_marker`: Location data
- `component_type`, `year`, `serial_number`: Component identification
- `material`, `size`, `manufacturer`: Component specifications
- `status`: Component status (ACTIVE, REPLACED, etc.)

### Serial Tracking Table
- Tracks last used serial numbers to prevent duplicates
- Organized by region, division, component type, and year

## Demo Scenario

For Smart India Hackathon presentation:

1. **Live Generation**: Generate QR codes for sample railway components
2. **Database Tracking**: Show database filling with component data
3. **Quality Verification**: Display AI quality checking in action
4. **Batch Export**: Export QR codes ready for "laser marking"

## Technical Specifications

- **Python 3.8+**
- **SQLite Database**
- **OpenCV for Computer Vision**
- **PIL/Pillow for Image Processing**
- **Click for CLI Interface**
- **Pandas for Data Handling**

## Scalability

The system is designed to handle:
- **Single QR codes** for individual components
- **Batch processing** of thousands of components
- **Millions of components** across Indian Railways network (68,000+ km)

## Future Enhancements

- Web interface for non-technical users
- Integration with laser marking software APIs
- Advanced analytics and reporting
- GPS coordinate integration
- Mobile app for field verification

## License

This project is developed for Smart India Hackathon 2025.

## Contact

For questions about this project, please contact the development team.
