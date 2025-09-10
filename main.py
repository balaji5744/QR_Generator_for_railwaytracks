"""
Main CLI Interface for Railway QR Code Generation System
Command-line interface for Smart India Hackathon demo
"""

import click
import os
import sys
from datetime import datetime
from typing import List, Dict

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from qr_generator import RailwayQRGenerator
from data_validator import RailwayDataValidator
from database_manager import RailwayDatabaseManager
from batch_processor import RailwayBatchProcessor
from quality_checker import RailwayQRQualityChecker
from config import RAILWAY_REGIONS, RAILWAY_DIVISIONS, COMPONENT_TYPES


@click.group()
def cli():
    """Railway QR Code Generation System for Smart India Hackathon"""
    pass


@cli.command()
@click.option('--region', required=True, help='Railway region (e.g., WR, CR, NR)')
@click.option('--division', required=True, help='Railway division (e.g., BCT, CSMT, DLI)')
@click.option('--track', 'track_id', required=True, type=int, help='Track ID (1-999)')
@click.option('--km', 'km_marker', required=True, type=int, help='KM marker (0-999999)')
@click.option('--type', 'component_type', required=True, help='Component type (BOLT, CLIP, PLATE, etc.)')
@click.option('--year', required=True, type=int, help='Year (2020-2030)')
@click.option('--serial', 'serial_number', type=int, help='Serial number (auto-generate if not provided)')
@click.option('--output', '-o', help='Output directory (default: output/qr_codes)')
@click.option('--material', help='Component material')
@click.option('--size', help='Component size')
@click.option('--manufacturer', help='Manufacturer name')
def generate(region, division, track_id, km_marker, component_type, year, 
            serial_number, output, material, size, manufacturer):
    """Generate a single QR code for railway component"""
    
    try:
        # Initialize components
        generator = RailwayQRGenerator()
        db_manager = RailwayDatabaseManager()
        validator = RailwayDataValidator()
        
        # Auto-generate serial number if not provided
        if serial_number is None:
            serial_number = db_manager.get_next_serial_number(region, division, component_type, year)
            click.echo(f"Auto-generated serial number: {serial_number}")
        
        # Validate inputs
        validation_result = validator.validate_components(
            region, division, track_id, km_marker, component_type, year, serial_number
        )
        
        if not validation_result['is_valid']:
            click.echo(f"❌ Validation Error: {validation_result['error_message']}", err=True)
            return
        
        # Generate QR code
        click.echo("🔧 Generating QR code...")
        filepath, qr_data = generator.generate_and_save(
            region, division, track_id, km_marker, component_type, year, serial_number, output
        )
        
        # Save to database
        component_specs = {
            'material': material,
            'size': size,
            'manufacturer': manufacturer,
            'status': 'ACTIVE'
        }
        
        db_success = db_manager.save_component_data(qr_data, component_specs)
        
        # Log generation
        db_manager.log_generation(qr_data, 'single', file_path=filepath)
        
        # Display results
        click.echo(f"✅ QR Code Generated Successfully!")
        click.echo(f"📄 QR Data: {qr_data}")
        click.echo(f"💾 File: {filepath}")
        click.echo(f"🗄️  Database: {'Saved' if db_success else 'Failed'}")
        
        # Show QR code info
        click.echo(f"\n📊 Component Details:")
        click.echo(f"   Region: {region} ({RAILWAY_REGIONS.get(region, 'Unknown')})")
        click.echo(f"   Division: {division}")
        click.echo(f"   Track: {track_id:03d}")
        click.echo(f"   KM Marker: {km_marker:06d}")
        click.echo(f"   Type: {component_type}")
        click.echo(f"   Year: {year}")
        click.echo(f"   Serial: {serial_number:06d}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
@click.option('--input', '-i', required=True, help='Input CSV file with component data')
@click.option('--output', '-o', help='Output directory (default: output/qr_codes)')
@click.option('--auto-serial', is_flag=True, help='Auto-generate serial numbers')
@click.option('--zip', is_flag=True, help='Create ZIP archive of generated QR codes')
@click.option('--quality-check', is_flag=True, help='Perform quality check on generated codes')
def batch(input, output, auto_serial, zip, quality_check):
    """Generate multiple QR codes from CSV file"""
    
    try:
        # Initialize components
        processor = RailwayBatchProcessor()
        quality_checker = RailwayQRQualityChecker()
        
        # Load components from CSV
        click.echo(f"📂 Loading components from {input}...")
        components = processor.load_components_from_csv(input)
        
        if not components:
            click.echo("❌ No valid components found in CSV file", err=True)
            return
        
        click.echo(f"📋 Found {len(components)} components")
        
        # Auto-generate serial numbers if requested
        if auto_serial:
            click.echo("🔢 Auto-generating serial numbers...")
            components = processor.generate_auto_serial_batch(components)
        
        # Generate batch QR codes
        click.echo("🔧 Generating QR codes...")
        result = processor.generate_batch_qr(components, output)
        
        # Display results
        click.echo(f"\n✅ Batch Generation Complete!")
        click.echo(f"🆔 Batch ID: {result['batch_id']}")
        click.echo(f"✅ Successful: {result['success_count']}")
        click.echo(f"❌ Failed: {result['failed_count']}")
        click.echo(f"📊 Report: {result['report_file']}")
        
        # Quality check if requested
        if quality_check and result['successful_generations']:
            click.echo("\n🔍 Performing quality check...")
            qr_files = [item['filepath'] for item in result['successful_generations']]
            quality_results = quality_checker.batch_quality_check(qr_files)
            
            click.echo(f"📈 Average Quality Score: {quality_results['average_quality_score']}")
            click.echo(f"📖 Readability Rate: {quality_results['readability_rate']}%")
            
            # Generate quality report
            quality_report_path = result['report_file'].replace('.csv', '_quality.csv')
            quality_checker.generate_quality_report(quality_results, quality_report_path)
            click.echo(f"📊 Quality Report: {quality_report_path}")
        
        # Create ZIP archive if requested
        if zip and result['successful_generations']:
            click.echo("\n📦 Creating ZIP archive...")
            qr_files = [item['filepath'] for item in result['successful_generations']]
            zip_path = os.path.join(output or 'output/qr_codes', f"qr_codes_{result['batch_id']}.zip")
            
            if processor.create_zip_archive(qr_files, zip_path):
                click.echo(f"📦 ZIP Archive: {zip_path}")
            else:
                click.echo("❌ Failed to create ZIP archive", err=True)
        
        # Show failed components if any
        if result['failed_generations']:
            click.echo(f"\n❌ Failed Components ({len(result['failed_generations'])}):")
            for failed in result['failed_generations'][:5]:  # Show first 5
                click.echo(f"   - {failed['error']}")
            if len(result['failed_generations']) > 5:
                click.echo(f"   ... and {len(result['failed_generations']) - 5} more")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
@click.option('--path', '-p', required=True, help='Path to QR code image file')
@click.option('--detailed', is_flag=True, help='Show detailed analysis')
def verify(path, detailed):
    """Verify quality of a QR code"""
    
    try:
        quality_checker = RailwayQRQualityChecker()
        
        if not os.path.exists(path):
            click.echo(f"❌ File not found: {path}", err=True)
            return
        
        click.echo(f"🔍 Analyzing QR code: {path}")
        result = quality_checker.verify_qr_quality(path)
        
        # Display results
        quality_score = result['quality_score']
        is_readable = result['is_readable']
        
        # Color coding for quality score
        if quality_score >= 90:
            score_color = "green"
        elif quality_score >= 70:
            score_color = "yellow"
        else:
            score_color = "red"
        
        click.echo(f"\n📊 Quality Analysis Results:")
        click.echo(f"🎯 Quality Score: {quality_score}/100")
        click.echo(f"📖 Readable: {'✅ Yes' if is_readable else '❌ No'}")
        
        if result['issues']:
            click.echo(f"\n⚠️  Issues Found:")
            for issue in result['issues']:
                click.echo(f"   - {issue}")
        else:
            click.echo(f"\n✅ No issues detected!")
        
        # Detailed analysis
        if detailed:
            analysis = result['detailed_analysis']
            click.echo(f"\n🔬 Detailed Analysis:")
            click.echo(f"   Size Score: {analysis.get('size_score', 0):.1f}/100")
            click.echo(f"   Contrast Score: {analysis.get('contrast_score', 0):.1f}/100")
            click.echo(f"   Sharpness Score: {analysis.get('sharpness_score', 0):.1f}/100")
            click.echo(f"   Alignment Score: {analysis.get('alignment_score', 0):.1f}/100")
            click.echo(f"   Readability Score: {analysis.get('readability_score', 0):.1f}/100")
            
            dimensions = analysis.get('image_dimensions', (0, 0))
            click.echo(f"   Image Size: {dimensions[1]}x{dimensions[0]} pixels")
            click.echo(f"   File Size: {analysis.get('file_size', 0)} bytes")
        
        # Suggestions
        suggestions = quality_checker.suggest_improvements(result)
        if suggestions:
            click.echo(f"\n💡 Suggestions:")
            for suggestion in suggestions:
                click.echo(f"   - {suggestion}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['csv', 'json']), default='csv', help='Output format')
@click.option('--output', '-o', help='Output file path')
@click.option('--region', help='Filter by region')
@click.option('--division', help='Filter by division')
@click.option('--type', 'component_type', help='Filter by component type')
@click.option('--year', type=int, help='Filter by year')
def report(output_format, output, region, division, component_type, year):
    """Generate reports from database"""
    
    try:
        db_manager = RailwayDatabaseManager()
        
        # Build filters
        filters = {}
        if region:
            filters['region'] = region
        if division:
            filters['division'] = division
        if component_type:
            filters['component_type'] = component_type
        if year:
            filters['year'] = year
        
        # Search components
        click.echo("🔍 Searching database...")
        components = db_manager.search_components(filters)
        
        if not components:
            click.echo("❌ No components found matching criteria", err=True)
            return
        
        click.echo(f"📋 Found {len(components)} components")
        
        # Generate output file path
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"output/reports/railway_components_{timestamp}.{output_format}"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output), exist_ok=True)
        
        # Export data
        if output_format == 'csv':
            success = db_manager.export_to_csv(output, filters)
            if success:
                click.echo(f"✅ CSV Report: {output}")
            else:
                click.echo("❌ Failed to generate CSV report", err=True)
        else:
            click.echo("❌ JSON export not implemented yet", err=True)
        
        # Show statistics
        stats = db_manager.get_statistics()
        click.echo(f"\n📊 Database Statistics:")
        click.echo(f"   Total Components: {stats['total_components']}")
        click.echo(f"   Recent Generations: {stats['recent_generations']}")
        
        if stats['by_type']:
            click.echo(f"   By Type:")
            for comp_type, count in list(stats['by_type'].items())[:5]:
                click.echo(f"     {comp_type}: {count}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
def stats():
    """Show database statistics"""
    
    try:
        db_manager = RailwayDatabaseManager()
        stats = db_manager.get_statistics()
        
        click.echo("📊 Railway QR Code Database Statistics")
        click.echo("=" * 50)
        click.echo(f"Total Components: {stats['total_components']}")
        click.echo(f"Recent Generations (7 days): {stats['recent_generations']}")
        
        if stats['by_type']:
            click.echo(f"\n📋 Components by Type:")
            for comp_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
                click.echo(f"   {comp_type}: {count}")
        
        if stats['by_region']:
            click.echo(f"\n🚂 Components by Region:")
            for region, count in sorted(stats['by_region'].items(), key=lambda x: x[1], reverse=True):
                region_name = RAILWAY_REGIONS.get(region, 'Unknown')
                click.echo(f"   {region} ({region_name}): {count}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)


@cli.command()
def demo():
    """Run demo with sample data"""
    
    try:
        click.echo("🚂 Railway QR Code Generation System Demo")
        click.echo("=" * 50)
        
        # Initialize components
        generator = RailwayQRGenerator()
        db_manager = RailwayDatabaseManager()
        quality_checker = RailwayQRQualityChecker()
        
        # Demo data
        demo_components = [
            {
                'region': 'WR',
                'division': 'BCT',
                'track_id': 21,
                'km_marker': 114320,
                'component_type': 'BOLT',
                'year': 2024,
                'serial_number': 1001,
                'material': 'Steel',
                'size': 'M20',
                'manufacturer': 'Railway Component Co.'
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
                'size': 'Standard',
                'manufacturer': 'Track Solutions Ltd.'
            },
            {
                'region': 'NR',
                'division': 'DLI',
                'track_id': 67,
                'km_marker': 234100,
                'component_type': 'PLATE',
                'year': 2024,
                'serial_number': 3001,
                'material': 'Steel',
                'size': 'Heavy Duty',
                'manufacturer': 'Northern Rails Inc.'
            }
        ]
        
        click.echo("🔧 Generating demo QR codes...")
        
        generated_files = []
        for i, component in enumerate(demo_components, 1):
            click.echo(f"   {i}. Generating {component['component_type']} for {component['region']}-{component['division']}...")
            
            # Generate QR code
            filepath, qr_data = generator.generate_and_save(
                component['region'], component['division'], component['track_id'],
                component['km_marker'], component['component_type'], component['year'],
                component['serial_number']
            )
            
            # Save to database
            component_specs = {
                'material': component['material'],
                'size': component['size'],
                'manufacturer': component['manufacturer'],
                'status': 'ACTIVE'
            }
            
            db_manager.save_component_data(qr_data, component_specs)
            db_manager.log_generation(qr_data, 'demo', file_path=filepath)
            
            generated_files.append(filepath)
            click.echo(f"      ✅ {qr_data}")
        
        # Quality check
        click.echo(f"\n🔍 Performing quality check...")
        quality_results = quality_checker.batch_quality_check(generated_files)
        
        click.echo(f"📈 Average Quality Score: {quality_results['average_quality_score']}/100")
        click.echo(f"📖 Readability Rate: {quality_results['readability_rate']}%")
        
        # Show statistics
        stats = db_manager.get_statistics()
        click.echo(f"\n📊 Database Statistics:")
        click.echo(f"   Total Components: {stats['total_components']}")
        
        click.echo(f"\n✅ Demo completed successfully!")
        click.echo(f"📁 Generated files in: output/qr_codes/")
        click.echo(f"🗄️  Database: models/database.db")
        
    except Exception as e:
        click.echo(f"❌ Demo Error: {str(e)}", err=True)


if __name__ == '__main__':
    cli()
