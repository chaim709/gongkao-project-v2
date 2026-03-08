from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.logging import get_logger
import time

logger = get_logger("request")


SLOW_REQUEST_MS = 1000  # 超过1秒视为慢请求


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 2)

        # 跳过健康检查和静态文件
        path = request.url.path
        if path in ("/health", "/") or path.startswith("/uploads"):
            return response

        log_data = dict(
            method=request.method,
            path=path,
            status=response.status_code,
            duration_ms=duration,
            client=request.client.host if request.client else None,
        )

        if duration > SLOW_REQUEST_MS:
            logger.warning("slow_request", **log_data)
        else:
            logger.info("request", **log_data)

        return response
