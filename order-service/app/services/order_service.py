import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from bson.objectid import ObjectId
from fastapi import HTTPException, status

from ..db.mongodb import get_orders_collection
from ..models.order import Order, OrderItem, OrderStatus
from ..services.external import catalog_service
from ..core.config import settings

logger = logging.getLogger(__name__)


def convert_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to API response format"""
    if doc and '_id' in doc:
        doc['id'] = str(doc['_id'])
        del doc['_id']
    return doc


def custom_json_encoder(obj):
    """Custom JSON encoder for MongoDB ObjectId and Decimal"""
    try:
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {key: custom_json_encoder(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [custom_json_encoder(item) for item in obj]
        return obj
    except Exception as e:
        logger.error(f"Error in custom_json_encoder: {str(e)}")
        raise


def convert_decimals_to_float(obj):
    """Recursively convert Decimal objects to float for MongoDB compatibility"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    else:
        return obj


def parse_object_id(id_str: str) -> ObjectId:
    """Parse string to ObjectId with validation"""
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID format"
        )


class OrderService:
    """Service class for order business logic"""
    
    def __init__(self):
        self.valid_status_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.COMPLETED],
            OrderStatus.COMPLETED: [],
            OrderStatus.CANCELLED: []
        }
    
    async def create_order(self, order_data: Order, user_id: str) -> Dict[str, Any]:
        """Create a new order with product validation and price calculation"""
        try:
            collection = await get_orders_collection()
            
            # Validate products and get their details
            product_ids = [item.product_id for item in order_data.items]
            products = await catalog_service.validate_products(product_ids)
            
            # Calculate prices and update items
            total_amount = Decimal('0.00')
            updated_items = []
            
            for item in order_data.items:
                product = products[item.product_id]
                
                # Check if product is available
                if not product.get('is_available', True):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product {product.get('name', item.product_id)} is not available"
                    )
                
                unit_price = Decimal(str(product['price']))
                item_total = unit_price * item.quantity
                total_amount += item_total
                
                # Update item with product details
                item.product_name = product['name']
                item.unit_price = unit_price
                item.total_price = item_total
                updated_items.append(item)
            
            # Create order document
            now = datetime.utcnow()
            estimated_delivery = now + timedelta(hours=2)  # 2 hours from now
            
            order_doc = {
                "user_id": user_id,
                "items": [convert_decimals_to_float(item.model_dump()) for item in updated_items],
                "total": float(total_amount),
                "status": order_data.status.value,
                "delivery_address": order_data.delivery_address,
                "contact_phone": order_data.contact_phone,
                "delivery_notes": order_data.delivery_notes,
                "created_at": now,
                "updated_at": now,
                "estimated_delivery": estimated_delivery
            }
            
            # Insert order
            result = await collection.insert_one(order_doc)
            
            # Fetch the created order
            created_order = await collection.find_one({"_id": result.inserted_id})
            
            # Convert MongoDB document to API format
            created_order = convert_mongo_doc(created_order)
            
            return json.loads(json.dumps(created_order, default=custom_json_encoder))
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order"
            )
    
    async def get_orders(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
        order_status: Optional[OrderStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        min_total: Optional[float] = None,
        max_total: Optional[float] = None,
        get_all_orders: bool = False
    ) -> Dict[str, Any]:
        """Get orders for a user with filtering and pagination
        
        Args:
            user_id: User ID to filter orders by (ignored if get_all_orders=True)
            skip: Number of orders to skip for pagination
            limit: Maximum number of orders to return
            order_status: Filter by order status
            from_date: Filter orders from this date
            to_date: Filter orders until this date
            min_total: Minimum order total
            max_total: Maximum order total
            get_all_orders: If True, return all orders regardless of user_id (for sellers/admins)
        """
        try:
            collection = await get_orders_collection()
            
            # Build filter query
            filter_query = {}
            
            # Only filter by user_id if not getting all orders
            if not get_all_orders:
                filter_query["user_id"] = user_id
            
            if order_status:
                filter_query["status"] = order_status.value
            
            if from_date or to_date:
                date_filter = {}
                if from_date:
                    date_filter["$gte"] = from_date
                if to_date:
                    date_filter["$lte"] = to_date
                filter_query["created_at"] = date_filter
            
            if min_total is not None or max_total is not None:
                total_filter = {}
                if min_total is not None:
                    total_filter["$gte"] = min_total
                if max_total is not None:
                    total_filter["$lte"] = max_total
                filter_query["total"] = total_filter
            
            # Get total count
            total_count = await collection.count_documents(filter_query)
            
            # Get orders with pagination
            cursor = collection.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
            orders = []
            
            async for order in cursor:
                orders.append(json.loads(json.dumps(convert_mongo_doc(order), default=custom_json_encoder)))
            
            return {
                "orders": orders,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "has_more": skip + len(orders) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error fetching orders: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch orders"
            )
    
    async def get_order_by_id(self, order_id: str, user_id: str) -> Dict[str, Any]:
        """Get a specific order by ID"""
        try:
            collection = await get_orders_collection()
            object_id = parse_object_id(order_id)
            
            order = await collection.find_one({"_id": object_id, "user_id": user_id})
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            return json.loads(json.dumps(convert_mongo_doc(order), default=custom_json_encoder))
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch order"
            )
    
    async def update_order_status(self, order_id: str, new_status: OrderStatus, user_id: str) -> Dict[str, Any]:
        """Update order status with validation"""
        try:
            collection = await get_orders_collection()
            object_id = parse_object_id(order_id)
            
            # Get current order
            order = await collection.find_one({"_id": object_id, "user_id": user_id})
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            current_status = OrderStatus(order["status"])
            
            # Validate status transition
            if not self.is_valid_status_transition(current_status, new_status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot change order status from {current_status.value} to {new_status.value}"
                )
            
            # Update order
            update_data = {
                "status": new_status.value,
                "updated_at": datetime.utcnow()
            }
            
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order status was not updated"
                )
            
            # Fetch updated order
            updated_order = await collection.find_one({"_id": object_id})
            
            return json.loads(json.dumps(convert_mongo_doc(updated_order), default=custom_json_encoder))
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating order status {order_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update order status"
            )
    
    async def cancel_order(self, order_id: str, user_id: str) -> bool:
        """Cancel an order"""
        try:
            collection = await get_orders_collection()
            object_id = parse_object_id(order_id)
            
            # Get current order
            order = await collection.find_one({"_id": object_id, "user_id": user_id})
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            current_status = OrderStatus(order["status"])
            
            # Check if order can be cancelled
            if current_status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot cancel order with status {current_status.value}"
                )
            
            # Update order status to cancelled
            result = await collection.update_one(
                {"_id": object_id},
                {"$set": {
                    "status": OrderStatus.CANCELLED.value,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return result.modified_count > 0
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel order"
            )
    
    def is_valid_status_transition(self, current: OrderStatus, new: OrderStatus) -> bool:
        """Check if status transition is valid"""
        return new in self.valid_status_transitions.get(current, [])


# Service instance
order_service = OrderService() 