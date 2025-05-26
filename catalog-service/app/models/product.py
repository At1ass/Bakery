from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict
from typing import List, Optional, Union, Annotated
from decimal import Decimal
import re
from datetime import datetime

from .ingredient import Ingredient


class Product(BaseModel):
    """Model for product objects"""
    id: Optional[str] = Field(None, description="Product ID")
    name: Annotated[str, Field(min_length=1, max_length=100, description="Product name")]
    description: Annotated[str, Field(min_length=1, max_length=500, description="Product description")]
    price: Decimal = Field(..., gt=0, lt=10000, description="Product price (must be greater than 0 and less than 10000)")
    category: str = Field(..., description="Product category")
    tags: List[Annotated[str, Field(min_length=1, max_length=30)]] = Field(
        default_factory=list,
        description="Product tags",
        max_length=10
    )
    image_url: Optional[HttpUrl] = Field(None, description="URL to product image")
    recipe: List[Ingredient] = Field(default_factory=list, description="List of ingredients in the recipe")
    is_available: bool = Field(default=True, description="Whether the product is available")
    created_by: Optional[str] = Field(None, description="User ID who created the product")
    created_at: Optional[Union[datetime, str]] = Field(None, description="Creation timestamp")
    updated_at: Optional[Union[datetime, str]] = Field(None, description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="User ID who last updated the product")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Chocolate Cake",
                "description": "Rich chocolate cake with ganache",
                "price": 29.99,
                "category": "Cakes",
                "tags": ["chocolate", "cake", "dessert"],
                "image_url": "https://example.com/chocolate-cake.jpg",
                "recipe": [
                    {"ingredient": "flour", "quantity": 2.5, "unit": "cups"},
                    {"ingredient": "cocoa", "quantity": 0.75, "unit": "cups"},
                    {"ingredient": "sugar", "quantity": 2.0, "unit": "cups"}
                ],
                "is_available": True
            }
        }
    )

    @field_validator('name')
    @classmethod
    def name_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        if not re.match(r'^[\w\s\-\']+$', v):
            raise ValueError('Name can only contain letters, numbers, spaces, hyphens, and apostrophes')
        return v.strip()

    @field_validator('description')
    @classmethod
    def description_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty")
        if not re.match(r'^[\w\s\-\',\.\!\?]+$', v):
            raise ValueError('Description contains invalid characters')
        return v.strip()

    @field_validator('category')
    @classmethod
    def category_must_be_valid(cls, v):
        valid_categories = {
            'Cakes', 'Cupcakes', 'Cookies', 'Pastries', 'Breads',
            'Pies', 'Donuts', 'Chocolates', 'Ice Cream', 'Other'
        }
        if v not in valid_categories:
            raise ValueError(f'Invalid category. Must be one of: {", ".join(sorted(valid_categories))}')
        return v

    @field_validator('tags')
    @classmethod
    def tags_must_be_valid(cls, v):
        if not v:  # If tags is empty, return default list
            return ['uncategorized']
        
        # Remove duplicates while preserving order
        seen = set()
        v = [x for x in v if not (x.lower() in seen or seen.add(x.lower()))]
        
        # Validate each tag
        for tag in v:
            if not tag.strip():
                raise ValueError("Tag cannot be empty")
            if not re.match(r'^[\w\-]+$', tag):
                raise ValueError(f'Tag "{tag}" can only contain letters, numbers, and hyphens')
        
        return v

    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        # Round to 2 decimal places and convert to float
        try:
            return float(round(v, 2))
        except Exception:
            raise ValueError("Price must be a valid decimal number") 