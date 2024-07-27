import json
from loguru import logger
from datetime import datetime
from starlette.requests import Request


class BaseLog:
    def __init__(self):
        pass

    def print(self, log, level="info"):
        log_str = " " + str(log)
        try:
            getattr(logger, level)(log_str)
        except:
            logger.info(log_str)


class CustomLog(BaseLog):
    def __init__(self, request: Request):
        user_id = request.headers.get("userid", "UNKNOWN")
        self.data = {
            "methodName": request.method,
            "userId": user_id,
            "url": str(request.url),
            "hostName": request.client.host,
            "ipAddress": request.client.host,
            "port": request.url.port,
        }

    def print_log(
        self, message="", level="info", elapsed_time=None, extraData: dict = {}
    ):
        dt = self.data
        dt["logTime"] = str(datetime.now())
        dt["message"] = ""
        dt["level"] = level
        if message:
            dt["message"] = message
        if elapsed_time is not None:
            dt["elapsedTime"] = elapsed_time
        if extraData:
            dt["extraData"] = extraData
        super().print(json.dumps(dt), level)
