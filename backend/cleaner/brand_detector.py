# """
# Brand Detection Module
# Detects brand names from product titles using a hardcoded list
# """

# import re
# from typing import Optional, List, Tuple


# class BrandDetector:
#     """Detects brand names from product names"""
    
#     # Comprehensive list of brands (expandable)
#     BRANDS = [
#         # Soft Drinks
#         "Coca-Cola", "Coca Cola", "Coke",
#         "Pepsi", "PepsiCo",
#         "Fanta",
#         "Sprite",
#         "7UP", "7-Up", "Seven Up",
#         "Dr Pepper", "Dr. Pepper",
#         "Mountain Dew", "Mtn Dew",
#         "Schweppes",
#         "Tango",
#         "Irn-Bru", "Irn Bru", "IRN-BRU",
#         "Ribena",
#         "Vimto",
#         "Robinsons",
#         "Oasis",
#         "Tropicana",
#         "Capri-Sun", "Capri Sun",
#         "Fruit Shoot",
#         "Starbucks", "Starbucks Coffee",
#         "Costa Coffee", "Costa",
#         "Rubicon",
#         "Cinnabon",
#         "Pac Man",
#         "Icelandic ",
#         "Appletiser",
        
        
#         # Energy Drinks
#         "Red Bull", "RedBull",
#         "Monster", "Monster Energy",
#         "Lucozade",
#         "Relentless",
#         "Rockstar",
#         "Prime",
#         "Boost",
#         "Emerge",
#         "Hell", "Hell Energy",
#         "Reign",
#         "Bang",
#         "Celsius",
#         "G Fuel", "GFuel",
#         "Old jamaica",
#         "Fiji",
#         "Lipton",
#         "Bubbleology",
#         "Nestle",
#         "Nescafe",
#         "Alpro",
#         "Bottlegreen",
#         "Applied Nutrition",
#         "Fever-tree",
#         "Cawston Press",
#         "Barr",
#         "London Essence",
        
#         # Water & Sports Drinks
#         "Evian",
#         "Volvic",
#         "Highland Spring",
#         "Buxton",
#         "Perrier",
#         "San Pellegrino", "S.Pellegrino",
#         "Powerade",
#         "Gatorade",
        
#         "Pipers",
        
#         # Confectionery & Chocolate
        
#         "Galaxy",
#         "Mars",
#         "Snickers",
#         "Twix",
        
#         "Milky Way",
#         "Maltesers",
        
#         "Lindt",
#         "Ferrero Rocher", "Ferrero",
#         "Kinder",
#         "Haribo",
#         "Maynards",
#         "Bassetts",
#         "Rowntree's", "Rowntrees",
#         "Skittles",
#         "Starburst",
        
#         "Double Decker",
#         "Boost",
        
#         "Reese's", "Reeses",
#         "Hershey's", "Hersheys",
#         "Oreo",
#         "Toblerone",
#         "Terry's", "Terrys",
#         "Quality Street",
#         "Celebrations",
#         "Roses",
#         "Heroes",
    
        
#         # Other Brands
      
#         "Tropicana",
#         "Copella",
#         "Ocean Spray",
#         "Princes",
#         "Del Monte",
#         "Heinz",
        
#     ]
    
#     def __init__(self, additional_brands: Optional[List[str]] = None):
#         """Initialize with optional additional brands"""
#         self.brands = self.BRANDS.copy()
#         if additional_brands:
#             self.brands.extend(additional_brands)
        
#         # Sort by length (longest first) for accurate matching
#         self.brands = sorted(set(self.brands), key=len, reverse=True)
        
#         # Create brand mapping for normalization
#         self.brand_mapping = self._create_brand_mapping()
    
#     def _create_brand_mapping(self) -> dict:
#         """Create mapping of variations to canonical brand names"""
#         mapping = {
#             # Coca-Cola variations
#             "coca cola": "Coca-Cola",
#             "coke": "Coca-Cola",
#             "coca-cola": "Coca-Cola",
            
#             # 7UP variations
#             "7up": "7UP",
#             "7-up": "7UP",
#             "seven up": "7UP",
            
#             # Dr Pepper variations
#             "dr pepper": "Dr Pepper",
#             "dr. pepper": "Dr Pepper",
            
#             # Irn-Bru variations
#             "irn bru": "Irn-Bru",
#             "irn-bru": "Irn-Bru",
            
#             # Red Bull variations
#             "redbull": "Red Bull",
#             "red bull": "Red Bull",
            
#             # Capri Sun variations
#             "capri sun": "Capri-Sun",
#             "capri-sun": "Capri-Sun",
            
            
#             # Reese's variations
#             "reeses": "Reese's",
#             "reese's": "Reese's",
            
#             "Appletiser": "Coca-Cola",
#         }
#         return mapping
    
#     def detect_brand(self, product_name: str) -> Optional[str]:
#         """
#         Detect brand name from product name
#         Returns the canonical brand name or None
#         """
#         if not product_name:
#             return None
        
#         name_lower = product_name.lower()
        
#         # First, check the mapping for known variations
#         for variation, canonical in self.brand_mapping.items():
#             if variation in name_lower:
#                 return canonical
        
#         # Then, check against all brands
#         for brand in self.brands:
#             # Create pattern for word boundary matching
#             pattern = r'\b' + re.escape(brand) + r'\b'
#             if re.search(pattern, product_name, re.IGNORECASE):
#                 return brand
        
#         return None
    
#     def detect_all_brands(self, product_name: str) -> List[str]:
#         """Detect all brand names in a product name"""
#         if not product_name:
#             return []
        
#         found_brands = []
#         name_lower = product_name.lower()
        
#         for brand in self.brands:
#             pattern = r'\b' + re.escape(brand) + r'\b'
#             if re.search(pattern, product_name, re.IGNORECASE):
#                 # Normalize to canonical name
#                 canonical = self.brand_mapping.get(brand.lower(), brand)
#                 if canonical not in found_brands:
#                     found_brands.append(canonical)
        
#         return found_brands
    
#     def extract_brand_and_product(self, product_name: str) -> Tuple[Optional[str], str]:
#         """
#         Extract brand and remaining product description
#         Returns (brand, remaining_name)
#         """
#         brand = self.detect_brand(product_name)
        
#         if brand:
#             # Remove brand from product name
#             pattern = r'\b' + re.escape(brand) + r'\b\s*'
#             remaining = re.sub(pattern, '', product_name, flags=re.IGNORECASE).strip()
#             return brand, remaining
        
#         return None, product_name


# # Singleton instance for easy import
# brand_detector = BrandDetector()


# if __name__ == "__main__":
    
   
    
#     detector = BrandDetector()
    
  
  
import json
import os
import re
from typing import Optional, List, Tuple


class BrandDetector:
    """Detects brand names from product titles using a JSON configuration file"""
    
    def __init__(self, brands_file: Optional[str] = None):
        """
        Initialize BrandDetector with brands from JSON file
        
        Args:
            brands_file: Path to brands.json file. If None, uses default relative path.
        """
        if brands_file is None:
            # Construct path relative to this file's directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            brands_file = os.path.join(current_dir, '..', 'data', 'brands.json')
        
        self.brands = self._load_brands(brands_file)
        self.brands = sorted(set(self.brands), key=len, reverse=True)
        self.brand_mapping = self._load_brand_mapping(brands_file)

    def _load_brands(self, path: str) -> List[str]:
        """Load brands list from JSON file"""
        try:
            if not os.path.exists(path):
                print(f"⚠️  Brands file not found: {path}")
                return []

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                brands = data.get('brands', []) if isinstance(data, dict) else data
                if isinstance(brands, list):
                    return brands
                else:
                    print(f"⚠️  Invalid brands format in {path}")
                    return []
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Error loading brands from {path}: {e}")
            return []

    def _load_brand_mapping(self, path: str) -> dict:
        """Load brand name variations mapping from JSON file"""
        try:
            if not os.path.exists(path):
                return {}

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get('brand_mapping', {}) if isinstance(data, dict) else {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Error loading brand mapping from {path}: {e}")
            return {}

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
            if variation in name_lower:
                return canonical
        
        # Then, check against all brands
        for brand in self.brands:
            pattern = r'\b' + re.escape(brand) + r'\b'
            if re.search(pattern, product_name, re.IGNORECASE):
                return brand

        return None
    
    def detect_all_brands(self, product_name: str) -> List[str]:
        """Detect all brand names in a product name"""
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
    
    def extract_brand_and_product(self, product_name: str) -> Tuple[Optional[str], str]:
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


# Singleton instance for easy import
brand_detector = BrandDetector()
