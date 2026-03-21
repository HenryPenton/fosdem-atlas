"""Speaker page routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.application.services import SpeakerService


def create_speakers_page_router(
    speaker_service: SpeakerService,
    templates: Jinja2Templates,
) -> APIRouter:
    router = APIRouter(tags=["speaker-pages"])

    @router.get("/speakers", response_class=HTMLResponse)
    def speakers_browser(request: Request) -> HTMLResponse:
        speakers = speaker_service.get_all_speakers()
        return templates.TemplateResponse(
            request=request,
            name="speakers.html",
            context={
                "title": "FOSDEM Explorer — Speakers",
                "speakers": speakers,
            },
        )

    @router.get("/speaker/{speaker_id}", response_class=HTMLResponse)
    def speaker_detail(request: Request, speaker_id: str) -> HTMLResponse:
        result = speaker_service.get_speaker_detail(speaker_id)
        if result is None:
            return templates.TemplateResponse(
                request=request,
                name="404.html",
                context={
                    "title": "FOSDEM Explorer — Not Found",
                    "message": "That speaker doesn't exist or may have been removed.",
                },
                status_code=404,
            )
        return templates.TemplateResponse(
            request=request,
            name="speaker.html",
            context={
                "title": f"FOSDEM Explorer — {result.name}",
                "speaker": result,
                "events": result.events,
            },
        )

    return router
