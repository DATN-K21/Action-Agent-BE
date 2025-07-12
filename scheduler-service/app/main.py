from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.base import router
from app.core import exceptions, logging, swagger
from app.core.lifespan import lifespan

logging.configure_logging()
logger = logging.get_logger(__name__)

app = FastAPI(
    title="Scheduler Service API",
    description="Job scheduling service for the Action-Executing AI Agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set custom OpenAPI schema

swagger.set_custom_openapi(app)

# Register exception handlers
exceptions.register_exception_handlers(app)

# Include routers
app.include_router(router)
