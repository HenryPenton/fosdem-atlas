"""Tests for PWA features — offline page, manifest, service worker."""

from fastapi.testclient import TestClient


class TestOfflinePage:
    def test_offline_returns_200(self, client: TestClient) -> None:
        response = client.get("/offline")
        assert response.status_code == 200

    def test_offline_contains_message(self, client: TestClient) -> None:
        response = client.get("/offline")
        assert "offline" in response.text.lower()


class TestStaticPWAAssets:
    def test_manifest_served(self, client: TestClient) -> None:
        response = client.get("/static/manifest.json")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        data = response.json()
        assert data["name"] == "FOSDEM Explorer"
        assert data["start_url"] == "/"
        assert len(data["icons"]) >= 2

    def test_service_worker_served(self, client: TestClient) -> None:
        response = client.get("/static/sw.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]

    def test_icon_192_served(self, client: TestClient) -> None:
        response = client.get("/static/icons/icon-192.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_icon_512_served(self, client: TestClient) -> None:
        response = client.get("/static/icons/icon-512.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"


class TestPWABaseHTML:
    def test_manifest_link_in_html(self, client: TestClient) -> None:
        response = client.get("/")
        assert 'rel="manifest"' in response.text
        assert "/static/manifest.json" in response.text

    def test_theme_color_meta_in_html(self, client: TestClient) -> None:
        response = client.get("/")
        assert 'name="theme-color"' in response.text

    def test_service_worker_registration_in_html(self, client: TestClient) -> None:
        response = client.get("/")
        assert "serviceWorker" in response.text
        assert "sw.js" in response.text
