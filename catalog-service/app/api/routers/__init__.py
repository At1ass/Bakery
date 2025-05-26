from .products import router as products_router
from .health import router as health_router
from .categories import router as categories_router
from .tags import router as tags_router

__all__ = ["products_router", "health_router", "categories_router", "tags_router"]
