# 🏗️ Product Scraping Pipeline - Integrated Architecture

## Overview

The pipeline follows a three-phase approach for reliable and standardized product data collection:

```
Scrapers (Simple) → Raw JSON Files → Central Cleaner (Smart) → Master JSON (Standardized)
```

## Phase 1: Data Collection (Scrapers)

### Bestway Wholesale Scraper (`bestwayScraper.py`)
- **Source**: https://www.bestwaywholesale.co.uk/grocery
- **Output**: `data/bestwayraw_products.json` (Raw data, unmodified from scraper)
- **Process**: 
  1. Scrapes product listings with pagination
  2. Extracts: ID, name, price, category, image URL, SKU
  3. Fetches detailed info from product pages
  4. Saves raw JSON immediately

### Laxmi Wholesale Scraper (`laxmiScraper.py`)
- **Source**: https://www.lakshmiwholesale.com
- **Output**: `all_products.json` (Raw data from navigation scraping)
- **Process**:
  1. Navigates category/subcategory structure
  2. Extracts: Name, brand, price, category, image
  3. Optionally fetches detailed info per product
  4. Saves raw JSON before cleaning

## Phase 2: Central Cleaning & Normalization

### IntegratedProductCleaner (`cleaner_intergated.py`)

The heart of the pipeline - combines multiple cleaning operations:

#### 1. **Product Name Cleaning** (NormalizationEngine)
- Removes price marks (PMP £1.25, £3.99, etc.)
- Removes packaging descriptors (single, new, special edition)
- Extracts package size/weight
- Standardizes casing and units
- Result: Clean, standardized product names

#### 2. **Brand Detection** (BrandDetector)
- Auto-learns brands from product names
- Maintains `brands.json` database
- Supports brand name variations
- Detects multiple brands in one product
- Result: Standardized brand names with variations

#### 3. **Field Normalization**
- Converts all fields to schema format
- Type enforcement (text, numeric, boolean, list)
- Unit standardization (ml, g, kg, l, etc.)
- URL validation
- Category mapping
- Result: Normalized field values

#### 4. **Smart Inference** (EnhancedInferenceEngine)
- Extracts nutritional info from descriptions
- Identifies allergens
- Detects certifications (organic, vegan, etc.)
- Extracts ingredients lists
- Extracts storage instructions
- Result: Rich, extracted metadata

#### 5. **Schema Enforcement**
- Ensures all 130+ fields present
- Applies consistent field ordering
- Type validation
- Missing value handling
- Result: Standardized product objects

## Phase 3: Master Output

### Master JSON (`master_products_TIMESTAMP.json`)

Output combines products from all sources with:
- **Standardized fields**: 130+ fields following master schema
- **Source tracking**: Source website name and URL
- **Scraped timestamp**: When data was collected
- **Cleaned timestamp**: When data was standardized
- **Normalized metadata**: Brands, categories, certifications

## File Structure

```
backend/
├── scraper/
│   ├── bestwayScraper.py          # Phase 1: Bestway scraper
│   ├── laxmiScraper.py            # Phase 1: Laxmi scraper
│   ├── scraper_runner.py          # Orchestrator (NEW)
│   └── data/
│       ├── bestwayraw_products.json  # Raw from Bestway
│       └── ...
│
├── cleaner/
│   ├── cleaner_intergated.py      # Phase 2: Central cleaner
│   ├── normalization.py           # Text normalization
│   ├── brand_detector.py          # Brand detection & learning
│   ├── schema.py                  # Master schema definition
│   ├── infrence.py                # Inference engine
│   └── data/
│       └── brands.json            # Auto-learned brands
│
└── data/
    ├── master_products_20260130_143022.json  # Final output
    ├── bestwayraw_products.json
    ├── clean_laxmi.json
    └── ...
```

## Usage

### Run Individual Scrapers

**Bestway:**
```bash
python scraper/bestwayScraper.py
```

**Laxmi:**
```bash
python scraper/laxmiScraper.py
```

### Run Complete Pipeline

```bash
python scraper/scraper_runner.py --all --merge --output ./data
```

**Options:**
- `--bestway`: Run only Bestway scraper
- `--laxmi`: Run only Laxmi scraper  
- `--all`: Run all scrapers (default)
- `--merge`: Merge and standardize results (default: True)
- `--output`: Output directory (default: ./data)

### Merge Existing Raw Data

```bash
python scraper/scraper_runner.py --merge --output ./data
```

## Master Schema (130+ Fields)

### Product Identification
- Product ID
- Product Name
- Brand
- Barcode (EAN/UPC)

### Description & Content
- Short Description
- Long Description
- Ingredients List
- Storage Instructions
- Country of Origin

### Physical Properties
- Package Size
- Quantity
- Net Weight
- Volume for Liquids
- Color
- Packaging Type

### Nutritional Information (per 100g/serving)
- Calories, Total Fat, Saturated Fat, Cholesterol
- Sodium, Carbohydrates, Dietary Fiber, Sugars
- Protein, Water Content

### Vitamins & Minerals
- Vitamin A, C, D, E, K
- B-Complex (B1, B2, B3, B5, B6, B7, B9, B12)
- Calcium, Iron, Magnesium, Phosphorus
- Potassium, Zinc, Copper, Manganese, Selenium

### Health Properties (Boolean)
- Vegan, Vegetarian
- Gluten-Free, Dairy-Free, Soy-Free, Nut-Free
- Kosher, Halal, Organic, Non-GMO
- Keto-Friendly, Low-Carb, High-Protein
- Heart Healthy, Diabetes-Friendly

### Allergens (Flags)
- Contains Peanuts, Tree Nuts, Milk, Eggs, Wheat
- Contains Soy, Fish, Shellfish, Sesame

### Images
- Featured Image URL
- Gallery Image URLs

### Metadata
- Source Website Name
- Source Website URL
- Scraped At (timestamp)
- Cleaned At (timestamp)

## Data Quality

### Cleaning Quality
- Price marks removed from names
- Packaging info extracted separately
- Units standardized (ml, g, kg, etc.)
- Brand names normalized
- Casing standardized (Title Case)

### Schema Compliance
- All 130+ fields present
- Consistent field types
- Null values handled appropriately
- No duplicate products (by content hash)

### Source Tracking
- Every product linked to source
- Timestamp on all operations
- No data loss, only enhancement

## Example Flow

```python
# 1. Scraper produces raw JSON
{
    "name": "Nescafe Cappuccino Unsweetened PMP £3.99 7 x 14.2g",
    "price": "£3.99",
    "brand": "Nescafé",
    "image": "https://...",
    "category": "Beverages",
    "description": "Ingredients: Coffee, sugar, milk. Energy 45kcal"
}

# 2. IntegratedProductCleaner processes it
- Extracts: "Nescafe Cappuccino Unsweetened" (name)
- Detects: "Nescafé" (brand) → learns variation
- Extracts: "7 x 14.2g" → Package Size field
- Infers: 45kcal from description
- Infers: Contains Milk (allergen) from ingredients
- Adds: Source metadata, timestamps

# 3. Master product follows schema
{
    "Product ID": "...",
    "Product Name": "Nescafé Cappuccino Unsweetened",
    "Brand": "Nescafé",
    "Category": "Beverages",
    ...
    "Package Size": "7 x 14.2g",
    "Calories (kcal)": 45,
    "Contains Milk": true,
    "Ingredients List": "Coffee, sugar, milk",
    "Source Website Name": "Lakshmi Wholesale",
    "Source Website URL": "https://www.lakshmiwholesale.com",
    "Scraped At": "2026-01-30T14:30:22Z",
    "Cleaned At": "2026-01-30T14:35:45Z"
}
```

## Key Features

✅ **Automatic Brand Learning**: Discovers new brands and saves to database
✅ **Smart Name Cleaning**: Removes noise, extracts key info
✅ **Rich Inference**: Extracts nutritional and allergen data
✅ **Flexible Input**: Handles flat and nested JSON structures
✅ **Multi-Source**: Merges data from multiple websites
✅ **Schema Standardization**: Enforces 130+ field standard
✅ **Traceable**: Every product has source and timestamp
✅ **Extensible**: Easy to add new cleaners and inferrers

## Future Enhancements

- [ ] Machine learning for field mapping
- [ ] Image deduplication across sources
- [ ] Price history tracking
- [ ] Product matching (same product, different source)
- [ ] Duplicate detection
- [ ] Quality scoring per product
- [ ] Advanced allergen inference from images
- [ ] Nutritional estimation from category
