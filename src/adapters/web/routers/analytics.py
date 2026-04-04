"""Analytics page route."""

import dataclasses

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.application.services import AnalyticsService


def create_analytics_page_router(
    analytics_service: AnalyticsService,
    templates: Jinja2Templates,
) -> APIRouter:
    router = APIRouter(tags=["analytics-pages"])

    @router.get("/analytics", response_class=HTMLResponse)
    def analytics(request: Request) -> HTMLResponse:
        data = analytics_service.get_analytics()
        return templates.TemplateResponse(
            request=request,
            name="analytics.html",
            context={
                "title": "FOSDEM Atlas — Analytics",
                **dataclasses.asdict(data),
            },
        )

    return router
