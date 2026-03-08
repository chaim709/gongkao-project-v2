"""API 限流中间件：基于 IP + 路径的简单限流"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from collections import defaultdict
import time


class RateLimitMiddleware(BaseHTTPMiddleware):
    """滑动窗口限流器"""

    def __init__(self, app, default_limit: int = 60, window: int = 60, strict_paths: dict = None):
        """
        default_limit: 默认每个窗口期最大请求数
        window: 窗口期（秒）
        strict_paths: 需要严格限流的路径 {路径前缀: (limit, window)}
        """
        super().__init__(app)
        self.default_limit = default_limit
        self.window = window
        self.strict_paths = strict_paths or {
            "/api/v1/auth/login": (5, 60),       # 登录：每分钟最多5次
            "/api/v1/students/batch": (3, 60),    # 批量操作：每分钟3次
            "/api/v1/export": (5, 60),            # 导出：每分钟5次
        }
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 每5分钟清理一次

    def _cleanup_stale_keys(self, now: float):
        """清理过期的键，防止内存无限增长"""
        stale_keys = [
            key for key, timestamps in self.requests.items()
            if not timestamps or (now - timestamps[-1]) > self.window
        ]
        for key in stale_keys:
            del self.requests[key]
        self._last_cleanup = now

    async def dispatch(self, request: Request, call_next):
        # 跳过非 API 请求
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.time()

        # 定期清理过期键
        if now - self._last_cleanup > self._cleanup_interval:
            self._cleanup_stale_keys(now)

        # 确定限流参数
        limit, window = self.default_limit, self.window
        for prefix, (plimit, pwindow) in self.strict_paths.items():
            if path.startswith(prefix):
                limit, window = plimit, pwindow
                break

        key = f"{client_ip}:{path}"

        # 清理过期记录
        self.requests[key] = [t for t in self.requests[key] if now - t < window]

        if len(self.requests[key]) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
                headers={"Retry-After": str(window)},
            )

        self.requests[key].append(now)
        return await call_next(request)
