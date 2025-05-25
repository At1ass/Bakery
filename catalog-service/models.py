from pydantic import BaseModel
from typing import List, Optional

class Ingredient(BaseModel):
    id: str
    name: str
    quantity: float

class Product(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    price: float
    recipe: Optional[List[Ingredient]] = []
