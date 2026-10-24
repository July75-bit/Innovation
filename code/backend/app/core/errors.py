"""统一错误格式与服务端异常。

契约（docs/software/api_contract.md §2）：

    {"success": false, "message": "可直接展示的中文", "code": "MACHINE_CODE"}

- 业务失败：400 / 404，``message`` 前端直接展示，不写映射表；
- 参数格式错误：422 ``VALIDATION_ERROR``（Pydantic 校验失败）；
- 未预期异常：500 ``INTERNAL_ERROR``，不把堆栈暴露给前端。
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("playerstock.errors")


class ApiError(Exception):
    """业务异常：由接口层抛出，统一转成契约里的错误 JSON。"""

    def __init__(self, message: str, *, status_code: int = 400, code: str = "BAD_REQUEST") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def error_response(message: str, status_code: int, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "code": code},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """挂到 app 上，保证所有失败都是同一套 JSON。"""

    @app.exception_handler(ApiError)
    async def _handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.message, exc.status_code, exc.code)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        first = errors[0] if errors else {}
        location = ".".join(str(part) for part in first.get("loc", ()) if part != "body")
        message = f"请求参数不合法：{location}" if location else "请求参数不合法"
        return error_response(message, 422, "VALIDATION_ERROR")

    @app.exception_handler(Exception)
    async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("未处理异常 %s %s", request.method, request.url.path)
        return error_response("服务器内部错误，请稍后重试", 500, "INTERNAL_ERROR")
