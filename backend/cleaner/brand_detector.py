# brand_detector.py
"""
Brand Detection System with Auto-Learning
Detects brands from product names and maintains a JSON database of known brands
"""

import json
import os
import re
from typing import Optional, List, Dict
from pathlib import Path


class BrandDetector:
    """
    Detects brand names from product titles using a JSON configuration file.
    Automatically learns new brands and saves them back to the JSON file.
    """
    
    def __init__(self, brands_file: Optional[str] = None, auto_save: bool = True):
        """
        Initialize BrandDetector with brands from JSON file
        
        Args:
            brands_file: Path to brands.json file. If None, uses default path.
            auto_save: If True, automatically saves new brands to JSON file
        """
        if brands_file is None:
            # Construct path relative to this file's directory
            current_dir = Path(__file__).parent
            brands_file = current_dir / 'data' / 'brands.json'
        
        self.brands_file = Path(brands_file)
        self.auto_save = auto_save
        
        # Ensure data directory exists
        self.brands_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load brands and mappings
        self.brands_data = self._load_brands_file()
        self.brands = self.brands_data.get('brands', [])
        self.brand_mapping = self.brands_data.get('brand_mapping', {})
        
        # Sort brands by length (longest first) for better matching
        self.brands = sorted(set(self.brands), key=len, reverse=True)
        
        # Track if we've made changes that need saving
        self._dirty = False

    def _load_brands_file(self) -> Dict:
        """Load complete brands data from JSON file"""
        try:
            if not self.brands_file.exists():
                print(f"⚠️  Brands file not found: {self.brands_file}")
                print(f"   Creating new brands file...")
                return {'brands': [], 'brand_mapping': {}}

            with open(self.brands_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Ensure proper structure
                if isinstance(data, list):
                    # Old format - just list of brands
                    return {'brands': data, 'brand_mapping': {}}
                elif isinstance(data, dict):
                    return {
                        'brands': data.get('brands', []),
                        'brand_mapping': data.get('brand_mapping', {})
                    }
                else:
                    print(f"⚠️  Invalid brands format in {self.brands_file}")
                    return {'brands': [], 'brand_mapping': {}}
                    
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Error loading brands from {self.brands_file}: {e}")
            return {'brands': [], 'brand_mapping': {}}

    def _save_brands(self):
        """Save brands and mapping back to JSON file"""
        if not self.auto_save:
            return
        
        try:
            # Sort brands alphabetically before saving
            sorted_brands = sorted(set(self.brands))
            
            # Sort mapping by key
            sorted_mapping = dict(sorted(self.brand_mapping.items()))
            
            data = {
                'brands': sorted_brands,
                'brand_mapping': sorted_mapping
            }
            
            with open(self.brands_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self._dirty = False
            print(f"✓ Saved {len(sorted_brands)} brands to {self.brands_file}")
            
        except IOError as e:
            print(f"⚠️  Error saving brands to {self.brands_file}: {e}")

    def detect_brand(self, product_name: str) -> Optional[str]:
        """
        Detect brand name from product name
        Returns the canonical brand name or None
        """
        if not product_name:
            return None

        name_lower = product_name.lower()
        
        # First, check the mapping for known variations
        for variation, canonical in self.brand_mapping.items():
            if variation.lower() in name_lower:
                return canonical
        
        # Then, check against all brands (using word boundaries for accuracy)
        for brand in self.brands:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(brand) + r'\b'
            if re.search(pattern, product_name, re.IGNORECASE):
                return brand

        return None
    
    def detect_all_brands(self, product_name: str) -> List[str]:
        """
        Detect all brand names in a product name
        Useful for products that mention multiple brands
        """
        if not product_name:
            return []
        
        found_brands = []
        
        for brand in self.brands:
            pattern = r'\b' + re.escape(brand) + r'\b'
            if re.search(pattern, product_name, re.IGNORECASE):
                # Normalize to canonical name
                canonical = self.brand_mapping.get(brand.lower(), brand)
                if canonical not in found_brands:
                    found_brands.append(canonical)
        
        return found_brands
    
    def extract_brand_and_product(self, product_name: str) -> tuple[Optional[str], str]:
        """
        Extract brand and remaining product description
        Returns (brand, remaining_name)
        """
        brand = self.detect_brand(product_name)
        
        if brand:
            # Remove brand from product name
            pattern = r'\b' + re.escape(brand) + r'\b\s*'
            remaining = re.sub(pattern, '', product_name, flags=re.IGNORECASE).strip()
            return brand, remaining
        
        return None, product_name
    
    def add_brand(self, brand: str, canonical: Optional[str] = None) -> bool:
        """
        Manually add a new brand to the database
        
        Args:
            brand: The brand name to add
            canonical: If this is a variation, the canonical brand name
        
        Returns:
            True if brand was added, False if it already exists
        """
        if not brand:
            return False
        
        brand = brand.strip()
        
        if canonical:
            # This is a variation - add to mapping
            canonical = canonical.strip()
            if brand.lower() not in self.brand_mapping:
                self.brand_mapping[brand.lower()] = canonical
                # Ensure canonical is in brands list
                if canonical not in self.brands:
                    self.brands.append(canonical)
                self._dirty = True
                return True
        else:
            # This is a main brand
            if brand not in self.brands:
                self.brands.append(brand)
                # Re-sort by length
                self.brands = sorted(set(self.brands), key=len, reverse=True)
                self._dirty = True
                return True
        
        return False
    
    def learn_brand(self, product_name: str, confirmed_brand: str) -> bool:
        """
        Learn a brand from a confirmed example
        This is used when you know the correct brand for a product
        
        Args:
            product_name: The product name
            confirmed_brand: The correct brand name
        
        Returns:
            True if brand was learned (new), False if already known
        """
        result = self.add_brand(confirmed_brand)
        
        if result and self.auto_save:
            self._save_brands()
        
        return result
    
    def add_brand_variation(self, variation: str, canonical_brand: str):
        """
        Add a brand name variation
        
        Example:
            add_brand_variation("Coca Cola", "Coca-Cola")
            add_brand_variation("Coke", "Coca-Cola")
        """
        if variation and canonical_brand:
            self.brand_mapping[variation.lower()] = canonical_brand
            if canonical_brand not in self.brands:
                self.brands.append(canonical_brand)
                self.brands = sorted(set(self.brands), key=len, reverse=True)
            self._dirty = True
            
            if self.auto_save:
                self._save_brands()
    
    def get_brand_count(self) -> int:
        """Get the number of known brands"""
        return len(self.brands)
    
    def get_all_brands(self) -> List[str]:
        """Get list of all known brands"""
        return sorted(self.brands)
    
    def save_if_dirty(self):
        """Save brands to file if changes were made"""
        if self._dirty:
            self._save_brands()
    
    def __del__(self):
        """Destructor - save if dirty on cleanup"""
        if hasattr(self, '_dirty') and self._dirty:
            self._save_brands()


# Singleton instance for easy import
_brand_detector_instance = None

def get_brand_detector(brands_file: Optional[str] = None) -> BrandDetector:
    """Get or create the global brand detector instance"""
    global _brand_detector_instance
    if _brand_detector_instance is None:
        _brand_detector_instance = BrandDetector(brands_file)
    return _brand_detector_instance


if __name__ == "__main__":
    # Example usage
    detector = BrandDetector()
    
    print(f"Loaded {detector.get_brand_count()} brands")
    
    # Test detection
    test_products = [
        "Coca-Cola Original 330ml",
        "Nescafe Gold Blend Coffee 200g",
        "Cadbury Dairy Milk Chocolate",
        "Unknown Brand Product"
    ]
    
    for product in test_products:
        brand = detector.detect_brand(product)
        print(f"'{product}' → Brand: {brand}")
    
    # Add new brand
    detector.add_brand("TestBrand")
    detector.save_if_dirty()