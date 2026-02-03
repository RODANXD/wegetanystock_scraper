# cleaner_integrated.py
"""
Integrated Central Data Cleaner
Combines brand detection, product cleaning, normalization, and inference
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .schema import PRODUCT_SCHEMA, FIELD_TYPES, get_empty_product
from .normalization import NormalizationEngine
from .infrence_inhanced import EnhancedInferenceEngine
from .brand_detector import get_brand_detector


class   IntegratedProductCleaner:
    """
    Central cleaner that combines:
    1. Brand detection (with auto-learning)
    2. Product name cleaning
    3. Field normalization
    4. Smart inference
    5. Description extraction
    6. Schema enforcement
    """
    
    def __init__(self, brands_file: Optional[str] = None):
        self.normalizer = NormalizationEngine()
        self.inferencer = EnhancedInferenceEngine()
        self.brand_detector = get_brand_detector(brands_file)
        self.schema = PRODUCT_SCHEMA
        self.field_types = FIELD_TYPES
    
    def load_raw_products(self, file_path: str) -> List[Dict[str, Any]]:
        """Load raw product data from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both single object and array
        if isinstance(data, dict):
            # Check if it has a 'products' key
            if 'products' in data:
                return data['products']
            else:
                return [data]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Invalid JSON format: expected list or object")
    
    def clean_and_normalize_product(self, raw_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 1: Clean product names, detect brands, normalize all fields
        Extracts all available data from raw product to match schema
        """
        normalized = get_empty_product()
        
        # Get original name
        original_name = raw_product.get('name') or raw_product.get('Product Name', '')
        
        # ===== PRODUCT NAME CLEANING =====
        if original_name:
            # Clean the product name (remove prices, sizes, etc.)
            cleaned_name = self.normalizer.clean_product_name(original_name)
            normalized['Product Name'] = cleaned_name
        
        # ===== BRAND DETECTION =====
        existing_brand = raw_product.get('brand') or raw_product.get('Brand')
        if existing_brand and str(existing_brand).upper() not in ['N/A', 'NA', 'NONE', 'NULL']:
            normalized['Brand'] = self.normalizer.normalize_text(existing_brand)
            # Learn this brand for future detection
            if normalized['Brand']:
                self.brand_detector.learn_brand(original_name, normalized['Brand'])
        else:
            # Detect brand from product name
            detected_brand = self.brand_detector.detect_brand(original_name)
            normalized['Brand'] = detected_brand
        
        # ===== EXTRACT CATEGORY AND SUBCATEGORY =====
        category_raw = raw_product.get('category', '')
        if category_raw:
            # Parse hierarchical category: "Grocery > Soft Drinks > 1 and 1.5 Ltr Bottles"
            parts = [p.strip() for p in str(category_raw).split('>')]
            if len(parts) >= 1:
                normalized['Category'] = self.normalizer.normalize_category(parts[0])
            if len(parts) >= 2:
                normalized['Subcategory'] = self.normalizer.normalize_text(parts[1])
        
        # ===== EXTRACT BARCODE =====
        barcode = raw_product.get('Retail Ean') or raw_product.get('product_code') or raw_product.get('sku')
        if barcode:
            normalized['Barcode (EAN/UPC)'] = self.normalizer.normalize_text(barcode)
        
        # ===== EXTRACT BASIC PRODUCT INFO =====
        # Map common raw fields to schema
        basic_mappings = {
            'description': 'Long Description',
            'product': 'Short Description',
            'image': 'Featured Image URL',
            'url': None,  # Skip URL mapping (tracking field)
            'price': None,  # Skip price (not in schema)
            'rsp': None,  # Skip RRP
        }
        
        for raw_field, schema_field in basic_mappings.items():
            if schema_field and raw_field in raw_product:
                value = raw_product[raw_field]
                if value and not normalized.get(schema_field):
                    normalized[schema_field] = self.normalizer.normalize_text(value)
        
        # ===== EXTRACT PACKAGE SIZE AND VOLUME =====
        size_raw = raw_product.get('size') or raw_product.get('Size', '')
        if size_raw and not normalized.get('Package Size'):
            normalized['Package Size'] = self.normalizer.normalize_text(size_raw)
            # Also try to extract volume/weight
            volume_weight = self.normalizer.extract_volume_weight(str(size_raw))
            if volume_weight and volume_weight['type'] == 'volume':
                normalized['Volume for Liquids (ml/L)'] = self.normalizer.normalize_volume(
                    f"{volume_weight['value']}{volume_weight['unit']}"
                )
        
        # Extract from product name if not found
        if not normalized.get('Package Size'):
            volume_weight = self.normalizer.extract_volume_weight(original_name)
            if volume_weight:
                normalized['Package Size'] = f"{volume_weight['value']}{volume_weight['unit']}"
                if volume_weight['type'] == 'volume' and not normalized.get('Volume for Liquids (ml/L)'):
                    normalized['Volume for Liquids (ml/L)'] = self.normalizer.normalize_volume(
                        f"{volume_weight['value']}{volume_weight['unit']}"
                    )
        
        # ===== EXTRACT NUTRITIONAL DATA FROM ingredients_description =====
        ingredients_desc = raw_product.get('ingredients_description', {})
        if isinstance(ingredients_desc, dict):
            nutrition_mappings = {
                'Energy': 'Calories (kcal)',  # Note: Energy is in kJ, need to convert
                'Fat': 'Total Fat (g)',
                'of which saturates': 'Saturated Fat (g)',
                'Carbohydrate': 'Total Carbohydrates (g)',
                'of which sugars': 'Total Sugars (g)',
                'Protein': 'Protein (g)',
                'Salt': 'Sodium (mg)',  # Note: Salt in g, Sodium in mg
            }
            
            for raw_key, schema_key in nutrition_mappings.items():
                if raw_key in ingredients_desc:
                    value = ingredients_desc[raw_key]
                    # Convert energy from kJ to kcal (1 kcal = 4.184 kJ)
                    if raw_key == 'Energy' and isinstance(value, str):
                        try:
                            kj_value = float(value.replace('kJ', '').replace('kj', '').strip())
                            kcal_value = kj_value / 4.184
                            normalized[schema_key] = round(kcal_value, 1)
                        except:
                            pass
                    # Convert salt from g to mg (1g = 1000mg)
                    elif raw_key == 'Salt' and isinstance(value, str):
                        try:
                            g_value = float(value.replace('g', '').strip())
                            mg_value = g_value * 1000
                            normalized[schema_key] = round(mg_value, 1)
                        except:
                            pass
                    else:
                        # Standard numeric extraction
                        numeric_value = self.normalizer.normalize_number(value)
                        if numeric_value is not None:
                            normalized[schema_key] = numeric_value
        
        # ===== EXTRACT ALLERGEN INFO FROM other_info =====
        other_info = raw_product.get('other_info', [])
        if isinstance(other_info, list):
            allergens = []
            certifications = []
            free_from = []
            
            for info in other_info:
                if not info:
                    continue
                info_str = str(info)
                
                # Map "Free From X" to allergens/certifications
                if 'Free From' in info_str:
                    # Extract allergen
                    allergen = info_str.replace('Free From', '').strip()
                    if allergen and allergen not in allergens:
                        allergens.append(allergen)
                    # Map to boolean flags
                    if 'Gluten' in allergen:
                        normalized['Gluten-Free'] = True
                        normalized['Egg-Free'] = True
                    elif 'Milk' in allergen:
                        normalized['Dairy-Free'] = True
                    elif 'Eggs' in allergen:
                        normalized['Egg-Free'] = True
                    elif 'Nuts' in allergen or 'Peanuts' in allergen:
                        normalized['Nut-Free'] = True
                    elif 'Soya' in allergen or 'Soy' in allergen:
                        normalized['Soy-Free'] = True
                    elif 'Fish' in allergen:
                        pass  # Could add fish-free flag
                    elif 'Shellfish' in allergen or 'Crustaceans' in allergen:
                        normalized['Shellfish-Free'] = True
                
                # Map certifications
                elif 'Genetically Modified' in info_str:
                    normalized['Non-GMO'] = True
                    if 'Non-GMO' not in certifications:
                        certifications.append('Non-GMO')
                elif 'Pack Type' in info_str:
                    normalized['Canned Food'] = False  # Not canned
            
            # Set allergens list if found
            if allergens:
                normalized['Allergens'] = allergens
            if certifications:
                normalized['Product Certifications'] = certifications
        
        # ===== DETECT PACKAGING TYPE =====
        packaging_type = self.normalizer.detect_packaging_type(original_name)
        if packaging_type:
            tags = normalized.get('Tags', []) or []
            if packaging_type not in tags:
                tags.append(packaging_type)
            normalized['Tags'] = tags
        
        # ===== EXTRACT DIETARY FLAGS FROM description_bullets =====
        description_bullets = raw_product.get('description_bullets', [])
        if isinstance(description_bullets, list):
            for bullet in description_bullets:
                bullet_str = str(bullet).lower()
                if 'vegan' in bullet_str:
                    normalized['Vegan'] = True
                elif 'vegetarian' in bullet_str:
                    normalized['Vegetarian'] = True
                elif 'gluten' in bullet_str and 'free' in bullet_str:
                    normalized['Gluten-Free'] = True
                elif 'organic' in bullet_str:
                    normalized['Organic'] = True
                elif 'gmo' in bullet_str and 'free' in bullet_str:
                    normalized['Non-GMO'] = True
                elif 'no preservatives' in bullet_str:
                    normalized['No Preservatives'] = True
                elif 'natural' in bullet_str:
                    normalized['Natural Ingredients'] = True
        
        return normalized
    
    def enrich_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 2: Apply inference engine to fill missing fields
        Includes description extraction
        """
        enriched = self.inferencer.apply_all_inferences(product)
        return enriched
    
    def add_source_metadata(self, product: Dict[str, Any], 
                          source_name: str, source_url: str) -> Dict[str, Any]:
        """Stage 3: Add source tracking fields to product"""
        product['Source Website Name'] = source_name
        product['Source Website URL'] = source_url
        product['Scraped At'] = datetime.now().isoformat()
        
        # Ensure Product ID exists
        if not product.get('Product ID'):
            # Generate from source + timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            source_prefix = ''.join(filter(str.isalnum, source_name.lower()))[:3]
            product['Product ID'] = f"{source_prefix}_{timestamp}"
        
        return product
    
    def enforce_schema(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 4: Ensure product strictly follows schema
        - All fields present in exact order
        - Missing fields set to null
        - No extra fields
        """
        schema_compliant = {}
        
        for field in self.schema:
            value = product.get(field)
            schema_compliant[field] = value
        
        return schema_compliant
    
    def process_product(self, raw_product: Dict[str, Any], 
                       source_name: str, source_url: str) -> Optional[Dict[str, Any]]:
        """
        Complete processing pipeline for a single product:
        1. Clean & Normalize
        2. Enrich/Infer
        3. Add source metadata
        4. Enforce schema
        """
        # Validation: Skip products with null id or name
        product_id = raw_product.get('product_id') or raw_product.get('id') or raw_product.get('Product ID')
        product_name = raw_product.get('name') or raw_product.get('Product Name')
        
        if not product_id or not product_name:
            return None
        
        if str(product_name).upper() in ['N/A', 'NA', 'NONE', 'NULL']:
            return None
        
        # Stage 1: Clean and Normalize
        normalized = self.clean_and_normalize_product(raw_product)
        
        # Stage 2: Enrich
        enriched = self.enrich_product(normalized)
        
        # Stage 3: Add source metadata
        with_metadata = self.add_source_metadata(enriched, source_name, source_url)
        
        # Stage 4: Enforce schema
        final = self.enforce_schema(with_metadata)
        
        return final
    
    def process_batch(self, raw_products: List[Dict[str, Any]], 
                     source_name: str, source_url: str) -> List[Dict[str, Any]]:
        """Process multiple products from a single source"""
        processed = []
        skipped = 0
        
        for raw_product in raw_products:
            try:
                clean_product = self.process_product(raw_product, source_name, source_url)
                if clean_product:
                    processed.append(clean_product)
                else:
                    skipped += 1
            except Exception as e:
                print(f"⚠️  Error processing product: {e}")
                skipped += 1
                continue
        
        if skipped > 0:
            print(f"⚠️  Skipped {skipped} products (null id/name or errors)")
        
        return processed
    
    def process_file(self, input_file: str, source_name: str, 
                    source_url: str) -> List[Dict[str, Any]]:
        """
        Process an entire scraped data file
        """
        print(f"\n🧹 Processing {input_file} from {source_name}...")
        
        # Load raw data
        raw_products = self.load_raw_products(input_file)
        print(f"   Loaded {len(raw_products)} raw products")
        
        # Process batch
        processed = self.process_batch(raw_products, source_name, source_url)
        print(f"   ✓ Successfully processed {len(processed)} products")
        
        return processed
    
    def merge_multiple_sources(self, source_configs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Process and merge products from multiple sources
        """
        all_products = []
        
        for config in source_configs:
            try:
                products = self.process_file(
                    config['file'],
                    config['name'],
                    config['url']
                )
                all_products.extend(products)
            except Exception as e:
                print(f"⚠️  Error processing {config['file']}: {e}")
                continue
        
        print(f"\n✓ Total products merged: {len(all_products)}")
        
        # Save learned brands
        self.brand_detector.save_if_dirty()
        
        return all_products
    
    def save_master_json(self, products: List[Dict[str, Any]], 
                        output_file: str = 'master_products.json'):
        """Save processed products to master JSON file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(products, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Master JSON saved to: {output_path}")
        print(f"   Total products: {len(products)}")
        
        # Print statistics
        self._print_statistics(products)
    
    def _print_statistics(self, products: List[Dict[str, Any]]):
        """Print data quality statistics"""
        if not products:
            return
        
        total = len(products)
        
        # Count filled fields
        filled_counts = {field: 0 for field in self.schema}
        
        for product in products:
            for field, value in product.items():
                if value is not None and value != '':
                    if isinstance(value, list) and len(value) == 0:
                        continue
                    filled_counts[field] += 1
        
        print("\n" + "="*60)
        print("DATA QUALITY STATISTICS")
        print("="*60)
        print(f"Total Products: {total}")
        
        # Overall completeness
        total_possible = total * len(self.schema)
        total_filled = sum(filled_counts.values())
        completeness = (total_filled / total_possible) * 100
        print(f"Overall Completeness: {completeness:.1f}%")
        
        # Top filled fields
        print("\nTop 15 Most Complete Fields:")
        sorted_fields = sorted(filled_counts.items(), 
                             key=lambda x: x[1], reverse=True)[:15]
        for field, count in sorted_fields:
            pct = (count / total) * 100
            print(f"  {field}: {pct:.1f}% ({count}/{total})")
        
        # Source distribution
        sources = {}
        for product in products:
            source = product.get('Source Website Name', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print("\nProducts by Source:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")
        
        # Brand detection statistics
        branded = sum(1 for p in products if p.get('Brand'))
        print(f"\nBrand Detection: {branded}/{total} ({(branded/total)*100:.1f}%)")
        print(f"Known Brands: {self.brand_detector.get_brand_count()}")


# Convenience function
def clean_and_merge(source_configs: List[Dict[str, str]], 
                   output_file: str = 'master_products.json',
                   brands_file: Optional[str] = None):
    """
    One-liner to clean and merge multiple data sources
    
    Example:
        clean_and_merge([
            {'file': 'amazon.json', 'name': 'Amazon', 'url': 'https://amazon.com'},
            {'file': 'walmart.json', 'name': 'Walmart', 'url': 'https://walmart.com'}
        ])
    """
    cleaner = IntegratedProductCleaner(brands_file)
    products = cleaner.merge_multiple_sources(source_configs)
    cleaner.save_master_json(products, output_file)
    return products