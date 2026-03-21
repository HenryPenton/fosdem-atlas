"""FastAPI web adapter."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import cast

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import RequestResponseEndpoint

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

CACHE_MAX_AGE = 20
RATE_LIMIT = "1000/minute"

limiter = Limiter(
    key_func=lambda *_args, **_kwargs: "global",
    default_limits=[RATE_LIMIT],
    headers_enabled=True,
)


def create_app(
    schedule_service: ScheduleService,
    analytics_service: AnalyticsService,
    speaker_service: SpeakerService,
    settings: Settings,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="FOSDEM Explorer",
        description="A DuckDB-powered web application for exploring the FOSDEM schedule",
        version=settings.version,
        lifespan=lifespan,
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

    def _rate_limit_handler(request: Request, exc: Exception) -> Response:
        rate_exc = cast(RateLimitExceeded, exc)
        accept = request.headers.get("accept", "")
        response: Response
        if "text/html" in accept:
            response = HTMLResponse(
                content=templates.get_template("rate_limit.html").render(
                    {"request": request, "title": "FOSDEM Explorer — Too Many Requests"}
                ),
                status_code=429,
            )
        else:
            response = JSONResponse(
                {"error": f"Rate limit exceeded: {rate_exc.detail}"}, status_code=429
            )
        return request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)  # type: ignore[no-any-return]

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.middleware("http")
    async def add_cache_control(request: Request, call_next: RequestResponseEndpoint) -> Response:
        response: Response = await call_next(request)
        if request.url.path != "/health" and request.method == "GET":
            response.headers["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE}"
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
