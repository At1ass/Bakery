from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderItem(BaseModel):
    product_id: str = Field(..., description="The ID of the product")
    product_name: Optional[str] = Field(None, description="Name of the product")
    quantity: int = Field(..., gt=0, description="The quantity of the product")
    unit_price: Optional[Decimal] = Field(None, gt=0, description="Price per unit")
    total_price: Optional[Decimal] = Field(None, gt=0, description="Total price for this item")

    @validator('unit_price', 'total_price', pre=True)
    def validate_price(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v

class Order(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    items: List[OrderItem] = Field(..., min_items=1, description="List of items in the order")
    total: Optional[Decimal] = Field(None, gt=0, description="Total order amount")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Current order status")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes for the order")
    delivery_address: Optional[str] = Field(None, max_length=500, description="Delivery address")
    
    @validator('total', pre=True)
    def validate_total(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
