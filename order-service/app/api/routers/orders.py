from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, List
from datetime import datetime
import logging

from ...models.order import Order, OrderStatus
from ...schemas.order import (
    OrderResponse, OrderListResponse, OrderCreateResponse, 
    OrderUpdateResponse, OrderDeleteResponse, OrderStatusUpdateRequest
)
from ...services.order_service import order_service
from ...api.dependencies import (
    get_current_user_id, get_pagination_params, get_order_filters, is_seller_or_admin
)

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={
        404: {"description": "Order not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)


@router.post(
    "/",
    response_model=OrderCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order",
    description="Create a new order with product validation and automatic price calculation"
)
async def create_order(
    order_data: Order,
    user_id: str = Depends(get_current_user_id)
) -> OrderCreateResponse:
    """
    Create a new order:
    
    - **items**: List of products to order with quantities
    - **delivery_address**: Full delivery address
    - **contact_phone**: Contact phone number
    - **delivery_notes**: Optional delivery instructions
    
    The system will automatically:
    - Validate all products exist and are available
    - Calculate prices and totals
    - Set estimated delivery time
    """
    try:
        created_order = await order_service.create_order(order_data, user_id)
        
        return OrderCreateResponse(
            message="Order created successfully",
            order=OrderResponse(**created_order)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )


@router.get(
    "/",
    response_model=OrderListResponse,
    summary="Get user orders",
    description="Get orders for the authenticated user with filtering and pagination. Sellers and Admins see all orders."
)
async def get_orders(
    user_id: str = Depends(get_current_user_id),
    is_seller_admin: bool = Depends(is_seller_or_admin),
    pagination: Dict[str, int] = Depends(get_pagination_params),
    filters: Dict[str, Any] = Depends(get_order_filters)
) -> OrderListResponse:
    """
    Get orders with optional filtering:
    
    - **skip**: Number of orders to skip (pagination)
    - **limit**: Maximum number of orders to return (1-100)
    - **status**: Filter by order status
    - **from_date**: Filter orders from this date
    - **to_date**: Filter orders until this date
    - **min_total**: Minimum order total
    - **max_total**: Maximum order total
    
    Note: Sellers and Admins will see all orders from all customers.
    Customers will only see their own orders.
    """
    try:
        result = await order_service.get_orders(
            user_id=user_id,
            skip=pagination["skip"],
            limit=pagination["limit"],
            get_all_orders=is_seller_admin,
            **filters
        )
        
        orders = [OrderResponse(**order) for order in result["orders"]]
        
        return OrderListResponse(
            orders=orders,
            total=result["total"],
            skip=result["skip"],
            limit=result["limit"],
            has_more=result["has_more"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID",
    description="Get a specific order by its ID"
)
async def get_order(
    order_id: str = Path(..., description="Order ID", example="507f1f77bcf86cd799439011"),
    user_id: str = Depends(get_current_user_id)
) -> OrderResponse:
    """
    Get a specific order by ID.
    
    Only returns orders that belong to the authenticated user.
    """
    try:
        order = await order_service.get_order_by_id(order_id, user_id)
        return OrderResponse(**order)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order"
        )


@router.patch(
    "/{order_id}/status",
    response_model=OrderUpdateResponse,
    summary="Update order status",
    description="Update the status of an order with validation"
)
async def update_order_status(
    order_id: str = Path(..., description="Order ID", example="507f1f77bcf86cd799439011"),
    status_update: OrderStatusUpdateRequest = ...,
    user_id: str = Depends(get_current_user_id)
) -> OrderUpdateResponse:
    """
    Update order status with validation:
    
    Valid status transitions:
    - pending → confirmed, cancelled
    - confirmed → preparing, cancelled  
    - preparing → ready, cancelled
    - ready → completed
    - completed → (no transitions)
    - cancelled → (no transitions)
    """
    try:
        updated_order = await order_service.update_order_status(
            order_id, status_update.status, user_id
        )
        
        return OrderUpdateResponse(
            message=f"Order status updated to {status_update.status.value}",
            order=OrderResponse(**updated_order)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )


@router.delete(
    "/{order_id}/cancel",
    response_model=OrderDeleteResponse,
    summary="Cancel order",
    description="Cancel an order (sets status to cancelled)"
)
async def cancel_order(
    order_id: str = Path(..., description="Order ID", example="507f1f77bcf86cd799439011"),
    user_id: str = Depends(get_current_user_id)
) -> OrderDeleteResponse:
    """
    Cancel an order.
    
    Orders can only be cancelled if they are not already completed or cancelled.
    """
    try:
        success = await order_service.cancel_order(order_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order could not be cancelled"
            )
        
        return OrderDeleteResponse(
            message="Order cancelled successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        ) 