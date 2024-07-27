from fastapi import FastAPI

from routers import project


def include_routers(app: FastAPI):
    """
    Add FastAPI routes here
    """

    app.include_router(project.router)
