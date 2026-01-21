from DrissionPage import ChromiumPage
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Product_Scraper:
    """Scraper using cloudscraper to bypass Cloudflare"""
    
    BASE_URL = "https://www.wegetanystock.com"
    
    CATEGORY_URLS = [
        "/drinks",
        "/biscuits-snacks-sweets/cakes",
    ]
    
    def __init__(self, delay_range: tuple = (2, 5)):
        
        self.delay_range = delay_range
        self.page = None
        self.products = []
        logger.info("🚀 Initializing DrissionPage for Cloudflare bypass")
    
    def start_browser(self):
        
        if self.page is None:
            logger.info("🚀 Starting ChromiumPage browser...")
            self.page = ChromiumPage()
            logger.info("✅ Browser started successfully")
    
    def close_browser(self):
        
        if self.page:
            logger.info("🔒 Closing browser...")
            self.page.quit()
            self.page = None
    
    def random_delay(self):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(*self.delay_range)
        logger.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page using DrissionPage"""
        try:
            logger.info(f"📄 Fetching: {url}")
            
            
            if self.page is None:
                self.start_browser()
            
           
            self.page.get(url)
            logger.debug(f"Initial title: {self.page.title}")
            
            
            logger.debug("⏳ Waiting for Cloudflare bypass...")
            max_waits = 15  
            wait_count = 0
            
            while "Just a moment" in self.page.title and wait_count < max_waits:
                logger.debug(f"Waiting for Cloudflare... (attempt {wait_count + 1}/{max_waits})")
                time.sleep(3)
                wait_count += 1
            
            if "Just a moment" in self.page.title:
                logger.warning("⚠️ Still showing Cloudflare challenge after waiting")
            else:
                logger.debug(f"✅ Cloudflare bypassed. Current title: {self.page.title}")
            
          
            time.sleep(2)
            
            html_content = self.page.html
            logger.debug(f"Page HTML length: {len(html_content)} characters")
            logger.debug(f"HTML snippet (first 500 chars): {html_content[:500]}")
            
            if "Just a moment" in html_content or len(html_content) < 1000:
                logger.warning("⚠️ Page might not have loaded properly")
            
            soup = BeautifulSoup(html_content, 'lxml')
            
            
            body_tag = soup.select_one('body')
            if body_tag:
                logger.debug(f"Body tag found, content length: {len(str(body_tag))} characters")
                logger.debug(f"Body content snippet: {str(body_tag)[:300]}")
            
            logger.info(f"✅ Page loaded successfully: {self.page.title}")
            
            
            
            return soup
            
        except Exception as e:
            logger.error(f"❌ Error fetching {url}: {e}")
            return None
    
    def extract_price_from_title(self, title: str) -> Optional[str]:
        """Extract price from product title"""
        patterns = [
            r'[Pp][Mm][Pp]?\s*£(\d+\.?\d*)',
            r'£(\d+\.?\d*)\s*[Pp][Mm][Pp]?',
            r'[Pp]\.?[Mm]\.?\s*£(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return f"£{match.group(1)}"
        return None
    
    def extract_volume_weight(self, title: str) -> Optional[str]:
        """Extract volume or weight from title"""
        patterns = [
            r'(\d+\s*x\s*\d+(?:\.\d+)?\s*(?:ml|g|l|kg))',
            r'(\d+(?:\.\d+)?\s*(?:ml|l|litre|liter)s?)',
            r'(\d+(?:\.\d+)?\s*(?:g|kg|gram|kilogram)s?)',
            r'(\d+\s*(?:pk|pack))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def detect_product_type(self, title: str) -> str:
        """Detect product type from title"""
        title_lower = title.lower()
        
        if re.search(r'\bp\.?m\.?p?\b', title_lower) or re.search(r'pm\s*£|pmp\s*£|£\d+\.?\d*\s*pm', title_lower):
            return "price_marked"
        
        if re.search(r'\d+\s*x\s*\d+', title_lower) or re.search(r'\d+\s*(?:pk|pack)\b', title_lower):
            return "multipack"
        
        return "regular"
    
    def extract_product_data(self, product_element) -> Optional[Dict]:
        """Extract data from a product element"""
        try:
            product = {}
            logger.debug(f"Extracting product from element: {product_element.name}")
            
            
            name_selectors = [
                '.card__heading a',
                '.product-card__title',
                '.product-title a',
                'h3 a',
                'h2 a',
                '.card__heading',
                'a.full-unstyled-link',
            ]
            
            name = None
            for selector in name_selectors:
                try:
                    name_elem = product_element.select_one(selector)
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        logger.debug(f"Found name with '{selector}': {name[:50]}")
                        if name and len(name) > 3:
                            break
                except Exception as e:
                    logger.debug(f"Error with selector '{selector}': {e}")
                    continue
            
            if not name:
                logger.debug("Trying fallback: searching all links")
                
                links = product_element.select('a')
                logger.debug(f"Found {len(links)} links in element")
                for i, link in enumerate(links):
                    text = link.get_text(strip=True)
                    logger.debug(f"Link {i}: {text[:50]}")
                    if text and len(text) > 5:
                        name = text
                        logger.debug(f"Selected fallback name: {name[:50]}")
                        break
            
            if not name:
                logger.debug("No product name found, skipping element")
                return None
            
            product['name'] = name
            product['price'] = self.extract_price_from_title(name)
            product['volume_weight'] = self.extract_volume_weight(name)
            product['product_type'] = self.detect_product_type(name)
            
            # Extract image
            img_selectors = [
                'img.motion-reduce',
                '.card__media img',
                'img[src*="cdn.shopify"]',
                'img',
            ]
            
            for selector in img_selectors:
                img_elem = product_element.select_one(selector)
                if img_elem:
                    img_url = img_elem.get('src') or img_elem.get('data-src')
                    if not img_url:
                        srcset = img_elem.get('srcset')
                        if srcset:
                            img_url = srcset.split(',')[0].split()[0]
                    
                    if img_url:
                        if img_url.startswith('//'):
                            img_url = 'https:' + img_url
                        product['image_url'] = img_url
                        break
            
            
            link_elem = product_element.select_one('a[href*="/products/"]')
            if link_elem:
                product['url'] = urljoin(self.BASE_URL, link_elem.get('href'))
            
            return product
            
        except Exception as e:
            logger.error(f"Error extracting product: {e}")
            return None
    
    def scrape_category(self, category_url: str, max_products: int = 50) -> List[Dict]:
        """Scrape products from a category"""
        products = []
        page = 1
        
        while len(products) < max_products:
            # Build page URL
            if '?' in category_url:
                url = f"{self.BASE_URL}{category_url}&page={page}"
            else:
                url = f"{self.BASE_URL}{category_url}?page={page}"
            
            soup = self.fetch_page(url)
            if not soup:
                break
            
            
            
           
            product_selectors = [
                ('article[class*="text-gray"]', 'article with text-gray class'),  
                ('article', 'all article tags'),  
                ('div[class*="product-card"]', 'product-card divs'),
                ('.grid-item', 'grid-item class'),
                ('div[class*="col"]', 'column divs'),
                ('a.full-unstyled-link', 'full-unstyled-link anchors'),
            ]
            product_elements = []
            selected_selector = None
            
            for selector, desc in product_selectors:
                test_elements = soup.select(selector)
                logger.debug(f"Testing '{desc}' ({selector}): {len(test_elements)} elements")
                
                if 'article' in selector and 2 <= len(test_elements) <= 1000:
                    product_elements = test_elements
                    selected_selector = (selector, desc)
                    logger.info(f"✓ Using {len(test_elements)} {desc}")
                    break
                
                
                if len(test_elements) > 0:
                    valid_elements = []
                    for elem in test_elements:
                        text = elem.get_text(strip=True)
                        
                        if any(x in text.lower() for x in ['£', 'ml', 'g', 'kg', 'buy', 'basket']) or len(text) > 50:
                            valid_elements.append(elem)

                    if len(valid_elements) >= 2:  
                        product_elements = valid_elements
                        selected_selector = (selector, desc)
                        logger.info(f"✓ Found {len(valid_elements)} products with: {desc}")
                        break
            
            if not product_elements:
                logger.warning(f"No products found on page {page}")
                logger.info("📝 Hint: Website structure may have changed. Check HTML manually.")
                break
            
            logger.info(f"Using selector: {selected_selector[1]} ({selected_selector[0]})")
            
            new_count = 0
            for elem in product_elements:
                if len(products) >= max_products:
                    break
                
                product_data = self.extract_product_data(elem)
                if product_data and product_data.get('name'):
                    products.append(product_data)
                    new_count += 1
                    logger.info(f"  ✓ {product_data['name'][:50]}...")
            
            logger.info(f"Page {page}: Added {new_count} products (Total: {len(products)})")
            
            if new_count == 0:
                break
            
            page += 1
            self.random_delay()
            
            if page > 10:  
                break
        
        return products
    
    def scrape_all(self, target_count: int = 100) -> List[Dict]:
        """Scrape products from all categories"""
        all_products = []
        seen_names = set()
        
        try:
            # Start browser
            self.start_browser()
            
            
            logger.info("🏠 Visiting homepage first...")
            self.fetch_page(self.BASE_URL)
            self.random_delay()
            
            for category_url in self.CATEGORY_URLS:
                if len(all_products) >= target_count:
                    break
                
                logger.info(f"\n📁 Category: {category_url}")
                logger.info("-" * 40)
                
                remaining = target_count - len(all_products)
                products = self.scrape_category(category_url, max_products=remaining + 20)
                
                for product in products:
                    name_key = product.get('name', '').lower().strip()
                    if name_key and name_key not in seen_names:
                        seen_names.add(name_key)
                        all_products.append(product)
                    
                    if len(all_products) >= target_count:
                        break
                
                logger.info(f"Total so far: {len(all_products)}")
                self.random_delay()
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        
        finally:
            self.close_browser()
        
        logger.info(f"\n✅ Scraping complete! Total: {len(all_products)} products")
        return all_products
    
    def save_to_json(self, products: List[Dict], filepath: str):
        """Save products to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(products)} products to {filepath}")


def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("🕷️  WeGetAnyStock Scraper (Cloudflare Bypass)")
    print("=" * 60 + "\n")
    
    
    scraper = Product_Scraper(
        delay_range=(3, 6)  # Random delay between requests
    )
    
  
    products = scraper.scrape_all(target_count=100)
    
    if products:
        
        output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_products.json')
        scraper.save_to_json(products, output_path)
        
       
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"Total Products: {len(products)}")
        
        
        types = {}
        for p in products:
            t = p.get('product_type', 'unknown')
            types[t] = types.get(t, 0) + 1
        
        print("\nBy Type:")
        for t, count in types.items():
            print(f"  - {t}: {count}")
        
        print("\n📋 Sample Products:")
        for p in products[:5]:
            print(f"  • {p.get('name', 'N/A')[:60]}...")
    else:
        print("❌ No products scraped!")
    
    return products


if __name__ == "__main__":
    main()