import requests
from bs4 import BeautifulSoup
import json
import csv
import sys
from pathlib import Path

# Add parent directory to path to import cleaner
sys.path.insert(0, str(Path(__file__).parent.parent))
from cleaner.cleaner_intergated import IntegratedProductCleaner


class LakshmiGroceryScraper:
    def __init__(self):
        self.base_url = "https://www.lakshmiwholesale.com"
        self.session = requests.Session()

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

        self.grocery_data = {}
        self.product_cleaner = IntegratedProductCleaner()

        # 🔑 bypass age / wholesale gate
        self._verify_access()

    # --------------------------------------------------
    # AGE / WHOLESALE VERIFICATION
    # --------------------------------------------------
    def _verify_access(self):
        # establish session
        self.session.get(self.base_url, headers=self.headers, timeout=30)

        # set verification cookie
        self.session.cookies.set(
            "age_verified",
            "true",
            domain="lakshmiwholesale.com",
            path="/"
        )

    # --------------------------------------------------
    # FETCH PAGE
    # --------------------------------------------------
    def get_page(self, url):
        try:
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            print(f"❌ Error fetching {url}: {e}")
            return None

    # --------------------------------------------------
    # SCRAPE BRANDS NAVIGATION
    # --------------------------------------------------
    def get_brands_navigation(self):
        """
        Extract all brand names from the navigation
        
        Returns:
            list: List of brand names
        """
        print("🔍 Fetching brands from navigation...")
        soup = self.get_page(self.base_url)

        if not soup:
            return []

        # Find the BRANDS dropdown container
        brands_dropdown_container = None
        all_dropdowns = soup.find_all("div", class_="yv-dropdown-detail")
        
        print(f"[DEBUG] Searching for BRANDS in {len(all_dropdowns)} dropdown containers")
        
        for dropdown in all_dropdowns:
            link = dropdown.find("a", class_="dropdown-menu-item")
            if link and link.get_text(strip=True).upper() == "BRANDS":
                print("[DEBUG] ✓ Found BRANDS dropdown container")
                brands_dropdown_container = dropdown
                break
            
        if not brands_dropdown_container:
            print("❌ Brands dropdown not found")
            return []

        brands = []
        
        # Extract all brand links from the brands dropdown container
        brand_links = brands_dropdown_container.find_all("a", class_="yv-dropdown-item-link")
        
        print(f"✅ Found {len(brand_links)} brands")
        
        for link in brand_links:
            brand_name = link.get_text(strip=True)
            if brand_name:
                brands.append(brand_name)
                print(f"   ✓ {brand_name}")
        
        return sorted(list(set(brands)))  # Remove duplicates and sort

    # --------------------------------------------------
    # SCRAPE GROCERY NAVIGATION
    # --------------------------------------------------
    def get_grocery_navigation(self):
        print("🔍 Fetching homepage...")
        soup = self.get_page(self.base_url)

        if not soup:
            return None

        # find ONLY the grocery mega menu
        grocery_dropdown_container = None
        all_dropdowns = soup.find_all("div", class_="yv-dropdown-detail")
        
        print(f"[DEBUG] Found {len(all_dropdowns)} dropdown containers")
        
        for dropdown in all_dropdowns:
            link = dropdown.find("a", class_="dropdown-menu-item")
            if link and link.get_text(strip=True).upper() == "GROCERIES":
                print("[DEBUG] ✓ Found GROCERIES dropdown container")
                grocery_dropdown_container = dropdown
                break
            
        if not grocery_dropdown_container:
            print("❌ Grocery dropdown not found")
            return None

        grocery_data = {
            "main_category": "GROCERIES",
            "categories": []
        }

        # Extract categories from inside the grocery dropdown container
        category_blocks = grocery_dropdown_container.find_all(
            "div",
            class_="dropdown-inner-menu-item"
        )

        print(f"✅ Found {len(category_blocks)} grocery categories")

        for block in category_blocks:
            title_elem = block.find("a", class_="menu-category-title")
            if not title_elem:
                continue

            category_name = title_elem.get_text(strip=True)

            subcategories = []
            sub_links = block.find_all(
                "a",
                class_="yv-dropdown-item-link"
            )

            for link in sub_links:
                name = link.get_text(strip=True)
                href = link.get("href", "").strip()

                if not href.startswith("/collections/"):
                    continue

                subcategories.append({
                    "name": name,
                    "url": f"{self.base_url}{href}",
                    "relative_path": href,
                    "collection_slug": href.replace("/collections/", ""),
                    "products_api": f"{self.base_url}{href}/products.json"
                })

            grocery_data["categories"].append({
                "category_name": category_name,
                "subcategory_count": len(subcategories),
                "subcategories": subcategories
            })

        grocery_data["total_categories"] = len(grocery_data["categories"])
        grocery_data["total_subcategories"] = sum(
            c["subcategory_count"] for c in grocery_data["categories"]
        )

        self.grocery_data = grocery_data
        return grocery_data

    # --------------------------------------------------
    # SCRAPE PRODUCTS FROM COLLECTION URL
    # --------------------------------------------------
    def scrape_products(self, collection_url, category_name="", subcategory_name=""):
        """
        Scrape all products from a collection/category page
        
        Args:
            collection_url: URL of the collection page
            category_name: Parent category name (for reference)
            subcategory_name: Subcategory name (for reference)
            
        Returns:
            list: List of product dictionaries with details
        """
        print(f"\n🛍️  Scraping products from: {collection_url}")
        soup = self.get_page(collection_url)
        
        if not soup:
            print(f"❌ Failed to fetch {collection_url}")
            return []
        
        products = []
        
        # Find the products container
        products_container = soup.find("div", class_="row", attrs={"data-collection-products": ""})
        
        if not products_container:
            print("❌ Products container not found")
            return []
        
        # Find all product cards
        product_cards = products_container.find_all("div", class_="col-6", attrs={"data-product-grid": ""})
        
        print(f"[DEBUG] Found {len(product_cards)} product cards")
        
        for idx, card in enumerate(product_cards):
            try:
                # Extract product information
                product_info_div = card.find("div", class_="yv-product-information")
                product_img_div = card.find("div", class_="yv-product-card-img")
                
                if not product_info_div:
                    continue
                
                # Product name
                product_name_elem = product_info_div.find("a", class_="yv-product-title")
                product_name = product_name_elem.get_text(strip=True) if product_name_elem else "N/A"
                
                # Product URL - from the image link
                product_url = "N/A"
                if product_img_div:
                    img_link = product_img_div.find("a", class_="yv-product-img")
                    if img_link:
                        href = img_link.get("href", "").strip()
                        if href:
                            product_url = self.base_url + href if not href.startswith("http") else href
                
                # Price
                price_elem = product_info_div.find("span", class_="product-price")
                product_price = price_elem.get_text(strip=True) if price_elem else "N/A"
                
                # Product image
                img_elem = product_img_div.find("img") if product_img_div else None
                product_image = img_elem.get("src", "N/A") if img_elem else "N/A"
                
                # SKU or product ID (if available)
                product_id = card.get("data-product-id", "N/A")
                
                product_data = {
                    "name": product_name,
                    "price": product_price,
                    "url": product_url,
                    "image": product_image,
                    "product_id": product_id,
                    "category": category_name,
                    "subcategory": subcategory_name,
                }
                
                products.append(product_data)
                print(f"   ✓ [{idx+1}] {product_name}")
                
            except Exception as e:
                print(f"   ⚠️  Error parsing product {idx+1}: {e}")
                continue
        
        print(f"✅ Successfully scraped {len(products)} products")
        return products
    
    # --------------------------------------------------
    # SCRAPE PRODUCT DETAILS FROM PRODUCT PAGE
    # --------------------------------------------------
    # --------------------------------------------------
# SCRAPE PRODUCT DETAILS FROM PRODUCT PAGE
# --------------------------------------------------
    def scrape_product_details(self, product_url):
        print(f"🔍 Fetching details from: {product_url}")
        soup = self.get_page(product_url)

        details = {
            "description_html": "",
            "description_text": "",
            "allergy_warning": "",
            "storage_advice": ""
        }

        # ✅ FIX: Add None check
        if not soup:
            print(f"❌ Failed to fetch product page: {product_url}")
            return details

        accordion = soup.select_one("div.yv-product-accordion")
        print(f"[DEBUG] Accordion section: {'Found' if accordion else 'Not Found'}")

        if not accordion:
            # Try alternative selectors for product description
            print("[DEBUG] Trying alternative selectors...")

            # Try finding description in other common locations
            desc_div = soup.select_one("div.product-description")
            if desc_div:
                details["description_html"] = desc_div.decode_contents()
                details["description_text"] = desc_div.get_text("\n", strip=True)
                print(f"[DEBUG] Found description via alternative selector")

            return details

        for card in accordion.select("details.yv-accordion-card"):
            title = card.select_one("summary h6")
            if not title:
                continue

            section = title.get_text(strip=True).lower()
            print(f"[DEBUG] Found section: {section}")

            body = card.select_one("div.yv-content-body")
            if not body:
                continue

            text = body.get_text("\n", strip=True)
            html = body.decode_contents()

            if "description" in section:
                details["description_html"] = html
                details["description_text"] = text

                if "allergy warning" in text.lower():
                    details["allergy_warning"] = text.split("Allergy Warning:")[-1].split("Storage Advice")[0].strip()

                if "storage advice" in text.lower():
                    details["storage_advice"] = text.split("Storage Advice:")[-1].strip()

        return details
    # --------------------------------------------------
    # SCRAPE PRODUCTS WITH DETAILED INFO
    # --------------------------------------------------
    def scrape_products_with_details(self, collection_url, category_name="", subcategory_name=""):
        """
        Scrape products and their detailed information from product pages
        
        Args:
            collection_url: URL of the collection page
            category_name: Parent category name
            subcategory_name: Subcategory name
            
        Returns:
            list: List of product dictionaries with details
        """
        
        print(f"\n🛍️n🛍️n🛍️n🛍️n🛍️  Scraping products with details from: {collection_url}")
        # First, get basic product info from collection page
        products = self.scrape_products(collection_url, category_name, subcategory_name)
        
        # Then, fetch detailed info from each product page
        print(f"\n📋 Fetching detailed info for {len(products)} products...")
        
        for idx, product in enumerate(products):
            if product["url"] != "N/A":
                print(f"   [Details {idx+1}/{len(products)}] {product['name']}")
                product_details = self.scrape_product_details(product["url"])
                product.update(product_details)
        
        return products
    
    # --------------------------------------------------
    # SCRAPE ALL PRODUCTS FROM ALL CATEGORIES
    # --------------------------------------------------
    def scrape_all_products(self, with_details=False):
        """
        Scrape products from all categories and subcategories
        
        Args:
            with_details: If True, fetch detailed info for each product (slower)
            
        Returns:
            dict: All products organized by category
        """
        if not self.grocery_data:
            print("❌ No grocery data found. Run get_grocery_navigation() first")
            return {}
        
        all_products = {}
        
        for category in self.grocery_data["categories"]:
            category_name = category["category_name"]
            all_products[category_name] = {}
            
            for subcategory in category["subcategories"]:
                subcategory_name = subcategory["name"]
                subcategory_url = subcategory["url"]
                
                print(f"\n📂 {category_name} > {subcategory_name}")
                
                if with_details:
                    print("🔎 Scraping with detailed product info...")
                    products = self.scrape_products_with_details(
                        subcategory_url,
                        category_name,
                        subcategory_name
                    )
                else:
                    print("🔎 Scraping without detailed product info...")
                    products = self.scrape_products(
                        subcategory_url,
                        category_name,
                        subcategory_name
                    )
                
                all_products[category_name][subcategory_name] = products
        
        return all_products

    # --------------------------------------------------
    # CLEAN PRODUCTS
    # --------------------------------------------------
    def clean_all_products(self, all_products):
        """
        Clean all scraped products using IntegratedProductCleaner
        
        Args:
            all_products: List of raw product dictionaries
            
        Returns:
            list: Cleaned products following master schema
        """
        print("\n" + "=" * 70)
        print("CLEANING PRODUCTS WITH INTEGRATED CLEANER")
        print("=" * 70)
        print("   ├─ Product name cleaning")
        print("   ├─ Brand detection with auto-learning")
        print("   ├─ Field normalization")
        print("   └─ Schema enforcement")
        
        # Flatten if nested structure (category/subcategory)
        products_list = []
        if isinstance(all_products, dict):
            # Nested structure: {category: {subcategory: [products]}}
            for category, subcats in all_products.items():
                if isinstance(subcats, dict):
                    for subcat, products in subcats.items():
                        if isinstance(products, list):
                            for product in products:
                                product['category'] = category
                                product['subcategory'] = subcat
                                products_list.append(product)
                else:
                    products_list.extend(subcats if isinstance(subcats, list) else [subcats])
        else:
            products_list = all_products if isinstance(all_products, list) else [all_products]
        
        # Process through integrated cleaner
        cleaned_products = []
        for i, raw_product in enumerate(products_list, 1):
            try:
                # Clean and normalize the product
                cleaned_product = self.product_cleaner.clean_and_normalize_product(raw_product)
                
                # Add source metadata
                cleaned_product = self.product_cleaner.add_source_metadata(
                    cleaned_product,
                    source_name="Lakshmi Wholesale",
                    source_url="https://www.lakshmiwholesale.com"
                )
                
                # Enforce schema
                cleaned_product = self.product_cleaner.enforce_schema(cleaned_product)
                
                cleaned_products.append(cleaned_product)
                
                if i % 20 == 0:
                    print(f"   Processed {i}/{len(products_list)} products...")
                    
            except Exception as e:
                print(f"   ⚠️  Error processing product {i}: {e}")
                continue
        
        print(f"\n✅ Products cleaning completed: {len(cleaned_products)} cleaned")
        return cleaned_products

    # --------------------------------------------------
    # FLATTEN AND EXPORT TO CSV
    # --------------------------------------------------
    def export_to_csv(self, all_products, filename="clean_laxmi.csv"):
        """
        Export cleaned products to CSV file
        
        Args:
            all_products: Dict with structure {category: {subcategory: [products]}}
            filename: Output CSV filename
        """
        print(f"\n💾 Exporting to CSV: {filename}")
        
        # Flatten all products into a single list
        all_products_flat = []
        
        for category, subcategories in all_products.items():
            for subcategory, products in subcategories.items():
                for product in products:
                    # Flatten nested structures for CSV
                    flattened_product = {
                        'product_id': product.get('product_id', ''),
                        'name': product.get('name', ''),
                        'cleaned_name': product.get('cleaned_name', ''),
                        'price': product.get('price', ''),
                        'brand': product.get('brand', ''),
                        'category': product.get('category', ''),
                        'subcategory': product.get('subcategory', ''),
                        'volume_weight': product.get('volume_weight', ''),
                        'is_multipack': product.get('is_multipack', False),
                        'product_type': product.get('product_type', ''),
                        'url': product.get('url', ''),
                        'image_url': product.get('image_url', ''),
                        'slug': product.get('slug', ''),
                        'allergens': ', '.join(product.get('allergens', [])) if product.get('allergens') else '',
                        'certifications': ', '.join(product.get('certifications', [])) if product.get('certifications') else '',
                        'ingredients': product.get('ingredients', ''),
                        'country_of_origin': product.get('country_of_origin', ''),
                        'storage_advice': product.get('storage_advice', ''),
                        'allergy_warning': product.get('allergy_warning', ''),
                        'description': product.get('description', ''),
                    }
                    all_products_flat.append(flattened_product)
        
        if not all_products_flat:
            print("❌ No products to export")
            return
        
        # Define CSV headers
        headers = [
            'product_id', 'name', 'cleaned_name', 'price', 'brand', 'category',
            'subcategory', 'volume_weight', 'is_multipack', 'product_type', 'url',
            'image_url', 'slug', 'allergens', 'certifications', 'ingredients',
            'country_of_origin', 'storage_advice', 'allergy_warning', 'description'
        ]
        
        # Write to CSV
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(all_products_flat)
            
            print(f"✅ Successfully exported {len(all_products_flat)} products to {filename}")
        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")

    # --------------------------------------------------
    # SAVE CLEANED PRODUCTS TO JSON
    # --------------------------------------------------
    def save_cleaned_to_json(self, cleaned_products, filename="clean_laxmi.json"):
        """
        Save cleaned products to JSON file
        
        Args:
            cleaned_products: Dict with cleaned products
            filename: Output JSON filename
        """
        print(f"\n💾 Saving cleaned products to JSON: {filename}")
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(cleaned_products, f, indent=2, ensure_ascii=False)
            
            # Count total products
            total_products = sum(
                len(products)
                for subcategories in cleaned_products.values()
                for products in subcategories.values()
            )
            
            print(f"✅ Successfully saved {total_products} cleaned products to {filename}")
        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")
    
    # --------------------------------------------------
    # MAIN PIPELINE: SCRAPE, CLEAN, AND EXPORT
    # --------------------------------------------------
    def run_full_pipeline(self, with_details=True):
        """
        Run the complete pipeline: scrape → raw JSON → integrated cleaner → cleaned JSON
        
        Args:
            with_details: If True, fetch detailed info for each product
            
        Returns:
            tuple: (all_products, cleaned_products)
        """
        # Step 1: Get navigation
        print("=" * 70)
        print("STEP 1: SCRAPING NAVIGATION")
        print("=" * 70)
        data = self.get_grocery_navigation()
        
        if not data:
            print("❌ Failed to get navigation data")
            return None, None
        
        self.print_summary()
        self.save_to_json()
        
        # Step 1.5: Extract and save brands
        print("\n" + "=" * 70)
        print("STEP 1.5: EXTRACTING BRANDS")
        print("=" * 70)
        brands = self.get_brands_navigation()
        
        if brands:
            brands_file = "../data/brands.json"
            self.save_brands_to_json(brands, brands_file)
        
        # Step 2: Scrape products
        print("\n" + "=" * 70)
        print("STEP 2: SCRAPING RAW PRODUCTS")
        print("=" * 70)
        all_products = self.scrape_all_products(with_details=with_details)
        
        # ======================================================
        # PHASE 1: SAVE RAW PRODUCTS (Before cleaning)
        # ======================================================
        raw_file = "all_products.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        print(f"\n📁 Raw products saved: {raw_file}")
        
        # ======================================================
        # STEP 3: CLEAN PRODUCTS WITH INTEGRATED CLEANER
        # ======================================================
        cleaned_products = self.clean_all_products(all_products)
        
        # ======================================================
        # PHASE 2: SAVE CLEANED PRODUCTS
        # ======================================================
        self.save_cleaned_to_json(cleaned_products, "clean_laxmi.json")
        self.export_to_csv(cleaned_products, "clean_laxmi.csv")
        
        print("\n" + "=" * 70)
        print("✅ FULL PIPELINE COMPLETED")
        print("=" * 70)
        print(f"📊 Summary:")
        print(f"   Raw products: {len(all_products) if isinstance(all_products, list) else 'N/A'}")
        print(f"   Cleaned products: {len(cleaned_products)}")
        print(f"   Success rate: {len(cleaned_products)/(len(all_products) if isinstance(all_products, list) else 1)*100:.1f}%")
        
        return all_products, cleaned_products

    # --------------------------------------------------
    # PRINT SUMMARY
    # --------------------------------------------------
    def print_summary(self):
        if not self.grocery_data:
            print("❌ No data to display")
            return

        print("\n" + "=" * 70)
        print("GROCERY NAVIGATION SUMMARY".center(70))
        print("=" * 70)

        print(f"Total Categories: {self.grocery_data['total_categories']}")
        print(f"Total Subcategories: {self.grocery_data['total_subcategories']}")

        for category in self.grocery_data["categories"]:
            print(f"\n📁 {category['category_name']} "
                  f"({category['subcategory_count']})")

            for sub in category["subcategories"]:
                print(f"   ├─ {sub['name']}")
                print(f"   │  {sub['url']}")

        print("=" * 70)

    # --------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------
    def save_to_json(self, filename="grocery_navigation.json"):
        if not self.grocery_data:
            print("❌ Nothing to save")
            return

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.grocery_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved navigation to {filename}")

    def save_brands_to_json(self, brands, filename="brands.json"):
        """
        Save brands list to JSON file
        
        Args:
            brands: List of brand names
            filename: Output filename
        """
        if not brands:
            print("❌ No brands to save")
            return

        # Load existing brands if file exists
        existing_brands = []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing_brands = json.load(f)
        except FileNotFoundError:
            pass

        # Merge new brands with existing ones
        all_brands = sorted(list(set(existing_brands + brands)))
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_brands, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved {len(all_brands)} brands to {filename}")
        print(f"   ({len(brands)} new brands added)")



# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":
    scraper = LakshmiGroceryScraper()
    
    # Run the complete pipeline: scrape, clean, and export
    all_products, cleaned_products = scraper.run_full_pipeline(with_details=True)
    
    if cleaned_products:
        print("\n✅ All tasks completed successfully!")
        print("📁 Output files:")
        print("   - all_products.json (raw scraped data)")
        print("   - grocery_navigation.json (navigation structure)")
        print("   - brands.json (brands list)")
        print("   - clean_laxmi.json (cleaned products - JSON)")
        print("   - clean_laxmi.csv (cleaned products - CSV)")
    else:
        print("\n❌ Pipeline failed")