"""Main entry point for the FastAPI application."""

from app.core import logging
from app.core.settings import env_settings

logging.configure_logging()
logger = logging.get_logger(__name__)


from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api.router import router  # noqa: E402
from app.core import exceptions, swagger  # noqa: E402
from app.core.lifespan import lifespan  # noqa: E402
from app.core.socketio import get_socketio_asgi  # noqa: E402

is_debug = env_settings.DBG
logger.info(f"Starting server in {'DEBUG' if is_debug else 'PRODUCTION'} mode.")


app = FastAPI(
    debug=is_debug,
    title="Action-Executing AI Service API",
    description="This is an AI Service API using FastAPI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[env_settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


swagger.set_custom_openapi(app)
exceptions.register_exception_handlers(app)
app.include_router(router)
app.mount("/", get_socketio_asgi())
