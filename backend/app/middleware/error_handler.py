from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.exceptions.business import BusinessError
from app.utils.logging import get_logger
from datetime import datetime, timezone

logger = get_logger("error_handler")


async def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for err in errors:
        field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        messages.append(f"{field}: {err['msg']}")
    return JSONResponse(
        status_code=422,
        content={
            "code": 1001,
            "message": "参数验证失败",
            "detail": "; ".join(messages),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception):
    """全局未捕获异常处理"""
    logger.error(
        "unhandled_error",
        path=str(request.url.path),
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "code": 5000,
            "message": "服务器内部错误",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": str(request.url.path),
        },
    )
