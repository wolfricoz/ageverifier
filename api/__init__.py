from .config import router as config_router
from .ages import router as age_router
from .status import router as status_router

__all__ = ["config_router", "age_router", "status_router"]