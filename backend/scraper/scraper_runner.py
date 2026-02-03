#!/usr/bin/env python3
"""
Master Scraper Runner
Orchestrates the complete pipeline:
Scrapers (Simple) → Raw JSON Files → Central Cleaner (Smart) → Master JSON (Standardized)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cleaner.cleaner_intergated import IntegratedProductCleaner
from bestwayScraper import BestwayScraper
from laxmiScraper import LakshmiGroceryScraper


class ScraperRunner:
    """Orchestrates the scraping and cleaning pipeline"""
    
    def __init__(self, output_dir: str = "./data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.cleaner = IntegratedProductCleaner()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def run_bestway_scraper(self, target_products: int = 100) -> dict:
        """Run Bestway scraper and return results"""
        print("\n" + "="*80)
        print("🛒 RUNNING BESTWAY WHOLESALE SCRAPER")
        print("="*80)
        
        try:
            scraper = BestwayScraper(target_products=target_products, output_dir=str(self.output_dir))
            all_products, cleaned_products = scraper.run_full_pipeline()
            
            return {
                'source': 'Bestway',
                'status': 'completed',
                'raw_count': len(all_products) if isinstance(all_products, list) else 0,
                'cleaned_count': len(cleaned_products) if cleaned_products else 0
            }
        except Exception as e:
            print(f"❌ Error running Bestway scraper: {e}")
            return {'source': 'Bestway', 'status': 'failed', 'error': str(e)}
    
    def run_laxmi_scraper(self, with_details: bool = True) -> dict:
        """Run Laxmi scraper and return results"""
        print("\n" + "="*80)
        print("🏪 RUNNING LAKSHMI WHOLESALE SCRAPER")
        print("="*80)
        
        try:
            scraper = LakshmiGroceryScraper()
            all_products, cleaned_products = scraper.run_full_pipeline(with_details=with_details)
            
            return {
                'source': 'Lakshmi',
                'status': 'completed',
                'raw_count': len(all_products) if isinstance(all_products, list) else 0,
                'cleaned_count': len(cleaned_products) if cleaned_products else 0
            }
        except Exception as e:
            print(f"❌ Error running Laxmi scraper: {e}")
            return {'source': 'Lakshmi', 'status': 'failed', 'error': str(e)}
    
    def merge_and_standardize(self, source_configs: list) -> list:
        """
        Merge products from multiple sources and standardize to master schema
        
        Args:
            source_configs: List of dicts with 'file', 'name', 'url' keys
        
        Returns:
            List of standardized products
        """
        print("\n" + "="*80)
        print("🔀 MERGING AND STANDARDIZING ALL SOURCES")
        print("="*80)
        
        all_cleaned_products = []
        
        for config in source_configs:
            file_path = config.get('file')
            source_name = config.get('name', 'Unknown')
            source_url = config.get('url', '')
            
            if not Path(file_path).exists():
                print(f"⚠️  Skipping {source_name}: file not found ({file_path})")
                continue
            
            print(f"\n📥 Processing {source_name}...")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_products = json.load(f)
                
                # Ensure it's a list
                if isinstance(raw_products, dict):
                    raw_products = [raw_products]
                elif not isinstance(raw_products, list):
                    raw_products = [raw_products]
                
                print(f"   Found {len(raw_products)} raw products")
                
                # Process through integrated cleaner
                cleaned_count = 0
                for i, raw_product in enumerate(raw_products, 1):
                    try:
                        # Clean and normalize
                        cleaned = self.cleaner.clean_and_normalize_product(raw_product)
                        
                        # Add source metadata
                        cleaned = self.cleaner.add_source_metadata(
                            cleaned,
                            source_name=source_name,
                            source_url=source_url
                        )
                        
                        # Enforce schema
                        cleaned = self.cleaner.enforce_schema(cleaned)
                        
                        all_cleaned_products.append(cleaned)
                        cleaned_count += 1
                        
                        if i % 20 == 0:
                            print(f"   Processed {i}/{len(raw_products)}...")
                    
                    except Exception as e:
                        print(f"   ⚠️  Error on product {i}: {e}")
                        continue
                
                print(f"   ✅ Cleaned {cleaned_count}/{len(raw_products)} products")
            
            except Exception as e:
                print(f"   ❌ Error processing {source_name}: {e}")
                continue
        
        return all_cleaned_products
    
    def save_master_json(self, products: list, filename: str = None) -> str:
        """Save master standardized JSON"""
        if filename is None:
            filename = f"master_products_{self.timestamp}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Master JSON saved: {output_path}")
        return str(output_path)
    
    def print_summary(self, products: list):
        """Print summary statistics"""
        print("\n" + "="*80)
        print("📊 PIPELINE SUMMARY")
        print("="*80)
        
        if not products:
            print("No products to summarize")
            return
        
        # Count by source
        sources = {}
        brands_found = set()
        categories_found = set()
        
        for product in products:
            source = product.get('Source Website Name', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
            
            if product.get('Brand'):
                brands_found.add(product['Brand'])
            if product.get('Category'):
                categories_found.add(product['Category'])
        
        print(f"\n📈 Total Products: {len(products)}")
        print(f"\n📍 By Source:")
        for source, count in sorted(sources.items()):
            print(f"   {source}: {count}")
        
        print(f"\n🏷️  Brands Found: {len(brands_found)}")
        print(f"📂 Categories Found: {len(categories_found)}")
        
        # Sample product
        if products:
            print(f"\n📄 Sample Product:")
            sample = products[0]
            print(f"   Name: {sample.get('Product Name', 'N/A')}")
            print(f"   Brand: {sample.get('Brand', 'N/A')}")
            print(f"   Category: {sample.get('Category', 'N/A')}")
            print(f"   Source: {sample.get('Source Website Name', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(
        description='Master Scraper Runner - Scrape, Clean, and Standardize'
    )
    
    parser.add_argument(
        '--bestway',
        action='store_true',
        help='Run Bestway scraper'
    )
    
    parser.add_argument(
        '--laxmi',
        action='store_true',
        help='Run Laxmi scraper'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all scrapers'
    )
    
    parser.add_argument(
        '--merge',
        action='store_true',
        help='Merge results from all sources',
        default=True
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output directory',
        default='./data'
    )
    
    args = parser.parse_args()
    
    runner = ScraperRunner(output_dir=args.output)
    
    # Decide which scrapers to run
    if args.all or (not args.bestway and not args.laxmi):
        run_bestway = True
        run_laxmi = True
    else:
        run_bestway = args.bestway
        run_laxmi = args.laxmi
    
    results = []
    
    # Run scrapers
    if run_bestway:
        result = runner.run_bestway_scraper()
        results.append(result)
    
    if run_laxmi:
        result = runner.run_laxmi_scraper()
        results.append(result)
    
    # Merge and standardize
    if args.merge:
        source_configs = [
            {
                'file': str(runner.output_dir / 'bestwayraw_products.json'),
                'name': 'Bestway Wholesale',
                'url': 'https://www.bestwaywholesale.co.uk'
            },
            {
                'file': str(Path(__file__).parent / 'all_products.json'),  # From laxmi scraper
                'name': 'Lakshmi Wholesale',
                'url': 'https://www.lakshmiwholesale.com'
            }
        ]
        
        master_products = runner.merge_and_standardize(source_configs)
        
        if master_products:
            output_file = runner.save_master_json(master_products)
            runner.print_summary(master_products)
        else:
            print("⚠️  No products to merge")
    
    print("\n" + "="*80)
    print("✅ PIPELINE EXECUTION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
