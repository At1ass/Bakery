from pydantic import BaseModel, Field, constr, validator, HttpUrl
from typing import List, Optional
from decimal import Decimal
import re

class Ingredient(BaseModel):
    ingredient: constr(min_length=1, max_length=100) = Field(..., description="Ingredient name")
    quantity: Decimal = Field(..., gt=0, description="Quantity of ingredient")
    unit: constr(min_length=1, max_length=20) = Field(..., description="Unit of measurement (e.g., g, ml, pcs)")

    @validator('unit')
    def validate_unit(cls, v):
        valid_units = {'g', 'kg', 'ml', 'l', 'pcs', 'tsp', 'tbsp', 'cups', 'oz', 'lbs'}
        if v.lower() not in valid_units:
            raise ValueError(f'Invalid unit. Must be one of: {", ".join(sorted(valid_units))}')
        return v.lower()

class Product(BaseModel):
    id: Optional[str] = Field(None, description="Product ID")
    name: constr(min_length=1, max_length=100) = Field(..., description="Product name")
    description: constr(min_length=1, max_length=500) = Field(..., description="Product description")
    price: Decimal = Field(..., gt=0, lt=10000, description="Product price (must be greater than 0 and less than 10000)")
    category: constr(min_length=1, max_length=50) = Field(..., description="Product category")
    tags: List[constr(min_length=1, max_length=30)] = Field(
        default_factory=list,
        description="Product tags",
        max_items=10
    )
    image_url: Optional[HttpUrl] = Field(None, description="URL to product image")
    recipe: List[Ingredient] = Field(default_factory=list, description="List of ingredients in the recipe")
    is_available: bool = Field(default=True, description="Whether the product is available")
    created_by: Optional[str] = Field(None, description="User ID who created the product")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

    @validator('name')
    def name_must_be_valid(cls, v):
        if not re.match(r'^[\w\s\-\']+$', v):
            raise ValueError('Name can only contain letters, numbers, spaces, hyphens, and apostrophes')
        return v.strip()

    @validator('description')
    def description_must_be_valid(cls, v):
        if not re.match(r'^[\w\s\-\',\.\!\?]+$', v):
            raise ValueError('Description contains invalid characters')
        return v.strip()

    @validator('category')
    def category_must_be_valid(cls, v):
        valid_categories = {
            'Cakes', 'Cupcakes', 'Cookies', 'Pastries', 'Breads',
            'Pies', 'Donuts', 'Chocolates', 'Ice Cream', 'Other'
        }
        if v not in valid_categories:
            raise ValueError(f'Invalid category. Must be one of: {", ".join(sorted(valid_categories))}')
        return v

    @validator('tags')
    def tags_must_be_valid(cls, v):
        if not v:  # If tags is empty, return default list
            return ['uncategorized']
        
        # Remove duplicates while preserving order
        seen = set()
        v = [x for x in v if not (x.lower() in seen or seen.add(x.lower()))]
        
        # Validate each tag
        for tag in v:
            if not re.match(r'^[\w\-]+$', tag):
                raise ValueError(f'Tag "{tag}" can only contain letters, numbers, and hyphens')
        
        return v

    @validator('price')
    def validate_price(cls, v):
        # Round to 2 decimal places
        return round(v, 2)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "name": "Chocolate Cake",
                "description": "Rich chocolate cake with ganache",
                "price": "29.99",
                "category": "Cakes",
                "tags": ["chocolate", "cake", "dessert"],
                "image_url": "https://example.com/chocolate-cake.jpg",
                "recipe": [
                    {"ingredient": "flour", "quantity": "2.5", "unit": "cups"},
                    {"ingredient": "cocoa", "quantity": "0.75", "unit": "cups"},
                    {"ingredient": "sugar", "quantity": "2.0", "unit": "cups"}
                ],
                "is_available": True
            }
        }
