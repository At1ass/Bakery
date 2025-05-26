from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from ..models.order import OrderStatus


class OrderItemResponse(BaseModel):
    """Response model for order items"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Response model for a single order"""
    id: str = Field(..., description="Order ID")
    user_id: str = Field(..., description="User ID")
    items: List[OrderItemResponse] = Field(..., description="Order items")
    total: Decimal = Field(..., description="Total order amount")
    status: OrderStatus = Field(..., description="Order status")
    delivery_address: str = Field(..., description="Delivery address")
    contact_phone: str = Field(..., description="Contact phone")
    delivery_notes: Optional[str] = Field(None, description="Delivery notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery time")


class OrderListResponse(BaseModel):
    """Response model for order list with pagination"""
    orders: List[OrderResponse] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders")
    skip: int = Field(..., description="Number of orders skipped")
    limit: int = Field(..., description="Number of orders returned")
    has_more: bool = Field(..., description="Whether there are more orders")


class OrderCreateResponse(BaseModel):
    """Response model for order creation"""
    message: str = Field(..., description="Success message")
    order: OrderResponse = Field(..., description="Created order")


class OrderUpdateResponse(BaseModel):
    """Response model for order updates"""
    message: str = Field(..., description="Success message")
    order: OrderResponse = Field(..., description="Updated order")


class OrderDeleteResponse(BaseModel):
    """Response model for order deletion"""
    message: str = Field(..., description="Success message")


class OrderStatusUpdateRequest(BaseModel):
    """Request model for order status updates"""
    status: OrderStatus = Field(..., description="New order status")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment")
    timestamp: datetime = Field(..., description="Response timestamp") 