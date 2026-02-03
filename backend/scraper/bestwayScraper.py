#!/usr/bin/env python3
"""
Bestway Wholesale Scraper
Scrapes products from https://www.bestwaywholesale.co.uk/grocery
Integrates with the central cleaning pipeline
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import sys
from pathlib import Path

# Add parent directory to path to handle relative imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cleaner.cleaner_intergated import IntegratedProductCleaner


class BestwayScraper:
    """Scraper for Bestway Wholesale UK"""
    
    def __init__(self, target_products: int = 100, output_dir: str = "../data"):
        self.base_url = "https://www.bestwaywholesale.co.uk/grocery"
        self.target_products = target_products
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }
        
        self.all_products = []
        self.cleaner = IntegratedProductCleaner()
        self.items_per_page = 20
    
    def scrape_product_details(self, product_url):
        """Scrape additional details from individual product page"""
        try:
            response = requests.get(product_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            
            def get_table_value(label):
                th = soup.find("th", string=lambda x: x and label.lower() in x.lower())
                if th:
                    td = th.find_next_sibling("td")
                    return td.get_text(strip=True) if td else None
                return None
            
            # Extract description
            description_tab = soup.find("div", class_="accordionButton", string="Description")
            description_content = description_tab.find_next_sibling(
                "div", class_="accordionContent"
            ) if description_tab else None

            description = None
            description_bullets = []
            if description_content:
                description_bullets = [
                    li.get_text(strip=True)
                    for li in description_content.select("ul li")
                ]
                desc_p = description_content.select_one('[itemprop="description"] p')
                description = desc_p.get_text(strip=True) if desc_p else None
            
            # Extract ingredients
            nutritions = {}

            ingredients_tab = soup.find(
                "div",
                class_="accordionButton",
                string=lambda x: x and "ingredients" in x.lower()
            )
            
            ingredients_content = (
                ingredients_tab.find_next_sibling("div", class_="accordionContent")
                if ingredients_tab else None
            )
            
            if ingredients_content:
                h2 = ingredients_content.find(
                    "h2",
                    string=lambda x: x and "nutritional information" in x.lower()
                )
            
                if h2:
                    table = h2.find_next("table")
            
                    if table:
                        for row in table.find_all("tr"):
                            th = row.find("th")
                            td = row.find("td")   # only ONE td per row in your HTML
            
                            if th and td and th.get_text(strip=True):
                                nutritions[th.get_text(strip=True)] = td.get_text(strip=True)
            
            print(nutritions)

            
            # Extract other info
            other_tab = soup.find(
                "div", class_="accordionButton", string=lambda x: x and "other info" in x.lower()
            )
            other_content = other_tab.find_next_sibling(
                "div", class_="accordionContent"
            ) if other_tab else None

            other_info = []
            if other_content:
                other_info = [li.get_text(strip=True) for li in other_content.select("ul li")]
            
            return {
                "product": get_table_value("Product"),
                "rsp": get_table_value("RSP:"),
                "brand": get_table_value("Brand:"),
                "size": get_table_value("Pack Size:"),
                "product_code": get_table_value("Product Code:"),
                "Retail Ean": get_table_value("Retail EAN:"),
                "vat_rate": get_table_value("VAT Rate:"),
                "description": description,
                "description_bullets": description_bullets,
                "ingredients_description": nutritions,
                "other_info": other_info,
            }
        except Exception as e:
            print(f"Error scraping details for {product_url}: {e}")
            return {"product": None, "rsp": None, "brand": None}
    
    def scrape_products(self):
        """Scrape products from all pages"""
        print("=" * 70)
        print("PHASE 1: SCRAPING RAW PRODUCTS")
        print("=" * 70)
        
        page = 0
        
        try:
            while len(self.all_products) < self.target_products:
                # Construct URL with pagination parameter
                url = f"{self.base_url}?s={page * self.items_per_page}"
                print(f"\n🔍 Scraping page {page}... (Current count: {len(self.all_products)})")
                
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Find main container
                container = soup.find("div", class_="shop-products-column")
                
                if not container:
                    print("❌ No products container found. Pagination may have ended.")
                    break

                # Get all product items
                products = container.select("ul.shop-products > li")

                if not products:
                    print("❌ No products found on this page. Stopping.")
                    break

                print(f"✅ Found {len(products)} products on page {page}")

                for product in products:
                    if len(self.all_products) >= self.target_products:
                        break
                        
                    product_id = product.get("data-ga-product-id")
                    name = product.get("data-ga-product-name")
                    price = product.get("data-ga-product-price")
                    category = product.get("data-ga-product-category")
                    url_path = product.get("data-ga-product-url")
                    product_img = product.get("data-ga-product-image") 
                    img_tag = product.select_one(".prodimageinner img")
                    
                    image_url = None
                    if img_tag:
                        image_url = img_tag.get("src") or img_tag.get("data-src")
                        # Handle relative URLs
                        if image_url and image_url.startswith("/"):
                            image_url = f"https://www.bestwaywholesale.co.uk{image_url}"

                    sku = product.select_one(".prodsku")
                    size = product.select_one(".prodsize")

                    product_data = {
                        "id": product_id,
                        "name": name,
                        "price": price,
                        "category": category,
                        "sku": sku.text.replace("SKU:", "").strip() if sku else None,
                        "multi pack": size.text.strip() if size else None,
                        "image": image_url,
                        "url": f"https://www.bestwaywholesale.co.uk{url_path}"
                    }
                    
                    # Scrape additional details from product page
                    if url_path:
                        product_url = f"https://www.bestwaywholesale.co.uk{url_path}"
                        details = self.scrape_product_details(product_url)
                        product_data.update(details)
                    
                    self.all_products.append(product_data)
                    print(f"   {len(self.all_products)}. {name}")

                page += 1
                time.sleep(1)  # Be respectful to the server
        
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            return False
        
        return True
    
    def save_raw_products(self):
        """Save raw products to JSON"""
        print("\n" + "=" * 70)
        print("PHASE 1.5: SAVING RAW DATA")
        print("=" * 70)
        
        raw_output_file = self.output_dir / "bestwayraw_products.json"
        
        with open(raw_output_file, "w", encoding="utf-8") as f:
            json.dump(self.all_products, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully scraped {len(self.all_products)} products!")
        print(f"📁 Raw data saved to {raw_output_file}")
        
        return raw_output_file
    
    def clean_and_save_products(self):
        """Clean products and save cleaned output"""
        print("\n" + "=" * 70)
        print("PHASE 2: CLEANING AND NORMALIZING")
        print("=" * 70)
        print("   ├─ Product name cleaning")
        print("   ├─ Brand detection with auto-learning")
        print("   ├─ Field normalization")
        print("   └─ Schema enforcement")
        
        # Process each raw product through the integrated cleaner
        cleaned_products = []
        for i, raw_product in enumerate(self.all_products, 1):
            try:
                # Clean and normalize the product
                cleaned_product = self.cleaner.clean_and_normalize_product(raw_product)
                
                # Add source metadata
                cleaned_product = self.cleaner.add_source_metadata(
                    cleaned_product,
                    source_name="Bestway Wholesale",
                    source_url="https://www.bestwaywholesale.co.uk"
                )
                
                # Enforce schema
                cleaned_product = self.cleaner.enforce_schema(cleaned_product)
                
                cleaned_products.append(cleaned_product)
                
                if i % 10 == 0:
                    print(f"   Processed {i}/{len(self.all_products)} products...")
                    
            except Exception as e:
                print(f"   ⚠️  Error processing product {i}: {e}")
                continue
        
        # Save cleaned data
        print("\n" + "=" * 70)
        print("PHASE 2.5: SAVING CLEANED DATA")
        print("=" * 70)
        
        cleaned_output_file = self.output_dir / "bestway_cleaned_products.json"
        with open(cleaned_output_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_products, f, indent=2, ensure_ascii=False)
        
        print(f"✨ Cleaned {len(cleaned_products)} products successfully!")
        print(f"📁 Cleaned data saved to {cleaned_output_file}")
        print(f"\n📊 Pipeline Summary:")
        print(f"   Raw products: {len(self.all_products)}")
        print(f"   Cleaned products: {len(cleaned_products)}")
        if len(self.all_products) > 0:
            print(f"   Success rate: {len(cleaned_products)/len(self.all_products)*100:.1f}%")
        
        return cleaned_output_file, cleaned_products
    
    def run_full_pipeline(self):
        """Run complete pipeline: scrape → save raw → clean → save cleaned"""
        print("\n" + "=" * 80)
        print("🛒 BESTWAY WHOLESALE SCRAPER - FULL PIPELINE")
        print("=" * 80)
        
        # Phase 1: Scrape
        if not self.scrape_products():
            print("❌ Scraping failed")
            return None, None
        
        # Phase 1.5: Save raw
        raw_file = self.save_raw_products()
        
        # Phase 2: Clean
        cleaned_file, cleaned_products = self.clean_and_save_products()
        
        print("\n" + "=" * 80)
        print("✅ BESTWAY PIPELINE COMPLETE")
        print("=" * 80)
        
        return self.all_products, cleaned_products


# ============================================================================
# MAIN - Run as standalone script
# ============================================================================

if __name__ == "__main__":
    scraper = BestwayScraper(target_products=100)
    all_products, cleaned_products = scraper.run_full_pipeline()
    
    if cleaned_products:
        print("\n✅ Pipeline completed successfully!")
    else:
        print("\n❌ Pipeline failed")
    # print("Error:", e)

