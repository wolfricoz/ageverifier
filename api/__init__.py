from .config import router as config_router
from .ages import router as age_router
from .status import router as status_router
from .sentry import router as sentry_router

__all__ = ["config_router", "age_router", "status_router", "sentry_router"]