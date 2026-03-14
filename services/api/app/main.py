from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.routes import chat, documents, health
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.services.hr_database_service import HRDatabaseService

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("starting_application environment=%s", settings.app_env)
    HRDatabaseService(settings).ensure_database()
    logger.info("hr_database_ready path=%s", settings.hr_database_path)
    yield
    logger.info("stopping_application")


app = FastAPI(
    title="myhr-ai API",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> ORJSONResponse:
    logger.exception("unhandled_exception error=%s", str(exc))
    return ORJSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )
