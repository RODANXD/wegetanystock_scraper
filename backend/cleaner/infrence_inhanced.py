# inference_enhanced.py
"""
Enhanced Inference Engine: Extract insights from product descriptions
Includes nutritional info extraction, allergen detection, and certification identification
"""

import re
from typing import Dict, Any, List, Optional


class DescriptionExtractor:
    """Extract valuable information from product descriptions"""
    
    def __init__(self):
        pass
    
    def extract_nutritional_info(self, description_text: str) -> Optional[Dict]:
        """
        Extract nutritional information from description text
        Returns dict with nutritional values mapped to schema fields
        """
        if not description_text:
            return {}
        
        nutrition = {}
        
        # Nutritional patterns (UK/EU format)
        patterns = {
            'Calories (kcal)': [
                r'Energy[:\s]*(\d+(?:\.\d+)?)\s*kcal',
                r'(\d+(?:\.\d+)?)\s*kcal',
            ],
            'Total Fat (g)': [
                r'Fat[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'Total\s+Fat[:\s]*(\d+(?:\.\d+)?)\s*g',
            ],
            'Saturated Fat (g)': [
                r'(?:of which[:\s]*)?saturates?[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'Saturated\s+Fat[:\s]*(\d+(?:\.\d+)?)\s*g',
            ],
            'Total Carbohydrates (g)': [
                r'Carbohydrate[s]?[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'Total\s+Carbohydrate[s]?[:\s]*(\d+(?:\.\d+)?)\s*g',
            ],
            'Total Sugars (g)': [
                r'(?:of which[:\s]*)?sugars?[:\s]*(\d+(?:\.\d+)?)\s*g',
            ],
            'Dietary Fiber (g)': [
                r'Fibre[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'Fiber[:\s]*(\d+(?:\.\d+)?)\s*g',
                r'Dietary\s+Fibre[:\s]*(\d+(?:\.\d+)?)\s*g',
            ],
            'Protein (g)': [
                r'Protein[:\s]*(\d+(?:\.\d+)?)\s*g',
            ],
            'Sodium (mg)': [
                r'Salt[:\s]*(\d+(?:\.\d+)?)\s*g',  # Will convert to mg
                r'Sodium[:\s]*(\d+(?:\.\d+)?)\s*mg',
            ],
        }
        
        for field_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, description_text, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    
                    # Special handling for salt → sodium conversion
                    if 'Salt' in pattern and 'g' in pattern:
                        # Salt (g) → Sodium (mg): multiply by 400
                        value = value * 400
                    
                    nutrition[field_name] = value
                    break  # Found match, move to next field
        
        return nutrition if nutrition else None
    
    def extract_allergens(self, description_text: str, allergy_warning: str = "") -> List[str]:
        """Extract allergen information from descriptions and warnings"""
        allergens_set = set()
        
        # Combine both sources
        full_text = f"{description_text} {allergy_warning}".lower()
        
        # Allergen mapping (pattern → standardized name)
        allergen_patterns = {
            'Peanuts': [r'\bpeanuts?\b', r'\bgroundnuts?\b'],
            'Tree Nuts': [r'\btree nuts?\b', r'\bnuts?\b', r'\balmonds?\b', r'\bcashews?\b', 
                         r'\bwalnuts?\b', r'\bpecans?\b', r'\bhazelnuts?\b', r'\bpistachios?\b'],
            'Milk': [r'\bmilk\b', r'\bdairy\b', r'\blactose\b', r'\bwhey\b', r'\bcasein\b', r'\bcream\b'],
            'Eggs': [r'\beggs?\b', r'\balbumin\b'],
            'Wheat': [r'\bwheat\b', r'\bgluten\b'],
            'Soy': [r'\bsoy\b', r'\bsoya\b', r'\bsoybeans?\b'],
            'Fish': [r'\bfish\b', r'\banchovies\b', r'\btuna\b', r'\bsalmon\b', r'\bcod\b'],
            'Shellfish': [r'\bshellfish\b', r'\bcrustaceans?\b', r'\bshrimp\b', r'\bcrab\b', 
                         r'\blobster\b', r'\bmussels?\b', r'\boysters?\b'],
            'Sesame': [r'\bsesame\b', r'\btahini\b'],
            'Mustard': [r'\bmustard\b'],
            'Celery': [r'\bcelery\b'],
            'Lupin': [r'\blupin\b'],
            'Sulphites': [r'\bsulphites?\b', r'\bsulfites?\b', r'\bsulphur dioxide\b'],
        }
        
        for allergen_name, patterns in allergen_patterns.items():
            for pattern in patterns:
                if re.search(pattern, full_text):
                    allergens_set.add(allergen_name)
                    break  # Found this allergen, move to next
        
        return sorted(list(allergens_set)) if allergens_set else None
    
    def extract_ingredients(self, description_text: str) -> Optional[List[str]]:
        """Extract ingredients list from description"""
        if not description_text:
            return None
        
        # Look for ingredients section
        patterns = [
            r'Ingredients?[:\s]+(.*?)(?:\n\n|\.|Storage|Allergy|Nutrition|Contains:|May contain)',
            r'Contains?[:\s]+(.*?)(?:\n\n|\.|Storage|Allergy|Nutrition)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description_text, re.IGNORECASE | re.DOTALL)
            if match:
                ingredients_text = match.group(1).strip()
                
                # Split by comma or semicolon
                ingredients = re.split(r'[,;]', ingredients_text)
                
                # Clean each ingredient
                cleaned = []
                for ing in ingredients:
                    ing = ing.strip()
                    # Remove percentages in parentheses
                    ing = re.sub(r'\s*\(\d+%?\)', '', ing)
                    # Remove allergen warnings
                    ing = re.sub(r'\s*\([^)]*allergen[^)]*\)', '', ing, flags=re.IGNORECASE)
                    if ing and len(ing) > 2:  # Skip empty or very short
                        cleaned.append(ing)
                
                return cleaned[:30] if cleaned else None  # Limit to 30 ingredients
        
        return None
    
    def extract_country_of_origin(self, description_text: str) -> Optional[str]:
        """Extract country of origin from description"""
        if not description_text:
            return None
        
        patterns = [
            r'(?:Product of|Made in|Origin[:\s]+|Country of origin[:\s]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+origin',
            r'Produce of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description_text)
            if match:
                country = match.group(1).strip()
                
                # Validate against common countries
                common_countries = [
                    'India', 'UK', 'USA', 'China', 'Pakistan', 'Sri Lanka', 
                    'Bangladesh', 'Italy', 'France', 'Spain', 'Germany', 
                    'Netherlands', 'Thailand', 'Mexico', 'Brazil', 'Poland',
                    'United Kingdom', 'United States'
                ]
                
                if any(country.lower() == c.lower() for c in common_countries):
                    return country
        
        return None
    
    def extract_certifications(self, description_text: str) -> Optional[List[str]]:
        """Extract certifications and special attributes"""
        if not description_text:
            return None
        
        certifications_set = set()
        
        # Certification patterns
        cert_patterns = {
            'USDA Organic': [r'\bUSDA\s+Organic\b'],
            'Organic': [r'\borganic\b', r'\bcertified organic\b'],
            'Vegan': [r'\bvegan\b', r'\bplant-based\b'],
            'Vegetarian': [r'\bvegetarian\b', r'\bveggie\b'],
            'Halal': [r'\bhalal\b', r'\bcertified halal\b'],
            'Kosher': [r'\bkosher\b', r'\bcertified kosher\b'],
            'Gluten-Free': [r'\bgluten[- ]free\b', r'\bno gluten\b'],
            'Dairy-Free': [r'\bdairy[- ]free\b', r'\blactose[- ]free\b'],
            'Nut-Free': [r'\bnut[- ]free\b'],
            'Non-GMO': [r'\bnon[- ]GMO\b', r'\bGMO[- ]free\b'],
            'Fair Trade': [r'\bfair\s+trade\b', r'\bfairtrade\b'],
            'Rainforest Alliance': [r'\bRainforest\s+Alliance\b'],
        }
        
        text_lower = description_text.lower()
        
        for cert_name, patterns in cert_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    certifications_set.add(cert_name)
                    break
        
        return sorted(list(certifications_set)) if certifications_set else None
    
    def extract_storage_instructions(self, description_text: str) -> Optional[str]:
        """Extract storage instructions"""
        if not description_text:
            return None
        
        patterns = [
            r'Storage[:\s]+(.*?)(?:\n\n|\.|Allergy|Nutrition|Ingredients)',
            r'Store\s+in\s+(.*?)(?:\n\n|\.|Allergy|Nutrition|Ingredients)',
            r'Keep\s+(.*?)(?:\n\n|\.|Allergy|Nutrition|Ingredients)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description_text, re.IGNORECASE | re.DOTALL)
            if match:
                storage = match.group(1).strip()
                # Clean up and limit length
                storage = re.sub(r'\s+', ' ', storage)
                return storage[:200]  # Limit to 200 chars
        
        return None


class EnhancedInferenceEngine:
    """Enhanced inference combining base inference with description extraction"""
    
    def __init__(self):
        # Import the base inference engine
        from .infrence import InferenceEngine
        
        self.base_inference = InferenceEngine()
        self.description_extractor = DescriptionExtractor()
    
    def extract_from_description(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract additional data from product descriptions
        """
        enriched = {}
        
        # Get description fields
        description_text = product.get('description_text', '') or product.get('Long Description', '') or ''
        allergy_warning = product.get('allergy_warning', '') or product.get('Allergens', '')
        
        # Convert allergy_warning to string if it's a list
        if isinstance(allergy_warning, list):
            allergy_warning = ', '.join(allergy_warning)
        
        # Extract nutritional information
        nutrition = self.description_extractor.extract_nutritional_info(description_text)
        if nutrition:
            for field_name, value in nutrition.items():
                if product.get(field_name) is None:  # Only fill if not already present
                    enriched[field_name] = value
        
        # Extract allergens (will merge with any existing)
        extracted_allergens = self.description_extractor.extract_allergens(
            description_text, 
            str(allergy_warning) if allergy_warning else ''
        )
        if extracted_allergens:
            # Merge with existing allergens
            existing = product.get('Allergens', [])
            if existing:
                all_allergens = list(set(existing + extracted_allergens))
                enriched['Allergens'] = sorted(all_allergens)
            else:
                enriched['Allergens'] = extracted_allergens
        
        # Extract ingredients
        if not product.get('Ingredients List'):
            ingredients = self.description_extractor.extract_ingredients(description_text)
            if ingredients:
                enriched['Ingredients List'] = ingredients
        
        # Extract country of origin
        if not product.get('Country of Origin'):
            country = self.description_extractor.extract_country_of_origin(description_text)
            if country:
                enriched['Country of Origin'] = country
        
        # Extract certifications (merge with existing)
        certifications = self.description_extractor.extract_certifications(description_text)
        if certifications:
            existing_certs = product.get('Product Certifications', [])
            if existing_certs:
                all_certs = list(set(existing_certs + certifications))
                enriched['Product Certifications'] = sorted(all_certs)
            else:
                enriched['Product Certifications'] = certifications
        
        # Extract storage instructions
        if not product.get('Storage Instructions'):
            storage = self.description_extractor.extract_storage_instructions(description_text)
            if storage:
                enriched['Storage Instructions'] = storage
        
        return enriched
    
    def apply_all_inferences(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply both base inference and description extraction
        """
        # First apply base inference (brand, category, dietary flags, etc.)
        product = self.base_inference.apply_all_inferences(product)
        
        # Then extract from descriptions
        description_enrichment = self.extract_from_description(product)
        
        # Merge enrichment
        for field, value in description_enrichment.items():
            if value is not None:
                product[field] = value
        
        return product