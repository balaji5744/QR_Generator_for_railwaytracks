"""
Configuration settings for Railway QR Code Generation System
"""

# QR Code Settings
QR_ERROR_CORRECTION = 'H'  # High error correction for outdoor use
QR_BORDER = 4
QR_BOX_SIZE = 10
QR_FILL_COLOR = "black"
QR_BACK_COLOR = "white"

# Railway Regions and Divisions
RAILWAY_REGIONS = {
    'WR': 'Western Railway',
    'CR': 'Central Railway', 
    'NR': 'Northern Railway',
    'ER': 'Eastern Railway',
    'NER': 'North Eastern Railway',
    'NFR': 'Northeast Frontier Railway',
    'SR': 'Southern Railway',
    'SCR': 'South Central Railway',
    'SECR': 'South East Central Railway',
    'SWR': 'South Western Railway',
    'WCR': 'West Central Railway',
    'ECR': 'East Central Railway',
    'ECoR': 'East Coast Railway',
    'NCR': 'North Central Railway',
    'NCR': 'North Western Railway'
}

# Common Railway Divisions
RAILWAY_DIVISIONS = {
    'WR': ['BCT', 'VAPI', 'RTM', 'BRC', 'ADI', 'PUNE', 'KOP'],
    'CR': ['CSMT', 'LTT', 'KALYAN', 'PUNE', 'NAGPUR', 'BPL'],
    'NR': ['DLI', 'AMB', 'FZR', 'LDH', 'UMB', 'JRC'],
    'ER': ['HWH', 'ASN', 'DGR', 'MDP', 'SDAH'],
    'SR': ['MAS', 'SA', 'TPJ', 'MDU', 'TEN'],
    'SCR': ['SC', 'GTL', 'BZA', 'GNT', 'TPTY']
}

# Component Types
COMPONENT_TYPES = {
    'BOLT': 'Track Bolt',
    'CLIP': 'Rail Clip', 
    'PLATE': 'Fish Plate',
    'SLEEPER': 'Railway Sleeper',
    'FISH': 'Fish Plate',
    'ANCHOR': 'Rail Anchor',
    'SPIKE': 'Rail Spike',
    'WASHER': 'Rail Washer'
}

# File Paths
OUTPUT_DIR = 'output'
QR_CODES_DIR = 'output/qr_codes'
REPORTS_DIR = 'output/reports'
DATABASE_PATH = 'models/database.db'

# QR Code Size Settings (in mm)
QR_SIZES = {
    'BOLT': 5,      # 5mm for small components
    'CLIP': 8,      # 8mm for medium components  
    'PLATE': 12,    # 12mm for large components
    'SLEEPER': 15,  # 15mm for very large components
    'FISH': 12,
    'ANCHOR': 10,
    'SPIKE': 6,
    'WASHER': 4
}

# Quality Check Settings
QUALITY_THRESHOLD = 80  # Minimum quality score (0-100)
MIN_QR_SIZE = 21        # Minimum QR code size in pixels
