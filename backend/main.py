"""
Main Entry Point - Run Scraper and Cleaner
"""

import json
import os
import sys
import logging


logging.basicConfig(level=logging.DEBUG)


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from scraper.scraper import Product_Scraper
from cleaner.cleaner import ProductCleaner


def get_data_path(filename):
    """Get path to data file"""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, filename)


def run_scraper(target_count=100):
    """Run the web scraper"""
    print("\n" + "=" * 60)
    print("🕷️  STEP 1: SCRAPING PRODUCTS (Cloudflare Bypass)")
    print("=" * 60)
    
    scraper = Product_Scraper(
        delay_range=(3, 6)
    )
    
    brands = scraper.extract_brands_from_dropdown()
    scraper.save_brands(brands, "data/brands.json")
    print(f"📖 Extracted {len(brands)} brands")

    
    products = scraper.scrape_all(target_count=target_count)
    
    if products:
        output_path = get_data_path('raw_products.json')
        scraper.save_to_json(products, output_path)
        print(f"\n✅ Scraped {len(products)} products")
        print(f"📁 Saved to: {output_path}")
        return products
    else:
        print("❌ No products scraped!")
        return []


def run_cleaner():
    """Run the data cleaner"""
    print("\n" + "=" * 60)
    print("🧹 STEP 2: CLEANING DATA")
    print("=" * 60)
    
    input_path = get_data_path('raw_products.json')
    output_path = get_data_path('cleaned_products.json')
    frontend_path = r'C:\Users\ankun\NewdjangoEnv\Product_scraping\frontend\src\data\cleaned_products.json'
    
    if not os.path.exists(input_path):
        print(f"❌ File not found: {input_path}")
        print("Please run the scraper first!")
        return []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📖 Loaded {len(products)} products")
    
    cleaner = ProductCleaner()
    cleaned_products = cleaner.clean_products(products)
    
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_products, f, indent=2, ensure_ascii=False)
    
    
    os.makedirs(os.path.dirname(frontend_path), exist_ok=True)
    with open(frontend_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_products, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Cleaned {len(cleaned_products)} products")
    print(f"📁 Saved to: {output_path}")
    print(f"📁 Saved to: {frontend_path}")
    

    
    for product in cleaned_products[:5]:
        print(f"\n  Original:  {product.get('original_name', 'N/A')}")
        print(f"  Cleaned:   {product.get('cleaned_name', 'N/A')}")
        print(f"  Brand:     {product.get('brand', 'Not detected')}")
        print(f"  Slug:      {product.get('slug', 'N/A')}")
        print(f"  Multipack: {product.get('is_multipack', False)}")
    
    return cleaned_products


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Product Scraper & Cleaner')
    parser.add_argument('--count', type=int, default=100, help='Number of products to scrape')
    parser.add_argument('--scrape-only', action='store_true', help='Only run scraper')
    parser.add_argument('--clean-only', action='store_true', help='Only run cleaner')
    
    args = parser.parse_args()
    
    print("\n" + "-" * 63)
    print("🚀 PRODUCT SCRAPER & CLEANER")
    print("-" * 63)
    
    if args.clean_only:
        run_cleaner()
    elif args.scrape_only:
        run_scraper(target_count=args.count)
    else:
        # Run both
        products = run_scraper(target_count=args.count)
        
        if products:
            cleaned = run_cleaner()
            
            print("\n" + "=" * 63)
            print("🎉 ALL DONE!")
            print("=" * 63)
            print(f"\n📊 Summary:")
            print(f"   - Raw products:     {len(products)}")
            print(f"   - Cleaned products: {len(cleaned)}")
            print(f"\n📁 Output files:")
            print(f"   - {get_data_path('raw_products.json')}")
            print(f"   - {get_data_path('cleaned_products.json')}")


if __name__ == "__main__":
    main()