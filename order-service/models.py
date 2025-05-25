from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OrderItem(BaseModel):
    product_id: str = Field(..., description="The ID of the product")
    quantity: int = Field(..., gt=0, description="The quantity of the product")

class Order(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    items: List[OrderItem] = Field(..., min_items=1, description="List of items in the order")
    total: Optional[float] = None
    status: str = Field(default="pending", pattern="^(pending|completed|cancelled)$")
    created_at: datetime = Field(default_factory=datetime.now)
