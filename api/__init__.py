from .ages import router as age_router
from .config import router as config_router
from .premium import router as premium_router
from .sentry import router as sentry_router
from .status import router as status_router

__all__ = ["config_router", "age_router", "status_router", "sentry_router", "premium_router"]