from typing import Callable
from starlette.types import ASGIApp, Receive, Scope, Send


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp, logger):
        self.app = app
        self.logger = logger

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method")
        path = scope.get("path")
        self.logger.info("request_start", method=method, path=path)

        async def send_wrapper(message):
            if message.get("type") == "http.response.start":
                status = message.get("status")
                self.logger.info("request_end", method=method, path=path, status=status)
            await send(message)

        await self.app(scope, receive, send_wrapper)

