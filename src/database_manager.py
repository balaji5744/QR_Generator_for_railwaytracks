"""
Database Manager for Railway QR Code System
Handles SQLite database operations for component tracking
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH


class RailwayDatabaseManager:
    """Manages SQLite database for railway component tracking"""

    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE_PATH
        self.ensure_db_directory()
        self.init_database()

    def ensure_db_directory(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, qr_data TEXT UNIQUE NOT NULL,
                    region TEXT NOT NULL, division TEXT NOT NULL, track_id INTEGER NOT NULL,
                    km_marker INTEGER NOT NULL, component_type TEXT NOT NULL,
                    installation_date DATE NOT NULL, serial_number INTEGER NOT NULL,
                    material TEXT, size TEXT, manufacturer TEXT, warranty_expiry DATE,
                    status TEXT DEFAULT 'ACTIVE', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS serial_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT NOT NULL,
                    division TEXT NOT NULL, component_type TEXT NOT NULL,
                    tracking_date TEXT NOT NULL, last_serial_number INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(region, division, component_type, tracking_date)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, qr_data TEXT NOT NULL,
                    generation_type TEXT NOT NULL, batch_id TEXT, file_path TEXT,
                    quality_score REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def save_component_data(self, qr_data: str, component_specs: Dict, installation_date: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                parts = qr_data.split('-')
                region, division, track_id, km_marker, component_type, date_str, serial_number = parts[1:]
                cursor.execute('''
                    INSERT INTO components (
                        qr_data, region, division, track_id, km_marker, component_type,
                        installation_date, serial_number, material, size, manufacturer, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    qr_data, region, division, int(track_id), int(km_marker),
                    component_type, installation_date, int(serial_number),
                    component_specs.get('material'), component_specs.get('size'),
                    component_specs.get('manufacturer'), component_specs.get('status', 'ACTIVE')
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error saving component data: {e}")
            return False

    def get_next_serial_number(self, region: str, division: str,
                              component_type: str, tracking_date: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT last_serial_number FROM serial_tracking
                WHERE region = ? AND division = ? AND component_type = ? AND tracking_date = ?
            ''', (region, division, component_type, tracking_date))
            result = cursor.fetchone()
            if result:
                next_serial = result[0] + 1
                cursor.execute('''
                    UPDATE serial_tracking SET last_serial_number = ?
                    WHERE region = ? AND division = ? AND component_type = ? AND tracking_date = ?
                ''', (next_serial, region, division, component_type, tracking_date))
            else:
                next_serial = 1
                cursor.execute('''
                    INSERT INTO serial_tracking (region, division, component_type, tracking_date, last_serial_number)
                    VALUES (?, ?, ?, ?, ?)
                ''', (region, division, component_type, tracking_date, next_serial))
            conn.commit()
            return next_serial
        
    def search_components(self, filters: Dict) -> List[Dict]:
        """
        Search components by various criteria
        
        Parameters:
        - filters: dict (search criteria)
        
        Returns:
        - components: list of component dicts
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Build query dynamically based on filters
            query = "SELECT * FROM components WHERE 1=1"
            params = []
            
            if 'region' in filters:
                query += " AND region = ?"
                params.append(filters['region'])
            
            if 'division' in filters:
                query += " AND division = ?"
                params.append(filters['division'])
            
            if 'component_type' in filters:
                query += " AND component_type = ?"
                params.append(filters['component_type'])
            
            if 'year' in filters:
                query += " AND year = ?"
                params.append(filters['year'])
            
            if 'track_id' in filters:
                query += " AND track_id = ?"
                params.append(filters['track_id'])
            
            if 'status' in filters:
                query += " AND status = ?"
                params.append(filters['status'])
            
            # Add ordering
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            columns = [description[0] for description in cursor.description]
            components = [dict(zip(columns, row)) for row in rows]
            
            return components
    
    def get_component_by_qr(self, qr_data: str) -> Optional[Dict]:
        """
        Get component data by QR code
        
        Parameters:
        - qr_data: str
        
        Returns:
        - component: dict or None
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM components WHERE qr_data = ?', (qr_data,))
            row = cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            
            return None
    
    def log_generation(self, qr_data: str, generation_type: str, 
                      batch_id: str = None, file_path: str = None, 
                      quality_score: float = None):
        """
        Log QR code generation
        
        Parameters:
        - qr_data: str
        - generation_type: str ('single', 'batch')
        - batch_id: str (optional)
        - file_path: str (optional)
        - quality_score: float (optional)
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO generation_logs (qr_data, generation_type, batch_id, file_path, quality_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (qr_data, generation_type, batch_id, file_path, quality_score))
            
            conn.commit()
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics
        
        Returns:
        - stats: dict with various statistics
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total components
            cursor.execute('SELECT COUNT(*) FROM components')
            total_components = cursor.fetchone()[0]
            
            # Components by type
            cursor.execute('''
                SELECT component_type, COUNT(*) 
                FROM components 
                GROUP BY component_type 
                ORDER BY COUNT(*) DESC
            ''')
            by_type = dict(cursor.fetchall())
            
            # Components by region
            cursor.execute('''
                SELECT region, COUNT(*) 
                FROM components 
                GROUP BY region 
                ORDER BY COUNT(*) DESC
            ''')
            by_region = dict(cursor.fetchall())
            
            # Recent generations
            cursor.execute('''
                SELECT COUNT(*) 
                FROM generation_logs 
                WHERE created_at >= datetime('now', '-7 days')
            ''')
            recent_generations = cursor.fetchone()[0]
            
            return {
                'total_components': total_components,
                'by_type': by_type,
                'by_region': by_region,
                'recent_generations': recent_generations
            }
    
    def export_to_csv(self, output_file: str, filters: Dict = None) -> bool:
        """
        Export component data to CSV file
        
        Parameters:
        - output_file: str (output file path)
        - filters: dict (optional filters)
        
        Returns:
        - success: bool
        """
        
        try:
            import pandas as pd
            
            components = self.search_components(filters or {})
            
            if not components:
                return False
            
            df = pd.DataFrame(components)
            df.to_csv(output_file, index=False)
            
            return True
            
        except ImportError:
            print("pandas not available for CSV export")
            return False
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False


if __name__ == "__main__":
    # Test the database manager
    db = RailwayDatabaseManager()
    
    # Test saving component data
    test_qr = "IR-WR-BCT-021-114320-BOLT-2024-001234"
    test_specs = {
        'material': 'Steel',
        'size': 'M20',
        'manufacturer': 'Railway Component Co.',
        'status': 'ACTIVE'
    }
    
    success = db.save_component_data(test_qr, test_specs)
    print(f"Saved component: {success}")
    
    # Test getting next serial number
    next_serial = db.get_next_serial_number('WR', 'BCT', 'BOLT', 2024)
    print(f"Next serial number: {next_serial}")
    
    # Test statistics
    stats = db.get_statistics()
    print(f"Database statistics: {stats}")
