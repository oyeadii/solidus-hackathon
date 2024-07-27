from solidus.create_app import create_app
from solidus.app_lifespan import app_lifespan
from solidus.config import settings


docs_url = "/docs"
redoc_url = "/redoc"

app = create_app(
    title=f"Solidus-{settings.envi}",
    lifespan=app_lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url,
)
