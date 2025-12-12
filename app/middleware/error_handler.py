from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def register_error_handlers(app: FastAPI, logger):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("http_error", status_code=exc.status_code, detail=str(exc.detail))
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"message": str(exc.detail), "code": exc.status_code}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("validation_error", errors=exc.errors())
        return JSONResponse(
            status_code=422,
            content={"error": {"message": "Validation error", "details": exc.errors()}},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Log detailed error information, especially for OpenAPI endpoints
        error_info = {
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": request.url.path,
        }
        # Include traceback for OpenAPI endpoints to help debug schema generation issues
        if request.url.path in ["/openapi.json", "/docs", "/redoc"]:
            import traceback
            error_info["traceback"] = traceback.format_exc()
            logger.error("openapi_generation_error", **error_info)
        else:
            logger.error("unhandled_exception", **error_info)
        
        return JSONResponse(
            status_code=500,
            content={"error": {"message": "Internal server error"}},
        )

