from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.base import router
from app.core import exceptions, logging, swagger
from app.core.lifespan import lifespan
from app.core.settings import env_settings

logging.configure_logging()

logger = logging.get_logger(__name__)
logger.info(f"Starting server... DebugMode = {env_settings.DEBUG_SERVER}")

app = FastAPI(
    debug=env_settings.DEBUG_SERVER,
    title="Action-Executing AI Service API",
    description="This is an AI Service API using FastAPI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,  # type: ignore
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

swagger.set_custom_openapi(app)
exceptions.register_exception_handlers(app)

app.include_router(router)
