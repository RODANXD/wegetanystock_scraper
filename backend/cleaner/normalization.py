# normalization.py
"""
Enhanced Normalization Engine: Clean and standardize all product fields
Integrates product name cleaning, unit standardization, and type enforcement
"""

import re
from typing import Any, List, Optional, Union, Dict
from datetime import datetime


class NormalizationEngine:
    """
    Handles data cleaning, standardization, and type enforcement.
    Includes specialized logic for product names, prices, and measurements.
    """
    
    # Price mark patterns to remove from product names
    PRICE_MARK_PATTERNS = [
        r'\bPMP\s*£?\s*\d+\.?\d*\b',        # PMP £1.25
        r'\bPM\s*£?\s*\d+\.?\d*\b',         # PM £1.79
        r'\bP\.?M\.?\s*£?\s*\d+\.?\d*\b',   # P.M. £1.00
        r'\bPRICE\s*MARK(?:ED)?\s*£?\s*\d+\.?\d*\b',
        r'\b£\s*\d+\.?\d*\s*(PMP|PM)\b',    # £1.25 PMP
        r'\bRRP\s*£?\s*\d+\.?\d*\b',
        r'\bNOW\s*£?\s*\d+\.?\d*\b',
        r'\bWAS\s*£?\s*\d+\.?\d*\b',
        r'\bONLY\s*£?\s*\d+\.?\d*\b',
        r'\b\d+\s*FOR\s*£?\s*\d+\.?\d*\b',  # 2 FOR £1.00
        r'£\s*\d+(\.\d+)?',                 # £1.65
        r'\b\d+\s*p\b',                     # 75p
    ]
    
    # Generic descriptors to remove from product names
    DESCRIPTORS_TO_REMOVE = [
        r'\b(single|singles)\b',
        r'\b(new|new!|new!!)\b',
        r'\b(limited\s*edition)\b',
        r'\b(special\s*edition)\b',
    ]
    
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
        # Centiliters
        'centilitre': 'cl',
        'centilitres': 'cl',
        'centiliter': 'cl',
        'centiliters': 'cl',
    }
    
    # Packaging types
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
        'sachet': 'Sachet',
        'tin': 'Tin',
    }
    
    def __init__(self):
        self.category_mappings = self._load_category_mappings()
    
    def _load_category_mappings(self):
        """Define standard category names and their variations."""
        return {
            'Beverages': ['beverage', 'beverages', 'drinks', 'drink', 'soft drinks'],
            'Dairy': ['dairy', 'dairy products'],
            'Snacks': ['snacks', 'snack', 'snack food', 'crisps'],
            'Bakery': ['bakery', 'baked goods', 'bread'],
            'Canned Goods': ['canned', 'canned goods', 'canned food', 'tinned'],
            'Frozen Foods': ['frozen', 'frozen food', 'frozen foods'],
            'Meat & Seafood': ['meat', 'seafood', 'fish', 'poultry'],
            'Produce': ['produce', 'fruits', 'vegetables', 'fresh'],
            'Condiments': ['condiments', 'sauces', 'dressings'],
            'Cereals': ['cereal', 'cereals', 'breakfast'],
            'Pantry': ['pantry', 'dry goods'],
            'Confectionery': ['sweets', 'candy', 'chocolate', 'confectionery'],
            'Coffee & Tea': ['coffee', 'tea', 'hot beverages'],
        }
    
    # ========== PRODUCT NAME CLEANING ==========
    
    def clean_product_name(self, name: str) -> str:
        """
        Main cleaning function for product names
        Removes sizes, barcodes, multipack info, price marks
        Returns clean product title
        """
        if not name:
            return ""
        
        name = str(name)
        cleaned = name
        
        # Remove trailing barcode (10+ digits)
        cleaned = re.sub(r'\s+\d{10,}$', '', cleaned)
        
        # Remove multipack size info (e.g., "6x330ml")
        parts = re.split(r'\d+\s*[×xX]\s*\d+(?:\.\d+)?\s*(?:ml|g|l|kg|cl|oz)', cleaned, flags=re.IGNORECASE)
        if len(parts) > 1:
            cleaned = parts[0]
        
        # Remove price marks
        cleaned = self._remove_price_marks(cleaned)
        
        # Remove generic descriptors
        cleaned = self._remove_descriptors(cleaned)
        
        # Remove unit measurements (but keep in Package Size field)
        cleaned = re.sub(r'\s*\d+(?:\.\d+)?\s*(?:ml|g|l|kg|cl|oz|fl\s*oz)\b', '', cleaned, flags=re.IGNORECASE)
        
        # Standardize casing
        cleaned = self.standardize_casing(cleaned)
        
        # Clean whitespace
        cleaned = self._clean_whitespace(cleaned)
        
        return cleaned
    
    def _remove_price_marks(self, name: str) -> str:
        """Remove price mark phrases like PM £1.79, PMP £1.25"""
        result = name
        for pattern in self.PRICE_MARK_PATTERNS:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        return result
    
    def _remove_descriptors(self, name: str) -> str:
        """Remove generic descriptors"""
        result = name
        for pattern in self.DESCRIPTORS_TO_REMOVE:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)
        return result
    
    def standardize_casing(self, name: str) -> str:
        """
        Standardize text casing to Title Case with exceptions
        """
        words = name.split()
        titled_words = []
        
        # Words that should stay lowercase (unless first word)
        lowercase_words = {'and', 'or', 'the', 'a', 'an', 'of', 'for', 'with', 'in', 'on', '&'}
        
        # Special cases that should stay as-is
        special_cases = {
            'ml': 'ml', 'g': 'g', 'kg': 'kg', 'l': 'l', 'oz': 'oz', 'cl': 'cl',
            'pk': 'pk', 'uk': 'UK', 'usa': 'USA', 'bbb': 'BBB',
        }
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            # Check special cases first
            if word_lower in special_cases:
                titled_words.append(special_cases[word_lower])
            # Keep measurements lowercase (e.g., "250ml")
            elif re.match(r'^\d+(?:\.\d+)?[a-z]+$', word_lower):
                titled_words.append(word_lower)
            # Keep multipack format lowercase (e.g., "6x330ml")
            elif re.match(r'^\d+x\d+[a-z]+$', word_lower):
                titled_words.append(word_lower)
            # Lowercase conjunctions (but not if first word)
            elif word_lower in lowercase_words and i > 0:
                titled_words.append(word_lower)
            # Default: capitalize
            else:
                titled_words.append(word.capitalize())
        
        return ' '.join(titled_words)
    
    def _clean_whitespace(self, name: str) -> str:
        """Remove extra whitespace and clean up"""
        # Replace multiple spaces with single space
        result = re.sub(r'\s+', ' ', name)
        # Remove leading/trailing whitespace
        result = result.strip()
        # Remove space before punctuation
        result = re.sub(r'\s+([,.])', r'\1', result)
        return result
    
    # ========== UNIT STANDARDIZATION ==========
    
    def standardize_units(self, text: str) -> str:
        """
        Standardize all unit measurements in text
        Examples: "500 millilitres" → "500ml", "2 kilograms" → "2kg"
        """
        if not text:
            return ""
        
        text = str(text)
        result = text
        
        # Convert long-form units to short-form
        for long_form, short_form in self.UNIT_MAPPINGS.items():
            pattern = r'(\d+(?:\.\d+)?)\s*' + re.escape(long_form) + r'\b'
            result = re.sub(pattern, rf'\1{short_form}', result, flags=re.IGNORECASE)
        
        # Standardize existing short-form units (remove spaces)
        unit_pattern = r'(\d+(?:\.\d+)?)\s*(ml|g|kg|l|oz|cl|fl\s*oz)\b'
        
        def standardize_unit(match):
            number = match.group(1)
            unit = match.group(2).lower().replace(' ', '')
            return f"{number}{unit}"
        
        result = re.sub(unit_pattern, standardize_unit, result, flags=re.IGNORECASE)
        
        # Handle multipack format: 6x250ml, 4 x 330ml
        multipack_pattern = r'(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)\s*(ml|g|kg|l|cl|oz)\b'
        
        def standardize_multipack(match):
            count = match.group(1)
            size = match.group(2)
            unit = match.group(3).lower()
            return f"{count}x{size}{unit}"
        
        result = re.sub(multipack_pattern, standardize_multipack, result, flags=re.IGNORECASE)
        
        return result
    
    def extract_volume_weight(self, text: str) -> Optional[Dict]:
        """
        Extract volume or weight from text
        Returns dict with 'value', 'unit', 'type' (volume/weight)
        """
        if not text:
            return None
        
        # Standardize first
        standardized = self.standardize_units(text)
        
        # Volume units
        volume_pattern = r'(\d+(?:\.\d+)?)(ml|l|cl|fl\s*oz)\b'
        match = re.search(volume_pattern, standardized, re.IGNORECASE)
        if match:
            return {
                'value': float(match.group(1)),
                'unit': match.group(2).lower().replace(' ', ''),
                'type': 'volume'
            }
        
        # Weight units
        weight_pattern = r'(\d+(?:\.\d+)?)(g|kg|oz)\b'
        match = re.search(weight_pattern, standardized, re.IGNORECASE)
        if match:
            return {
                'value': float(match.group(1)),
                'unit': match.group(2).lower(),
                'type': 'weight'
            }
        
        return None
    
    def detect_packaging_type(self, text: str) -> Optional[str]:
        """
        Detect packaging type from text
        Returns standardized packaging type or None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        for variant, standard in self.PACKAGING_TYPES.items():
            if re.search(r'\b' + variant + r'\b', text_lower):
                return standard
        
        return None
    
    # ========== STANDARD NORMALIZATION ==========
    
    def normalize_text(self, value: Any) -> Optional[str]:
        """Normalize text fields: trim, clean whitespace."""
        if value is None or value == '':
            return None
        
        # Convert to string
        text = str(value).strip()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove null-like values
        if text.lower() in ['null', 'none', 'n/a', 'na', '-', '']:
            return None
        
        return text if text else None
    
    def normalize_number(self, value: Any) -> Optional[float]:
        """Normalize numeric fields: extract numbers, handle units."""
        if value is None or value == '':
            return None
        
        # If already a number
        if isinstance(value, (int, float)):
            return float(value)
        
        # Convert to string and clean
        text = str(value).strip().lower()
        
        # Handle null-like values
        if text in ['null', 'none', 'n/a', 'na', '-', '']:
            return None
        
        # Remove currency symbols and commas
        text = text.replace('£', '').replace('$', '').replace(',', '')
        
        # Extract first number found
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        return None
    
    def normalize_boolean(self, value: Any) -> Optional[bool]:
        """Normalize boolean fields."""
        if value is None or value == '':
            return None
        
        if isinstance(value, bool):
            return value
        
        text = str(value).strip().lower()
        
        # True values
        if text in ['true', 'yes', 'y', '1', 'on']:
            return True
        
        # False values
        if text in ['false', 'no', 'n', '0', 'off']:
            return False
        
        # Null values
        if text in ['null', 'none', 'n/a', 'na', '-', '']:
            return None
        
        return None
    
    def normalize_list(self, value: Any) -> Optional[List[str]]:
        """Normalize list/array fields."""
        if value is None or value == '':
            return None
        
        # Already a list
        if isinstance(value, list):
            # Clean each item
            cleaned = [self.normalize_text(item) for item in value]
            cleaned = [item for item in cleaned if item]  # Remove nulls
            return cleaned if cleaned else None
        
        # String that might be comma-separated
        text = str(value).strip()
        if text.lower() in ['null', 'none', 'n/a', 'na', '-', '']:
            return None
        
        # Split by comma or semicolon
        items = re.split(r'[,;]', text)
        cleaned = [self.normalize_text(item) for item in items]
        cleaned = [item for item in cleaned if item]
        
        return cleaned if cleaned else None
    
    def normalize_url(self, value: Any) -> Optional[str]:
        """Normalize URL fields."""
        url = self.normalize_text(value)
        if not url:
            return None
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://', '//')):
            # Assume https if no protocol
            url = 'https://' + url
        
        return url
    
    def normalize_category(self, value: Any) -> Optional[str]:
        """Normalize category names to standard values."""
        category = self.normalize_text(value)
        if not category:
            return None
        
        category_lower = category.lower()
        
        # Map to standard category
        for standard_cat, variations in self.category_mappings.items():
            if category_lower in variations:
                return standard_cat
        
        # Return title cased original if no mapping
        return self.standardize_casing(category)
    
    def normalize_price(self, value: Any) -> Optional[float]:
        """Normalize price values (remove currency, convert to float)"""
        if value is None or value == '':
            return None
        
        # Handle 'N/A' and similar
        if str(value).upper() in ['N/A', 'NA', 'NONE', 'NULL']:
            return None
        
        # Use number normalization (handles currency removal)
        return self.normalize_number(value)
    
    def normalize_weight(self, value: Any) -> Optional[float]:
        """Normalize weight values (convert to grams)"""
        if value is None or value == '':
            return None
        
        text = str(value).strip().lower()
        
        # Extract number and unit
        match = re.search(r'(\d+\.?\d*)\s*(g|kg|oz|lb|mg)?', text)
        if not match:
            return None
        
        number = float(match.group(1))
        unit = match.group(2) if match.group(2) else 'g'
        
        # Convert to grams
        conversions = {
            'g': 1,
            'kg': 1000,
            'mg': 0.001,
            'oz': 28.3495,
            'lb': 453.592,
        }
        
        return number * conversions.get(unit, 1)
    
    def normalize_volume(self, value: Any) -> Optional[float]:
        """Normalize volume values (convert to ml)"""
        if value is None or value == '':
            return None
        
        text = str(value).strip().lower()
        
        # Extract number and unit
        match = re.search(r'(\d+\.?\d*)\s*(ml|l|cl|fl oz|gal)?', text)
        if not match:
            return None
        
        number = float(match.group(1))
        unit = match.group(2) if match.group(2) else 'ml'
        
        # Convert to ml
        conversions = {
            'ml': 1,
            'l': 1000,
            'cl': 10,
            'fl oz': 29.5735,
            'gal': 3785.41,
        }
        
        return number * conversions.get(unit, 1)
    
    def generate_slug(self, name: str) -> str:
        """
        Generate URL-friendly slug from product name
        """
        if not name:
            return ""
        
        # First clean the name
        cleaned = self.clean_product_name(name)
        
        # Convert to lowercase
        slug = cleaned.lower()
        
        # Replace '&' with 'and'
        slug = slug.replace('&', 'and')
        
        # Remove special characters except alphanumeric, spaces, hyphens
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        
        # Replace spaces with hyphens
        slug = re.sub(r'\s+', '-', slug)
        
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        return slug