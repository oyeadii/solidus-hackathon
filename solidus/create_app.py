from fastapi import FastAPI

from .config import config
from .include_routers import include_routers
from .app_middlewares import add_cors_middleware, add_log_middleware
from .database import Base, engine


def create_app(title, lifespan, docs_url, redoc_url) -> FastAPI:
    app = FastAPI(
        title=title,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
    )

    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)

    # Include routers to app
    include_routers(app)

    # Add middleware from app_middlewares.py
    add_cors_middleware(app)
    add_log_middleware(app)
    return app
