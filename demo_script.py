"""
Railway QR Code Generation System - Complete Demo Script
Smart India Hackathon 2025
"""

import os
import sys
import time

def print_header(title):
    print("\n" + "="*60)
    print(f"🚂 {title}")
    print("="*60)

def print_step(step_num, description):
    print(f"\n{step_num}. {description}")
    print("-" * 40)

def run_command(command, description):
    print(f"   Running: {description}")
    print(f"   Command: {command}")
    os.system(command)
    time.sleep(1)

def main():
    print_header("Railway QR Code Generation System - Complete Demo")
    print("Smart India Hackathon 2025")
    print("AI-based Laser QR Code marking for Railway Track Fittings")
    
    print_step(1, "System Overview & Statistics")
    run_command("python main.py stats", "Show current database statistics")
    
    print_step(2, "Single QR Code Generation")
    run_command("python main.py generate --region WR --division BCT --track 30 --km 150000 --type BOLT --year 2024 --material Steel --size M24 --manufacturer \"Demo Railway Co.\"", "Generate single QR code with specifications")
    
    print_step(3, "Batch QR Code Generation")
    run_command("python main.py batch --input sample_components.csv --auto-serial --quality-check", "Generate multiple QR codes from CSV with quality check")
    
    print_step(4, "Quality Verification Demo")
    # Find a generated QR code file
    qr_files = [f for f in os.listdir("output/qr_codes") if f.endswith(".png")]
    if qr_files:
        qr_file = qr_files[0]
        run_command(f"python main.py verify --path \"output/qr_codes/{qr_file}\" --detailed", f"Verify quality of generated QR code: {qr_file}")
    
    print_step(5, "Database Reports")
    run_command("python main.py report --format csv --output demo_report.csv", "Generate CSV report of all components")
    
    print_step(6, "Final Statistics")
    run_command("python main.py stats", "Show final database statistics")
    
    print_header("Demo Complete!")
    print("✅ All features demonstrated successfully!")
    print("\n📁 Generated Files:")
    print("   - QR Codes: output/qr_codes/")
    print("   - Reports: output/reports/")
    print("   - Database: models/database.db")
    
    print("\n🎯 Key Features Demonstrated:")
    print("   ✅ Railway-specific QR code format")
    print("   ✅ Automatic serial number generation")
    print("   ✅ Batch processing from CSV")
    print("   ✅ AI-based quality verification")
    print("   ✅ Database tracking and reporting")
    print("   ✅ Component lifecycle management")
    
    print("\n🚀 Ready for Smart India Hackathon Presentation!")

if __name__ == "__main__":
    main()
