"""Shared utilities for web routers."""

from urllib.parse import urlparse

from fastapi import Request


def back_link(
    request: Request,
    default_url: str = "/",
    default_label: str = "Back to schedule",
) -> tuple[str, str]:
    """Return (url, label) for a context-aware back link derived from the Referer header."""
    referer = request.headers.get("referer", "")
    if not referer:
        return default_url, default_label
    try:
        parsed = urlparse(referer)
        if parsed.scheme not in ("http", "https"):
            return default_url, default_label
        path = parsed.path
    except Exception:
        return default_url, default_label

    if path == "/" or path.startswith("/day/"):
        return referer, "Back to schedule"
    if path == "/speakers":
        return referer, "Back to speakers"
    if path == "/tracks":
        return referer, "Back to tracks"
    if path == "/analytics":
        return referer, "Back to analytics"
    if path.startswith("/speaker/"):
        return referer, "Back to speaker"
    if path.startswith("/track/"):
        return referer, "Back to track"
    return referer, "Go back"
