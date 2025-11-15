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
        logger.error("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error": {"message": "Internal server error"}},
        )

