import logging
import time
from fastapi import Request

logger = logging.getLogger(__name__)


async def log_requests_middleware(request: Request, call_next):
    """Middleware to log all incoming requests."""

    start_time = time.time()

    logger.info(f"{request.method} {request.url.path}")

    response = await call_next(request)

    process_time = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.3f}s"
    )

    response.headers["X-Process-Time"] = str(process_time)

    return response