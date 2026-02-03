import re
from typing import Dict, Optional, List, Tuple
from .brand_detector import BrandDetector


class ProductCleaner:
    
    # Patterns for price marks to remove
    PRICE_MARK_PATTERNS = [
    r'\bPMP\s*£?\s*\d+\.?\d*\b',        # PMP / Pmp £1.25
    r'\bPM\s*£?\s*\d+\.?\d*\b',         # PM £1.79
    r'\bP\.?M\.?\s*£?\s*\d+\.?\d*\b',   # P.M. £1.00
    r'\bPRICE\s*MARK(?:ED)?\s*£?\s*\d+\.?\d*\b',
    r'\b£\s*\d+\.?\d*\s*(PMP|PM)\b',    # £1.25 PMP / PM
    r'\bRRP\s*£?\s*\d+\.?\d*\b',
    r'\bNOW\s*£?\s*\d+\.?\d*\b',
    r'\bWAS\s*£?\s*\d+\.?\d*\b',
    r'\bONLY\s*£?\s*\d+\.?\d*\b',
    r'\b\d+\s*FOR\s*£?\s*\d+\.?\d*\b',  # 2 FOR £1.00
    r'£\s*\d+(\.\d+)?',                 # £1.65
    r'\b\d+\s*p\b',                     # 75p
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
        # Volume
        'millilitre': 'ml',
        'millilitres': 'ml',
        'milliliter': 'ml',
        'milliliters': 'ml',
        'litre': 'l',
        'litres': 'l',
        'liter': 'l',
        'liters': 'l',
        # Weight
        'gram': 'g',
        'grams': 'g',
        'kilogram': 'kg',
        'kilograms': 'kg',
        'kilo': 'kg',
        'kilos': 'kg',
        # Fluid ounces
        'fl oz': 'fl oz',
        'fluid ounce': 'fl oz',
        'fluid ounces': 'fl oz',
        # Ounces
        'ounce': 'oz',
        'ounces': 'oz',
    }
    
    def __init__(self):
        self.brand_detector = BrandDetector()
    
    
    # remove product where id = null
    
    
    def _remove_descriptors(self, name: str) -> str:
        result = name
        for pattern in self.DESCRIPTORS_TO_REMOVE:
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
        cleaned = re.sub(r'\s+\d{10,}$', '', cleaned)
        parts = re.split(r'\d+\s*[×xX]\s*\d+(?:\.\d+)?\s*(?:ml|g|l|kg|cl|oz)', cleaned, flags=re.IGNORECASE)
        if len(parts) > 1:
            cleaned = parts[0]
        cleaned = self._remove_price_marks(cleaned)
        cleaned = self._remove_descriptors(cleaned)
        cleaned = re.sub(r'\s*\d+(?:\.\d+)?\s*(?:ml|g|l|kg|cl|oz|fl\s*oz)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = self.standardize_casing(cleaned)
        cleaned = self._clean_whitespace(cleaned)
        
        return cleaned
    
    def _remove_price_marks(self, name: str) -> str:
        """Remove price mark phrases like PM £1.79, PMP £1.25"""
        result = name
        
        for pattern in self.PRICE_MARK_PATTERNS:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        
        return result
    
    def standardize_units(self, name: str) -> str:
        if not name:
            return ""
        name = str(name)
        result = name
        
        
        for long_form, short_form in self.UNIT_MAPPINGS.items():
            pattern = r'(\d+(?:\.\d+)?)\s*' + re.escape(long_form) + r'\b'
            result = re.sub(pattern, rf'\1{short_form}', result, flags=re.IGNORECASE)
        
        
        unit_pattern = r'(\d+(?:\.\d+)?)\s*(ml|g|kg|l|oz|fl\s*oz)\b'
        
        def standardize_unit(match):
            number = match.group(1)
            unit = match.group(2).lower().replace(' ', '')
            
            
            
            return f"{number}{unit}"
        
        result = re.sub(unit_pattern, standardize_unit, result, flags=re.IGNORECASE)
        
        # Handle multipack format: 6x250ml, 4 x 330ml
        multipack_pattern = r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(ml|g|kg|l)\b'
        
        def standardize_multipack(match):
            count = match.group(1)
            size = match.group(2)
            unit = match.group(3).lower()
            return f"{count}x{size}{unit}"
        
        result = re.sub(multipack_pattern, standardize_multipack, result, flags=re.IGNORECASE)
        
        return result
    
    def standardize_casing(self, name: str) -> str:
       
        words = name.split()
        titled_words = []
        
       
        lowercase_words = {'and', 'or', 'the', 'a', 'an', 'of', 'for', 'with', 'in', 'on', '&'}
        
        
        special_cases = {
            'ml': 'ml',
            'g': 'g',
            'kg': 'kg',
            'l': 'l',
            'oz': 'oz',
            'pk': 'pk',
            'uk': 'UK',
            'usa': 'USA',
            'bbb': 'BBB',
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
            return ""
        name = str(name)
        patterns = [
            # 6x250ml, 4x330ml
            r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(ml|g|l|kg)',
            # 6 pack, 4 pack
            r'(\d+)\s*(?:pack|pk|pck)\b',
            # Pack of 6
            r'pack\s*of\s*(\d+)',
            # 6's
            r"(\d+)'?s\b",
            # Multipack
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
       
        if not name:
            return ""
        name = str(name)
        
        # First clean the name
        cleaned = self.clean_product_name(name)
        
        # Convert to lowercase
        slug = cleaned.lower()
        
        # Replace '&' with 'and'
        slug = slug.replace('&', 'and')
        
        # Remove special characters except alphanumeric, spaces, and hyphens
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        
        # Replace spaces with hyphens
        slug = re.sub(r'\s+', '-', slug)
        
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        return slug
    
    def clean_product(self, product: Dict) -> Dict:
        
        cleaned = product.copy()
        original_name = product.get('name', '')
        
        # Clean the name
        cleaned['cleaned_name'] = self.clean_product_name(original_name)
        cleaned['original_name'] = original_name
        
        #existing brand from scraped data, only detect missing data
        existing_brand = product.get('brand')
        if existing_brand:
            cleaned['brand'] = existing_brand
        else:
            detected_brand = self.brand_detector.detect_brand(original_name)
            cleaned['brand'] = detected_brand if detected_brand else None
        
        
        # Detect multipack
        multipack_info = self.detect_multipack(original_name)
        cleaned['multipack'] = multipack_info
        cleaned['is_multipack'] = multipack_info is not None
        
        # Generate slug
        cleaned['slug'] = self.generate_slug(original_name)
        
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
            if not p.get('id') or not p.get('name'):
                skipped_count += 1
                continue
            
            cleaned_products.append(self.clean_product(p))
        
        if skipped_count > 0:
            print(f"⚠️  Skipped {skipped_count} products with null id or name")
        
        return cleaned_products


# Export singleton instance
product_cleaner = ProductCleaner()


if __name__ == "__main__":
    
    cleaner = ProductCleaner()
    
    
 