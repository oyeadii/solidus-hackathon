from fastapi import Request
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import CustomLog


class LogRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        log = CustomLog(request)
        log.print_log("START")

        start_time = datetime.now()
        response = await call_next(request)
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()

        log.print_log("END", level="info", elapsed_time=elapsed_time)
        return response
