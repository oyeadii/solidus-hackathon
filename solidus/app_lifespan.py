from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    try:
        yield
    finally:
        # Cleanup code here, if necessary
        pass
