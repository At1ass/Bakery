from fastapi import Depends, Query, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.security import verify_token
from ..models.order import OrderStatus


async def get_current_user(user_data: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
    """Get current authenticated user"""
    return user_data


async def get_current_user_id(user_data: Dict[str, Any] = Depends(get_current_user)) -> str:
    """Get current user ID"""
    return user_data["user_id"]


async def get_current_user_role(user_data: Dict[str, Any] = Depends(get_current_user)) -> str:
    """Get current user role"""
    return user_data.get("role", "Customer")


async def is_seller_or_admin(user_data: Dict[str, Any] = Depends(get_current_user)) -> bool:
    """Check if current user is a seller or admin"""
    role = user_data.get("role", "Customer")
    return role in ["Seller", "Admin"]


def get_pagination_params(
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of orders to return")
) -> Dict[str, int]:
    """Get pagination parameters with validation"""
    return {"skip": skip, "limit": limit}


def get_order_filters(
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    from_date: Optional[datetime] = Query(None, description="Filter orders from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter orders until this date"),
    min_total: Optional[float] = Query(None, ge=0, description="Minimum order total"),
    max_total: Optional[float] = Query(None, ge=0, description="Maximum order total")
) -> Dict[str, Any]:
    """Get order filtering parameters with validation"""
    
    # Validate date range
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date cannot be later than to_date"
        )
    
    # Validate total range
    if min_total is not None and max_total is not None and min_total > max_total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_total cannot be greater than max_total"
        )
    
    return {
        "order_status": status,
        "from_date": from_date,
        "to_date": to_date,
        "min_total": min_total,
        "max_total": max_total
    } 