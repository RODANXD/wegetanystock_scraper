# inference.py
"""
Inference Engine: Automatically infer missing fields from available data
"""

import re
from typing import Dict, Any, List, Optional


class InferenceEngine:
    """Handles all field inference and enrichment logic."""
    
    def __init__(self):
        # Brand detection patterns
        self.brand_patterns = self._load_brand_patterns()
        
        # Dietary keywords for inference
        self.dietary_keywords = {
            'vegan': ['vegan', '100% plant', 'plant-based'],
            'vegetarian': ['vegetarian', 'veggie'],
            'gluten_free': ['gluten-free', 'gluten free', 'gf'],
            'dairy_free': ['dairy-free', 'dairy free', 'lactose-free'],
            'organic': ['organic', 'bio', 'usda organic'],
            'non_gmo': ['non-gmo', 'non gmo', 'gmo-free'],
            'keto': ['keto', 'ketogenic', 'keto-friendly'],
            'paleo': ['paleo', 'paleo-friendly'],
            'kosher': ['kosher', 'certified kosher'],
            'halal': ['halal', 'certified halal'],
        }
        
        # Allergen keywords
        self.allergen_keywords = {
            'peanuts': ['peanut', 'groundnut'],
            'tree_nuts': ['almond', 'cashew', 'walnut', 'pecan', 'hazelnut', 'pistachio', 'macadamia'],
            'milk': ['milk', 'dairy', 'lactose', 'whey', 'casein', 'cheese', 'butter', 'cream', 'yogurt'],
            'eggs': ['egg', 'albumin', 'mayonnaise'],
            'wheat': ['wheat', 'flour', 'gluten'],
            'soy': ['soy', 'soya', 'tofu', 'edamame', 'miso'],
            'fish': ['fish', 'salmon', 'tuna', 'cod', 'anchovy'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'prawn', 'mussel', 'oyster', 'clam'],
            'sesame': ['sesame', 'tahini'],
        }
        
        # Packaging types
        self.canned_keywords = ['canned', 'can', 'tinned', 'tin']
        
    def _load_brand_patterns(self) -> Dict[str, List[str]]:
        """Load common brand patterns for detection."""
        return {
            'Nestle': ['nestle', 'nescafe', 'kitkat', 'maggi'],
            'Unilever': ['dove', 'axe', 'knorr', 'lipton'],
            'PepsiCo': ['pepsi', 'lays', 'doritos', 'gatorade', 'tropicana'],
            'Coca-Cola': ['coca-cola', 'coke', 'sprite', 'fanta', 'dasani'],
            'Kraft Heinz': ['kraft', 'heinz', 'philadelphia', 'oscar mayer'],
            "Kellogg's": ['kelloggs', 'pringles', 'special k', 'frosted flakes'],
            # Add more brands as needed
        }
    
    def infer_brand(self, product: Dict[str, Any]) -> Optional[str]:
        """Infer brand from product name or description."""
        if product.get('Brand'):
            return product['Brand']
        
        text_fields = [
            product.get('Product Name', ''),
            product.get('Short Description', ''),
            product.get('Long Description', '')
        ]
        
        combined_text = ' '.join([str(f) for f in text_fields if f]).lower()
        
        # Check against known brands
        for brand, patterns in self.brand_patterns.items():
            for pattern in patterns:
                if pattern in combined_text:
                    return brand
        
        # Try to extract brand from product name (often first word or capitalized)
        product_name = product.get('Product Name', '')
        if product_name:
            # Extract first capitalized word/phrase
            match = re.match(r'^([A-Z][a-zA-Z0-9&\'\-]+)', product_name.strip())
            if match:
                return match.group(1)
        
        return None
    
    def infer_dietary_flags(self, product: Dict[str, Any]) -> Dict[str, bool]:
        """Infer dietary flags from name, description, ingredients, certifications."""
        flags = {}
        
        # Combine searchable text
        text_fields = [
            product.get('Product Name', ''),
            product.get('Short Description', ''),
            product.get('Long Description', ''),
            product.get('Tags', []),
            product.get('Product Certifications', []),
        ]
        
        ingredients = product.get('Ingredients List', [])
        if ingredients:
            text_fields.append(' '.join(ingredients))
        
        combined_text = ' '.join([str(f) for f in text_fields if f]).lower()
        
        # Check dietary keywords
        for diet_type, keywords in self.dietary_keywords.items():
            flags[diet_type] = any(kw in combined_text for kw in keywords)
        
        # Additional logic: if no animal products in ingredients → likely vegan
        if ingredients and flags.get('vegan') is False:
            animal_products = ['meat', 'chicken', 'beef', 'pork', 'fish', 'egg', 'milk', 'honey', 'gelatin']
            has_animal = any(
                any(ap in ing.lower() for ap in animal_products) 
                for ing in ingredients
            )
            if not has_animal:
                flags['vegan'] = True
        
        return flags
    
    def infer_allergens(self, product: Dict[str, Any]) -> List[str]:
        """Detect allergens from ingredients and product info."""
        allergens = set()
        
        # Check ingredients list
        ingredients = product.get('Ingredients List', [])
        if ingredients:
            ingredients_text = ' '.join([str(i).lower() for i in ingredients])
            
            for allergen_name, keywords in self.allergen_keywords.items():
                if any(kw in ingredients_text for kw in keywords):
                    allergens.add(allergen_name.replace('_', ' ').title())
        
        # Check product name and descriptions
        text = ' '.join([
            str(product.get('Product Name', '')),
            str(product.get('Short Description', '')),
        ]).lower()
        
        for allergen_name, keywords in self.allergen_keywords.items():
            if any(kw in text for kw in keywords):
                allergens.add(allergen_name.replace('_', ' ').title())
        
        return sorted(list(allergens))
    
    def infer_allergen_flags(self, allergens: List[str]) -> Dict[str, bool]:
        """Set individual allergen flags based on detected allergens."""
        flags = {
            'Contains Peanuts': 'Peanuts' in allergens,
            'Contains Tree Nuts': 'Tree Nuts' in allergens,
            'Contains Milk': 'Milk' in allergens,
            'Contains Eggs': 'Eggs' in allergens,
            'Contains Wheat': 'Wheat' in allergens,
            'Contains Soybeans': 'Soy' in allergens,
            'Contains Fish': 'Fish' in allergens,
            'Contains Shellfish': 'Shellfish' in allergens,
            'Contains Sesame': 'Sesame' in allergens,
        }
        return flags
    
    def infer_nut_free(self, allergens: List[str]) -> bool:
        """Infer if product is nut-free."""
        nut_allergens = ['Peanuts', 'Tree Nuts']
        return not any(allergen in allergens for allergen in nut_allergens)
    
    def infer_packaging_type(self, product: Dict[str, Any]) -> Dict[str, bool]:
        """Infer if product is canned or not."""
        text = ' '.join([
            str(product.get('Product Name', '')),
            str(product.get('Package Size', '')),
            str(product.get('Short Description', '')),
        ]).lower()
        
        is_canned = any(kw in text for kw in self.canned_keywords)
        
        return {
            'Canned Food': is_canned,
            'Non Canned Food': not is_canned,
        }
    
    def infer_category(self, product: Dict[str, Any]) -> Optional[str]:
        """Infer category from product name and description."""
        if product.get('Category'):
            return product['Category']
        
        # Simple category inference based on keywords
        text = str(product.get('Product Name', '')).lower()
        
        categories = {
            'Beverages': ['juice', 'soda', 'water', 'tea', 'coffee', 'drink'],
            'Dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
            'Snacks': ['chips', 'crackers', 'popcorn', 'nuts', 'snack'],
            'Bakery': ['bread', 'cookies', 'cake', 'pastry', 'muffin'],
            'Canned Goods': ['canned', 'can'],
            'Frozen Foods': ['frozen'],
            'Condiments': ['sauce', 'ketchup', 'mustard', 'mayo', 'dressing'],
        }
        
        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category
        
        return None
    
    def infer_nutrition_based_flags(self, product: Dict[str, Any]) -> Dict[str, bool]:
        """Infer dietary flags based on nutrition facts."""
        flags = {}
        
        # High Protein (>10g per serving)
        protein = product.get('Protein (g)')
        flags['High Protein'] = protein is not None and float(protein) > 10
        
        # High Fiber (>5g per serving)
        fiber = product.get('Dietary Fiber (g)')
        flags['High Fiber'] = fiber is not None and float(fiber) > 5
        
        # Low Sugar (<5g per serving)
        sugars = product.get('Total Sugars (g)')
        flags['Low Sugar'] = sugars is not None and float(sugars) < 5
        
        # Low Sodium (<140mg per serving)
        sodium = product.get('Sodium (mg)')
        flags['Low Sodium'] = sodium is not None and float(sodium) < 140
        
        # Low Carb (<10g per serving)
        carbs = product.get('Total Carbohydrates (g)')
        flags['Low Carb'] = carbs is not None and float(carbs) < 10
        
        return flags
    
    def apply_all_inferences(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all inference rules to enrich product data."""
        
        # Infer brand
        if not product.get('Brand'):
            product['Brand'] = self.infer_brand(product)
        
        # Infer category
        if not product.get('Category'):
            product['Category'] = self.infer_category(product)
        
        # Infer dietary flags
        dietary_flags = self.infer_dietary_flags(product)
        if dietary_flags.get('vegan') and product.get('Vegan') is None:
            product['Vegan'] = True
        if dietary_flags.get('vegetarian') and product.get('Vegetarian') is None:
            product['Vegetarian'] = True
        if dietary_flags.get('gluten_free') and product.get('Gluten-Free') is None:
            product['Gluten-Free'] = True
        if dietary_flags.get('dairy_free') and product.get('Dairy-Free') is None:
            product['Dairy-Free'] = True
        if dietary_flags.get('organic') and product.get('Organic') is None:
            product['Organic'] = True
        if dietary_flags.get('non_gmo') and product.get('Non-GMO') is None:
            product['Non-GMO'] = True
        if dietary_flags.get('keto') and product.get('Keto-Friendly') is None:
            product['Keto-Friendly'] = True
        if dietary_flags.get('paleo') and product.get('Paleo-Friendly') is None:
            product['Paleo-Friendly'] = True
        if dietary_flags.get('kosher') and product.get('Kosher') is None:
            product['Kosher'] = True
        if dietary_flags.get('halal') and product.get('Halal') is None:
            product['Halal'] = True
        
        # Infer allergens
        if not product.get('Allergens'):
            allergens = self.infer_allergens(product)
            product['Allergens'] = allergens
        else:
            allergens = product['Allergens']
        
        # Set allergen flags
        allergen_flags = self.infer_allergen_flags(allergens)
        for flag_name, flag_value in allergen_flags.items():
            if product.get(flag_name) is None:
                product[flag_name] = flag_value
        
        # Infer nut-free
        if product.get('Nut-Free') is None:
            product['Nut-Free'] = self.infer_nut_free(allergens)
        
        # Infer packaging type
        packaging_flags = self.infer_packaging_type(product)
        if product.get('Canned Food') is None:
            product['Canned Food'] = packaging_flags['Canned Food']
        if product.get('Non Canned Food') is None:
            product['Non Canned Food'] = packaging_flags['Non Canned Food']
        
        # Infer nutrition-based flags
        nutrition_flags = self.infer_nutrition_based_flags(product)
        for flag_name, flag_value in nutrition_flags.items():
            if product.get(flag_name) is None:
                product[flag_name] = flag_value
        
        return product