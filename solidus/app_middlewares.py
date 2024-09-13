from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utilities.custom_middlewares import LogRequestsMiddleware


def add_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def add_log_middleware(app: FastAPI):
    app.add_middleware(LogRequestsMiddleware)