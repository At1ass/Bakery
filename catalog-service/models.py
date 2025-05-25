from pydantic import BaseModel, Field, constr, conlist
from typing import List, Optional
from decimal import Decimal

class Ingredient(BaseModel):
    id: str = Field(..., description="Ingredient ID")
    name: constr(min_length=1, max_length=100) = Field(..., description="Ingredient name")
    quantity: Decimal = Field(..., gt=0, description="Quantity of ingredient")
    unit: constr(min_length=1, max_length=20) = Field(..., description="Unit of measurement (e.g., g, ml, pcs)")

class Product(BaseModel):
    id: Optional[str] = Field(None, description="Product ID")
    name: constr(min_length=1, max_length=100) = Field(..., description="Product name")
    description: constr(min_length=1, max_length=500) = Field(..., description="Product description")
    price: Decimal = Field(..., gt=0, description="Product price")
    category: constr(min_length=1, max_length=50) = Field(..., description="Product category")
    tags: conlist(str, min_items=1, max_items=10) = Field(default_factory=list, description="Product tags")
    image_url: Optional[str] = Field(None, description="URL to product image")
    recipe: List[Ingredient] = Field(default_factory=list, description="List of ingredients in the recipe")
    is_available: bool = Field(default=True, description="Whether the product is available")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
