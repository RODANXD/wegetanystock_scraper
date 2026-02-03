import re
from typing import Dict, Optional, List, Tuple
import json


class BrandDetector:
    """Simple brand detector - you can expand this based on your needs"""
    
    KNOWN_BRANDS = r"C:\Users\ankun\NewdjangoEnv\Product_scraping\backend\data\brands.json"
    
    def __init__(self):
        self.known_brands = self._load_brands()
    
    def _load_brands(self):
        
        try:
            with open(self.KNOWN_BRANDS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []
    def detect_brand(self, name: str) -> Optional[str]:
        """Detect brand from product name"""
        if not name:
            return None
        
        name_upper = name.upper()
        
        for brand in self.known_brands:
            if brand.upper() in name_upper:
                return brand
        
        # If no known brand found, try to extract first word as brand
        words = name.split()
        if words:
            return words[0].title()
        
        return None


class DescriptionExtractor:
    """Extract valuable information from product descriptions"""
    
    def __init__(self):
        pass
    
    def extract_nutritional_info(self, description_text: str) -> Dict:
        """
        Extract nutritional information from description
        Returns dict with nutritional values
        """
        if not description_text:
            return {}
        
        nutrition = {}
        
        # Common nutritional patterns
        patterns = {
            'energy': r'Energy[:\s]*(\d+(?:\.\d+)?)\s*(kJ|kcal|cal)',
            'fat': r'Fat[:\s]*(\d+(?:\.\d+)?)\s*g',
            'saturates': r'(?:of which[:\s]*)?saturates[:\s]*(\d+(?:\.\d+)?)\s*g',
            'carbohydrate': r'Carbohydrate[:\s]*(\d+(?:\.\d+)?)\s*g',
            'sugars': r'(?:of which[:\s]*)?sugars[:\s]*(\d+(?:\.\d+)?)\s*g',
            'fibre': r'Fibre[:\s]*(\d+(?:\.\d+)?)\s*g',
            'protein': r'Protein[:\s]*(\d+(?:\.\d+)?)\s*g',
            'salt': r'Salt[:\s]*(\d+(?:\.\d+)?)\s*g',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, description_text, re.IGNORECASE)
            if match:
                value = match.group(1)
                unit = match.group(2) if len(match.groups()) > 1 else 'g'
                nutrition[key] = f"{value}{unit}"
        
        return nutrition if nutrition else None
    
    def extract_allergens(self, description_text: str, allergy_warning: str = "") -> List[str]:
        """Extract allergen information"""
        allergens = []
        
        # Combine both sources
        full_text = f"{description_text} {allergy_warning}".lower()
        
        # Common allergens
        allergen_patterns = [
            r'\b(nuts?|peanuts?|tree nuts?)\b',
            r'\b(milk|dairy|lactose)\b',
            r'\b(soy|soya)\b',
            r'\b(wheat|gluten)\b',
            r'\b(eggs?)\b',
            r'\b(fish)\b',
            r'\b(shellfish|crustaceans?)\b',
            r'\b(sesame)\b',
            r'\b(mustard)\b',
            r'\b(celery)\b',
            r'\b(lupin)\b',
            r'\b(sulphites?|sulfites?)\b',
        ]
        
        for pattern in allergen_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                allergens.extend(set(matches))
        
        return list(set(allergens)) if allergens else None
    
    def extract_ingredients(self, description_text: str) -> Optional[str]:
        """Extract ingredients list from description"""
        if not description_text:
            return None
        
        # Look for ingredients section
        patterns = [
            r'Ingredients?[:\s]+(.*?)(?:\n\n|\.|Storage|Allergy|Nutrition)',
            r'Contains?[:\s]+(.*?)(?:\n\n|\.|Storage|Allergy|Nutrition)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description_text, re.IGNORECASE | re.DOTALL)
            if match:
                ingredients = match.group(1).strip()
                # Clean up
                ingredients = re.sub(r'\s+', ' ', ingredients)
                return ingredients[:500]  # Limit length
        
        return None
    
    def extract_country_of_origin(self, description_text: str) -> Optional[str]:
        """Extract country of origin"""
        if not description_text:
            return None
        
        patterns = [
            r'(?:Product of|Made in|Origin[:\s]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+origin',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description_text)
            if match:
                country = match.group(1).strip()
                # Common countries
                if country.lower() in ['india', 'uk', 'usa', 'china', 'pakistan', 'sri lanka', 'bangladesh']:
                    return country
        
        return None
    
    def extract_certifications(self, description_text: str) -> List[str]:
        """Extract certifications like vegan, halal, kosher, etc."""
        if not description_text:
            return None
        
        certifications = []
        
        cert_patterns = [
            r'\b(vegan|vegetarian|halal|kosher|organic|gluten[- ]free|dairy[- ]free|nut[- ]free)\b',
        ]
        
        text_lower = description_text.lower()
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                certifications.extend(matches)
        
        return list(set(certifications)) if certifications else None


class ProductCleaner:
    """Enhanced product cleaner with description extraction"""
    
    # Patterns for price marks to remove
    PRICE_MARK_PATTERNS = [
        r'\bPMP\s*£?\s*\d+\.?\d*\b',
        r'\bPM\s*£?\s*\d+\.?\d*\b',
        r'\bP\.?M\.?\s*£?\s*\d+\.?\d*\b',
        r'\bPRICE\s*MARK(?:ED)?\s*£?\s*\d+\.?\d*\b',
        r'\b£\s*\d+\.?\d*\s*(PMP|PM)\b',
        r'\bRRP\s*£?\s*\d+\.?\d*\b',
        r'\bNOW\s*£?\s*\d+\.?\d*\b',
        r'\bWAS\s*£?\s*\d+\.?\d*\b',
        r'\bONLY\s*£?\s*\d+\.?\d*\b',
        r'\b\d+\s*FOR\s*£?\s*\d+\.?\d*\b',
        r'£\s*\d+(\.\d+)?',
        r'\b\d+\s*p\b',
    ]
    
    DESCRIPTORS_TO_REMOVE = [
        r'\b(single|singles)\b',
        r'\b(can|bottle|bar|tin|pouch|box|pack)\b',
        r'\b(new|new!|new!!)\b',
        r'\b(limited\s*edition)\b',
        r'\b(special\s*edition)\b',
    ]
    
    PACKAGING_TYPES = {
        'can': 'Can',
        'cans': 'Can',
        'bottle': 'Bottle',
        'bottles': 'Bottle',
        'btl': 'Bottle',
        'bar': 'Bar',
        'bars': 'Bar',
        'bag': 'Bag',
        'bags': 'Bag',
        'pack': 'Pack',
        'packs': 'Pack',
        'box': 'Box',
        'boxes': 'Box',
        'pouch': 'Pouch',
        'carton': 'Carton',
        'tub': 'Tub',
        'jar': 'Jar',
    }
    
    # Unit standardization mapping
    UNIT_MAPPINGS = {
        'millilitre': 'ml',
        'millilitres': 'ml',
        'milliliter': 'ml',
        'milliliters': 'ml',
        'litre': 'l',
        'litres': 'l',
        'liter': 'l',
        'liters': 'l',
        'gram': 'g',
        'grams': 'g',
        'kilogram': 'kg',
        'kilograms': 'kg',
        'kilo': 'kg',
        'kilos': 'kg',
        'fl oz': 'fl oz',
        'fluid ounce': 'fl oz',
        'fluid ounces': 'fl oz',
        'ounce': 'oz',
        'ounces': 'oz',
    }
    
    def __init__(self):
        self.brand_detector = BrandDetector()
        self.description_extractor = DescriptionExtractor()
    
    def _remove_descriptors(self, name: str) -> str:
        """Remove common descriptors from product name"""
        result = name
        for pattern in self.DESCRIPTORS_TO_REMOVE:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        return result
    
    def _remove_price_marks(self, name: str) -> str:
        """Remove price mark phrases like PM £1.79, PMP £1.25"""
        result = name
        for pattern in self.PRICE_MARK_PATTERNS:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        return result
    
    def clean_product_name(self, name: str) -> str:
        """
        Main cleaning function for product names
        Extracts core product name without sizes, barcodes, or multipack info
        """
        if not name:
            return ""
        
        name = str(name)
        cleaned = name
        
        # Remove trailing barcode numbers
        cleaned = re.sub(r'\s+\d{10,}$', '', cleaned)
        
        # Split on multipack patterns and keep first part
        parts = re.split(r'\d+\s*[×xX]\s*\d+(?:\.\d+)?\s*(?:ml|g|l|kg|cl|oz)', cleaned, flags=re.IGNORECASE)
        if len(parts) > 1:
            cleaned = parts[0]
        
        # Remove price marks
        cleaned = self._remove_price_marks(cleaned)
        
        # Remove descriptors
        cleaned = self._remove_descriptors(cleaned)
        
        # Remove size information
        cleaned = re.sub(r'\s*\d+(?:\.\d+)?\s*(?:ml|g|l|kg|cl|oz|fl\s*oz)\b', '', cleaned, flags=re.IGNORECASE)
        
        # Standardize casing
        cleaned = self.standardize_casing(cleaned)
        
        # Clean whitespace
        cleaned = self._clean_whitespace(cleaned)
        
        return cleaned
    
    def extract_volume_weight(self, name: str) -> Optional[str]:
        """
        Extract volume/weight information from product name
        Returns standardized format like '500ml' or '7x14.2g'
        """
        if not name:
            return None
        
        # Try multipack pattern first: 6x250ml, 4 x 330ml
        multipack_pattern = r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(ml|g|kg|l|oz|fl\s*oz)\b'
        match = re.search(multipack_pattern, name, re.IGNORECASE)
        if match:
            count, size, unit = match.groups()
            unit = unit.lower().replace(' ', '')
            return f"{count}x{size}{unit}"
        
        # Try single size pattern: 500ml, 1.5kg
        single_pattern = r'(\d+(?:\.\d+)?)\s*(ml|g|kg|l|oz|fl\s*oz)\b'
        match = re.search(single_pattern, name, re.IGNORECASE)
        if match:
            size, unit = match.groups()
            unit = unit.lower().replace(' ', '')
            return f"{size}{unit}"
        
        return None
    
    def determine_product_type(self, name: str, multipack_info: Optional[Dict]) -> str:
        """
        Determine if product is single or multipack
        """
        if multipack_info:
            return "multipack"
        
        # Check for pack indicators in name
        pack_indicators = [
            r'\b\d+\s*pack\b',
            r'\bpack\s*of\s*\d+\b',
            r'\b\d+\s*[xX×]\s*\d+',
            r"\b\d+'?s\b",
        ]
        
        for pattern in pack_indicators:
            if re.search(pattern, name, re.IGNORECASE):
                return "multipack"
        
        return "single"
    
    def standardize_units(self, name: str) -> str:
        """Standardize unit formats"""
        if not name:
            return ""
        
        result = name
        
        # Convert long-form units to short-form
        for long_form, short_form in self.UNIT_MAPPINGS.items():
            pattern = r'(\d+(?:\.\d+)?)\s*' + re.escape(long_form) + r'\b'
            result = re.sub(pattern, rf'\1{short_form}', result, flags=re.IGNORECASE)
        
        # Standardize spacing in units
        unit_pattern = r'(\d+(?:\.\d+)?)\s*(ml|g|kg|l|oz|fl\s*oz)\b'
        
        def standardize_unit(match):
            number = match.group(1)
            unit = match.group(2).lower().replace(' ', '')
            return f"{number}{unit}"
        
        result = re.sub(unit_pattern, standardize_unit, result, flags=re.IGNORECASE)
        
        # Handle multipack format
        multipack_pattern = r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(ml|g|kg|l)\b'
        
        def standardize_multipack(match):
            count = match.group(1)
            size = match.group(2)
            unit = match.group(3).lower()
            return f"{count}x{size}{unit}"
        
        result = re.sub(multipack_pattern, standardize_multipack, result, flags=re.IGNORECASE)
        
        return result
    
    def standardize_casing(self, name: str) -> str:
        """Standardize text casing"""
        words = name.split()
        titled_words = []
        
        lowercase_words = {'and', 'or', 'the', 'a', 'an', 'of', 'for', 'with', 'in', 'on', '&'}
        
        special_cases = {
            'ml': 'ml', 'g': 'g', 'kg': 'kg', 'l': 'l', 'oz': 'oz',
            'pk': 'pk', 'uk': 'UK', 'usa': 'USA', 'bbb': 'BBB',
        }
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            if word_lower in special_cases:
                titled_words.append(special_cases[word_lower])
            elif re.match(r'^\d+(?:\.\d+)?[a-z]+$', word_lower):
                titled_words.append(word_lower)
            elif re.match(r'^\d+x\d+[a-z]+$', word_lower):
                titled_words.append(word_lower)
            elif word_lower in lowercase_words and i > 0:
                titled_words.append(word_lower)
            else:
                titled_words.append(word.capitalize())
        
        return ' '.join(titled_words)
    
    def _clean_whitespace(self, name: str) -> str:
        """Remove extra whitespace and clean up"""
        result = re.sub(r'\s+', ' ', name)
        result = result.strip()
        result = re.sub(r'\s+([,.])', r'\1', result)
        return result
    
    def detect_multipack(self, name: str) -> Optional[Dict]:
        """
        Detect multipack information
        Returns dict with 'count', 'size', 'unit' or None
        """
        if not name:
            return None
        
        patterns = [
            r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(ml|g|l|kg)',
            r'(\d+)\s*(?:pack|pk|pck)\b',
            r'pack\s*of\s*(\d+)',
            r"(\d+)'?s\b",
            r'(\d+)\s*multi\s*pack',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) >= 3:
                    return {
                        'count': int(groups[0]),
                        'size': float(groups[1]),
                        'unit': groups[2].lower(),
                        'format': f"{groups[0]}x{groups[1]}{groups[2].lower()}"
                    }
                elif len(groups) >= 1:
                    return {
                        'count': int(groups[0]),
                        'size': None,
                        'unit': None,
                        'format': f"{groups[0]}pk"
                    }
        
        return None
    
    def generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from product name"""
        if not name:
            return ""
        
        # First clean the name
        cleaned = self.clean_product_name(name)
        
        # Convert to lowercase
        slug = cleaned.lower()
        
        # Replace '&' with 'and'
        slug = slug.replace('&', 'and')
        
        # Remove special characters
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        
        # Replace spaces with hyphens
        slug = re.sub(r'\s+', '-', slug)
        
        # Remove multiple hyphens
        slug = re.sub(r'-+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        return slug
    
    def clean_product(self, product: Dict) -> Dict:
        """
        Clean a single product and extract all valuable information
        """
        cleaned = {}
        
        # Basic fields
        original_name = product.get('name', '')
        cleaned['name'] = original_name
        cleaned['cleaned_name'] = self.clean_product_name(original_name)
        cleaned['original_name'] = original_name
        
        # Price - handle N/A and clean currency symbols
        price = product.get('price', 'N/A')
        if price and price != 'N/A':
            # Extract numeric value
            price_match = re.search(r'[\d.]+', str(price))
            if price_match:
                cleaned['price'] = float(price_match.group())
            else:
                cleaned['price'] = None
        else:
            cleaned['price'] = None
        
        # Volume/Weight
        cleaned['volume_weight'] = self.extract_volume_weight(original_name)
        
        # Multipack detection
        multipack_info = self.detect_multipack(original_name)
        cleaned['multipack'] = multipack_info
        cleaned['is_multipack'] = multipack_info is not None
        
        # Product type
        cleaned['product_type'] = self.determine_product_type(original_name, multipack_info)
        
        # Brand detection
        existing_brand = product.get('brand')
        if existing_brand and existing_brand != 'N/A':
            cleaned['brand'] = existing_brand
        else:
            detected_brand = self.brand_detector.detect_brand(original_name)
            cleaned['brand'] = detected_brand if detected_brand else None
        
        # URLs and images
        cleaned['url'] = product.get('url', '')
        cleaned['image_url'] = product.get('image', '')
        cleaned['product_id'] = product.get('product_id', '')
        
        # Category information
        cleaned['category'] = product.get('category', '')
        cleaned['subcategory'] = product.get('subcategory', '')
        
        # Slug
        cleaned['slug'] = self.generate_slug(original_name)
        
        # Extract from description
        description_text = product.get('description_text', '')
        allergy_warning = product.get('allergy_warning', '')
        storage_advice = product.get('storage_advice', '')
        
        # Nutritional information
        nutrition = self.description_extractor.extract_nutritional_info(description_text)
        if nutrition:
            cleaned['nutritional_info'] = nutrition
        
        # Allergens
        allergens = self.description_extractor.extract_allergens(description_text, allergy_warning)
        if allergens:
            cleaned['allergens'] = allergens
        
        # Storage and allergy warnings
        if allergy_warning:
            cleaned['allergy_warning'] = allergy_warning
        
        if storage_advice:
            cleaned['storage_advice'] = storage_advice
        
        # Ingredients
        ingredients = self.description_extractor.extract_ingredients(description_text)
        if ingredients:
            cleaned['ingredients'] = ingredients
        
        # Country of origin
        country = self.description_extractor.extract_country_of_origin(description_text)
        if country:
            cleaned['country_of_origin'] = country
        
        # Certifications
        certifications = self.description_extractor.extract_certifications(description_text)
        if certifications:
            cleaned['certifications'] = certifications
        
        # Keep original description for reference
        if description_text:
            cleaned['description'] = description_text[:500]  # Limit to 500 chars
        
        return cleaned
    
    def clean_products(self, products: List[Dict]) -> List[Dict]:
        """
        Clean a list of products
        Filters out products with null id or name
        """
        cleaned_products = []
        skipped_count = 0
        
        for p in products:
            # Skip products with null id or name
            if not p.get('product_id') or not p.get('name'):
                skipped_count += 1
                continue
            
            # Skip if name is 'N/A'
            if p.get('name') == 'N/A':
                skipped_count += 1
                continue
            
            cleaned_products.append(self.clean_product(p))
        
        if skipped_count > 0:
            print(f"⚠️  Skipped {skipped_count} products with null id or name")
        
        return cleaned_products
    
    def clean_all_products(self, all_products: Dict) -> Dict:
        """
        Clean all products organized by category
        
        Args:
            all_products: Dict with structure {category: {subcategory: [products]}}
            
        Returns:
            Dict with cleaned products in same structure
        """
        cleaned_all = {}
        
        for category, subcategories in all_products.items():
            cleaned_all[category] = {}
            
            for subcategory, products in subcategories.items():
                print(f"\n🧹 Cleaning {category} > {subcategory} ({len(products)} products)")
                cleaned_all[category][subcategory] = self.clean_products(products)
        
        return cleaned_all


# Export singleton instance
product_cleaner = ProductCleaner()


if __name__ == "__main__":
    # Example usage
    cleaner = ProductCleaner()
    
    # Example product
    sample_product = {
        "name": "Nescafe Cappuccino Unsweetened Taste Instant Coffee Sachets 7 x 14.2g",
        "price": "£3.99",
        "url": "https://example.com/product",
        "image": "https://example.com/image.jpg",
        "product_id": "12345",
        "category": "Beverages",
        "subcategory": "Coffee",
        "description_text": "Energy: 45kcal, Fat: 2.5g, of which saturates: 1.8g, Carbohydrate: 5g, of which sugars: 4.5g, Protein: 1.2g, Salt: 0.2g. Contains milk and soy.",
        "allergy_warning": "Contains milk and soy",
        "storage_advice": "Store in a cool, dry place"
    }
    
    cleaned = cleaner.clean_product(sample_product)
    print(json.dumps(cleaned, indent=2))