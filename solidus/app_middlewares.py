from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utilities.custom_middlewares import LogRequestsMiddleware


def add_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000" ," http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["GET","POST","PUT","DELETE","PATCH"],
        allow_headers=["method","path","Authorization","Content-Type","origin","accept"],
    )


def add_log_middleware(app: FastAPI):
    app.add_middleware(LogRequestsMiddleware)
