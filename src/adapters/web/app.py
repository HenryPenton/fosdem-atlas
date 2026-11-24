"""FastAPI web adapter."""

from __future__ import annotations

import logging
import secrets
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import cast
from urllib.parse import quote

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import sync_check_limits
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.adapters.web.routers.analytics import create_analytics_page_router
from src.adapters.web.routers.export import create_export_page_router
from src.adapters.web.routers.health import create_health_page_router
from src.adapters.web.routers.partials import create_partials_router
from src.adapters.web.routers.schedule import create_schedule_router
from src.adapters.web.routers.speakers import create_speakers_page_router
from src.api.routes import create_api_router
from src.application.services import AnalyticsService, ScheduleService, SpeakerService
from src.config import Settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
RATE_LIMIT = "10000/minute"

logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=lambda *_args, **_kwargs: "global",
    default_limits=[RATE_LIMIT],
    headers_enabled=True,
)


def _global_rate_limit_scope() -> None:
    """Stand-in route handler so slowapi applies its default limit to every request."""


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """Apply the limiter's default limits to all requests except static files.

    slowapi's own middleware looks up the endpoint via ``route.endpoint``, which FastAPI
    no longer exposes for routers added with ``include_router``. It then treats every
    request as exempt, silently disabling rate limiting.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        app_limiter: Limiter = request.app.state.limiter
        if not app_limiter.enabled or request.url.path.startswith("/static"):
            return await call_next(request)

        error_response: Response | None
        should_inject_headers: bool
        error_response, should_inject_headers = sync_check_limits(
            app_limiter, request, _global_rate_limit_scope, request.app
        )
        if error_response is not None:
            return error_response

        response = await call_next(request)
        if should_inject_headers:
            response = app_limiter._inject_headers(response, request.state.view_rate_limit)
        return response


def create_app(
    schedule_service: ScheduleService,
    analytics_service: AnalyticsService,
    speaker_service: SpeakerService,
    settings: Settings,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="FOSDEM Atlas",
        description="A DuckDB-powered web application for exploring the FOSDEM schedule",
        version=settings.version,
        lifespan=lifespan,
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    templates.env.filters["urlencode_path"] = lambda s: quote(str(s), safe="/")

    def _rate_limit_handler(request: Request, exc: Exception) -> Response:
        rate_exc = cast(RateLimitExceeded, exc)
        logger.warning("Rate limit exceeded: %s %s", request.method, request.url.path)
        accept = request.headers.get("accept", "")
        response: Response
        if "text/html" in accept:
            response = HTMLResponse(
                content=templates.get_template("rate_limit.html").render(
                    {"request": request, "title": "FOSDEM Atlas — Too Many Requests"}
                ),
                status_code=429,
            )
        else:
            response = JSONResponse(
                {"error": f"Rate limit exceeded: {rate_exc.detail}"}, status_code=429
            )
        # app.state is untyped, so the limiter and the value returned from it are Any.
        return request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)  # type: ignore[no-any-return]

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(GlobalRateLimitMiddleware)

    @app.middleware("http")
    async def add_security_headers(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )
        response.headers["Content-Security-Policy"] = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
            f"style-src 'self'; "
            f"img-src 'self' data:; "
            f"font-src 'self'; "
            f"connect-src 'self'; "
            f"frame-ancestors 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
            f"worker-src 'self'"
        )
        return response

    # JSON API
    app.include_router(
        create_api_router(schedule_service, analytics_service, speaker_service, settings)
    )

    # Web page routers
    app.include_router(create_schedule_router(schedule_service, templates))
    app.include_router(create_speakers_page_router(speaker_service, templates))
    app.include_router(create_analytics_page_router(analytics_service, templates))
    app.include_router(create_partials_router(schedule_service, templates))
    app.include_router(create_export_page_router(schedule_service, speaker_service))
    app.include_router(create_health_page_router(schedule_service, settings))

    return app
