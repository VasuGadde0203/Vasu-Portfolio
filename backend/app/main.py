from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, contact, content, health
from app.core.config import Settings, load_settings_or_exit
from app.core.logging import configure_logging
from app.core.security import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from app.knowledge import load_profile, load_projects
from app.rag.query import HintDetector
from app.services.chat_service import ChatService
from app.services.contact_service import ContactStore, build_contact_store
from app.services.errors import ServiceError
from app.services.openai_service import AIClient, OpenAIService

log = logging.getLogger(__name__)


def create_app(settings: Settings | None = None, ai: AIClient | None = None,
               contact_store: ContactStore | None = None) -> FastAPI:
    configure_logging()
    settings = settings or load_settings_or_exit()
    profile = load_profile(settings.knowledge_dir)  # validates the knowledge files at startup
    projects = load_projects(settings.knowledge_dir)

    app = FastAPI(title="Vasu Gadde Portfolio API", version="1.0.0",
                  docs_url=None if settings.environment == "production" else "/docs",
                  redoc_url=None, openapi_url=None if settings.environment == "production" else "/openapi.json")
    # Set up eagerly rather than in a lifespan hook: serverless hosts (Vercel) may not run startup events.
    # Nothing here opens a network connection; the database and OpenAI are only contacted per request.
    app.state.contact_store = contact_store or build_contact_store(settings)
    app.state.profile = profile
    app.state.projects = projects
    app.state.chat_service = ChatService(settings, ai or OpenAIService(settings), HintDetector(projects, profile))

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_request_body_bytes)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"],
                       allow_headers=["Content-Type"], allow_credentials=False, max_age=600)

    @app.exception_handler(ServiceError)
    async def service_error(_: Request, exc: ServiceError) -> JSONResponse:
        headers = {"Retry-After": "60"} if exc.status_code == 429 else None
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, exc.status_code, headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        problems = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse({"error": {"code": "invalid_request", "message": "Invalid request.",
                                       "details": problems}}, 422)

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception) -> JSONResponse:
        log.error("Unhandled error (%s)", type(exc).__name__)
        return JSONResponse({"error": {"code": "internal_error", "message": "Something went wrong."}}, 500)

    for router in (health.router, content.router, chat.router, contact.router):
        app.include_router(router, prefix="/api")
    return app


def app_factory() -> FastAPI:
    """Uvicorn entry point: `uvicorn app.main:app_factory --factory`."""
    return create_app()
