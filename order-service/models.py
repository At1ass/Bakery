from pydantic import BaseModel, Field, field_validator, StringConstraints, ConfigDict
from typing import List, Optional, Annotated, Union
from decimal import Decimal
from datetime import datetime
from enum import Enum
import re
from bson.objectid import ObjectId

class OrderStatus(str, Enum):
    """Order status enum representing the possible states of an order"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PyObjectId(str):
    """Custom type for handling MongoDB ObjectId, ensuring proper validation and serialization"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str) and not isinstance(v, ObjectId):
            raise ValueError("Not a valid ObjectId")
        return str(v)

class OrderItem(BaseModel):
    """Model representing an item in an order"""
    product_id: str = Field(..., description="Product ID")
    product_name: Optional[str] = Field(None, description="Product name (filled by server)")
    quantity: int = Field(..., gt=0, le=100, description="Quantity ordered")
    unit_price: Optional[Decimal] = Field(None, description="Unit price (filled by server)")
    total_price: Optional[Decimal] = Field(None, description="Total price for this item (filled by server)")
    notes: Optional[str] = Field(None, max_length=200, description="Special instructions for this item")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": "507f1f77bcf86cd799439011",
                "quantity": 2,
                "notes": "Extra frosting please"
            }
        }
    )

    @field_validator('product_id')
    def validate_product_id(cls, v):
        if not re.match(r'^[0-9a-fA-F]{24}$', v):
            raise ValueError('Invalid MongoDB ObjectId format. Must be a 24-character hex string.')
        return v

    @field_validator('notes')
    def validate_notes(cls, v):
        if v:
            if not re.match(r'^[\w\s\-\',\.\!\?]+$', v):
                raise ValueError('Notes contain invalid characters. Use only letters, numbers, spaces, and basic punctuation.')
            return v.strip()
        return v

class Order(BaseModel):
    """Model representing an order in the system"""
    id: Optional[PyObjectId] = Field(None, alias="_id", description="Order ID")
    user_id: Optional[str] = Field(None, description="User ID (filled by server)")
    items: List[OrderItem] = Field(..., min_items=1, max_items=50, description="List of ordered items")
    total: Optional[Decimal] = Field(None, description="Total order amount (filled by server)")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
    delivery_address: Annotated[str, StringConstraints(min_length=10, max_length=200)] = Field(
        ...,
        description="Delivery address"
    )
    contact_phone: Annotated[str, StringConstraints(pattern=r'^\+?1?\d{9,15}$')] = Field(
        ...,
        description="Contact phone number"
    )
    delivery_notes: Optional[str] = Field(None, max_length=200, description="Delivery instructions")
    created_at: Optional[datetime] = Field(None, description="Order creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery time")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "product_id": "507f1f77bcf86cd799439011",
                        "quantity": 2,
                        "notes": "Extra frosting please"
                    }
                ],
                "delivery_address": "123 Main St, Apt 4B, City, State 12345",
                "contact_phone": "+1234567890",
                "delivery_notes": "Please ring doorbell twice"
            }
        }
    )

    @field_validator('delivery_address')
    def validate_address(cls, v):
        if not re.match(r'^[\w\s\-\',\.\#\&]+$', v):
            raise ValueError('Address contains invalid characters. Use only letters, numbers, spaces, and basic punctuation.')
        return v.strip()

    @field_validator('delivery_notes')
    def validate_delivery_notes(cls, v):
        if v:
            if not re.match(r'^[\w\s\-\',\.\!\?]+$', v):
                raise ValueError('Delivery notes contain invalid characters. Use only letters, numbers, spaces, and basic punctuation.')
            return v.strip()
        return v

    @field_validator('items')
    def validate_items(cls, v):
        product_ids = set()
        for item in v:
            if item.product_id in product_ids:
                raise ValueError(f'Duplicate product ID: {item.product_id}. Each product should be added only once with the desired quantity.')
            product_ids.add(item.product_id)
        return v
