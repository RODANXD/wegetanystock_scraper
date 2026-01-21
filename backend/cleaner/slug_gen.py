import re
from typing import Optional
import unicodedata


class SlugGenerator:
    """Generates SEO-friendly slugs"""

    CHAR_REPLACEMENTS = {
        '&': 'and',
        '+': 'plus',
        '@': 'at',
        '%': 'percent',
        '#': 'number',
        '£': '',
        '$': '',
        '€': '',
        '™': '',
        '®': '',
        '©': '',
    }
    
    def __init__(self, max_length: int = 100):
        self.max_length = max_length
    
    def generate(self, text: str, preserve_numbers: bool = True) -> str:
        """
        Generate SEO-friendly slug from text
        
        Args:
            text: Input text to convert
            preserve_numbers: Keep numbers in the slug
            
        Returns:
            URL-friendly slug string
        """
        if not text:
            return ""
        
        slug = text
        
        # Convert to lowercase
        slug = slug.lower()
        
        # Replace special characters
        for char, replacement in self.CHAR_REPLACEMENTS.items():
            slug = slug.replace(char, f' {replacement} ' if replacement else ' ')
        
        # Normalize unicode characters (é → e, etc.)
        slug = unicodedata.normalize('NFKD', slug)
        slug = slug.encode('ascii', 'ignore').decode('ascii')
        
        # Keep only alphanumeric, spaces, and hyphens
        if preserve_numbers:
            slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        else:
            slug = re.sub(r'[^a-z\s-]', '', slug)
        
        # Replace whitespace with hyphens
        slug = re.sub(r'\s+', '-', slug)
        
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        if len(slug) > self.max_length:
            slug = slug[:self.max_length]
            
            last_hyphen = slug.rfind('-')
            if last_hyphen > self.max_length // 2:
                slug = slug[:last_hyphen]
        
        return slug
    
    def generate_unique(self, text: str, existing_slugs: set) -> str:
        """
        Generate unique slug by appending number if needed
        
        Args:
            text: Input text
            existing_slugs: Set of existing slugs to avoid collision
            
        Returns:
            Unique slug string
        """
        base_slug = self.generate(text)
        
        if base_slug not in existing_slugs:
            return base_slug
        
       
        counter = 1
        while True:
            unique_slug = f"{base_slug}-{counter}"
            if unique_slug not in existing_slugs:
                return unique_slug
            counter += 1
    
    def generate_from_product(self, name: str, brand: Optional[str] = None, size: Optional[str] = None) -> str:
        """
        Generate slug from product name, brand, and size
        
        Args:
            name: Product name
            brand: Product brand
            size: Product size
        
        Returns:
            URL-friendly slug string
        """
        parts = []
        
        if brand:
            parts.append(brand)
        
        parts.append(name)
        
        if size:
            parts.append(size)
        
        full_text = ' '.join(parts)
        return self.generate(full_text)


# Singleton instance
slug_generator = SlugGenerator()
