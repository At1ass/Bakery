from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderItem(BaseModel):
    product_id: str
    quantity: int

class Order(BaseModel):
    id: Optional[str]
    user_id: Optional[str]
    user_email: Optional[str]
    items: List[OrderItem]
    total: Optional[float]
    status: str = "pending"  # pending, completed, cancelled
    created_at: datetime = datetime.now()
