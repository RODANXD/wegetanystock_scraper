#!/usr/bin/env python3
# main_integrated.py
"""
Main Pipeline Runner with Integrated Cleaner
Includes brand detection, product cleaning, and description extraction
"""

import argparse
from pathlib import Path
from cleaner_integrated import IntegratedProductCleaner, clean_and_merge


def main():
    """
    Main entry point for the integrated data cleaning pipeline
    """
    
    parser = argparse.ArgumentParser(
        description='Clean and normalize e-commerce product data with brand detection'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to JSON config file with source definitions',
        default=None
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path for master JSON',
        default='master_products.json'
    )
    
    parser.add_argument(
        '--brands',
        type=str,
        help='Path to brands.json file',
        default=None
    )
    
    parser.add_argument(
        '--sources',
        nargs='+',
        help='Source files: format is "file:name:url"',
        default=None
    )
    
    args = parser.parse_args()
    
    # Determine source configuration
    if args.config:
        # Load from config file
        import json
        with open(args.config, 'r') as f:
            config = json.load(f)
            source_configs = config.get('sources', [])
    
    elif args.sources:
        # Parse from command line
        source_configs = []
        for source_spec in args.sources:
            parts = source_spec.split(':')
            if len(parts) != 3:
                print(f"⚠️  Invalid source spec: {source_spec}")
                print("   Expected format: file:name:url")
                continue
            
            source_configs.append({
                'file': parts[0],
                'name': parts[1],
                'url': parts[2]
            })
    
    else:
        # Use default example
        print("No sources specified. Using example configuration...")
        source_configs = [
            {
                'file': 'data/raw_amazon.json',
                'name': 'Amazon',
                'url': 'https://amazon.com'
            },
            {
                'file': 'data/raw_walmart.json',
                'name': 'Walmart',
                'url': 'https://walmart.com'
            }
        ]
    
    # Validate source files exist
    valid_sources = []
    for config in source_configs:
        if not Path(config['file']).exists():
            print(f"⚠️  File not found: {config['file']} - skipping")
            continue
        valid_sources.append(config)
    
    if not valid_sources:
        print("\n❌ ERROR: No valid source files found!")
        print("\nTo create example data, run:")
        print("  python create_example_data.py")
        print("\nOr specify sources:")
        print("  python main_integrated.py --sources data/file1.json:Site1:https://site1.com")
        return
    
    # Run the pipeline
    print("\n" + "="*70)
    print("INTEGRATED PRODUCT DATA CLEANING PIPELINE")
    print("="*70)
    print("✓ Brand Detection with Auto-Learning")
    print("✓ Product Name Cleaning")
    print("✓ Description Extraction")
    print("✓ Field Normalization")
    print("✓ Smart Inference")
    print("="*70)
    
    products = clean_and_merge(valid_sources, args.output, args.brands)
    
    print("\n" + "="*70)
    print("✓ PIPELINE COMPLETE")
    print("="*70)
    
    return products


if __name__ == "__main__":
    main()