"""
Unit tests for Image Caption Generator API.
Run: pytest tests/ -v
"""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from PIL import Image


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------
def create_test_image(size=(224, 224), color=(100, 150, 200)) -> bytes:
    """Create a small in-memory test image as JPEG bytes."""
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def client():
    """Test client with mocked model service and cache."""
    # Mock model service
    with (
        patch("app.services.model_service.model_service") as mock_model,
        patch("app.services.cache.cache_service") as mock_cache,
    ):
        mock_model.is_loaded = True
        mock_model.device_name = "cpu"
        mock_model.generate_caption.return_value = {
            "caption": "a dog running on the beach",
            "confidence": 0.85,
            "processing_time_ms": 240,
            "beam_size": 3,
        }

        mock_cache.is_connected = True
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.connect = AsyncMock()
        mock_cache.disconnect = AsyncMock()

        from main import app
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
class TestHealthCheck:
    def test_health_returns_200(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200

    def test_health_has_required_fields(self, client):
        data = client.get("/api/v1/health").json()
        assert "status" in data
        assert "model_loaded" in data
        assert "redis_connected" in data

    def test_health_status_healthy(self, client):
        data = client.get("/api/v1/health").json()
        assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# Caption generation
# ---------------------------------------------------------------------------
class TestGenerateCaption:
    def test_valid_jpeg_returns_caption(self, client):
        img_bytes = create_test_image()
        r = client.post(
            "/api/v1/generate-caption",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        )
        assert r.status_code == 200
        data = r.json()
        assert "caption" in data
        assert isinstance(data["caption"], str)
        assert len(data["caption"]) > 0

    def test_response_has_confidence(self, client):
        img_bytes = create_test_image()
        r = client.post(
            "/api/v1/generate-caption",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        )
        data = r.json()
        assert "confidence" in data
        assert 0.0 <= data["confidence"] <= 1.0

    def test_response_has_processing_time(self, client):
        img_bytes = create_test_image()
        r = client.post(
            "/api/v1/generate-caption",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        )
        data = r.json()
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] >= 0

    def test_invalid_content_type_rejected(self, client):
        r = client.post(
            "/api/v1/generate-caption",
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
        assert r.status_code == 415

    def test_empty_file_rejected(self, client):
        r = client.post(
            "/api/v1/generate-caption",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
        )
        assert r.status_code in (400, 422)

    def test_invalid_beam_size_rejected(self, client):
        img_bytes = create_test_image()
        # beam_size=10 exceeds max of 5
        r = client.post(
            "/api/v1/generate-caption?beam_size=10",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        )
        assert r.status_code == 422

    def test_beam_size_1_works(self, client):
        img_bytes = create_test_image()
        r = client.post(
            "/api/v1/generate-caption?beam_size=1",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        )
        assert r.status_code == 200

    def test_png_accepted(self, client):
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        r = client.post(
            "/api/v1/generate-caption",
            files={"file": ("test.png", buf.getvalue(), "image/png")},
        )
        assert r.status_code == 200

    def test_cached_response_has_cached_true(self, client):
        """When cache returns a hit, response should include cached=True."""
        cached_data = {
            "caption": "cached caption here",
            "confidence": 0.9,
            "processing_time_ms": 10,
            "beam_size": 3,
        }
        img_bytes = create_test_image(color=(10, 20, 30))
        with patch("app.api.routes.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value=cached_data)
            r = client.post(
                "/api/v1/generate-caption",
                files={"file": ("cached.jpg", img_bytes, "image/jpeg")},
            )
        assert r.status_code == 200
        assert r.json().get("cached") is True


# ---------------------------------------------------------------------------
# Config endpoint
# ---------------------------------------------------------------------------
class TestConfig:
    def test_config_returns_max_size(self, client):
        data = client.get("/api/v1/config").json()
        assert "max_image_size_mb" in data
        assert data["max_image_size_mb"] > 0

    def test_config_returns_allowed_types(self, client):
        data = client.get("/api/v1/config").json()
        assert "allowed_types" in data
        assert "image/jpeg" in data["allowed_types"]


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
class TestRoot:
    def test_root_returns_200(self, client):
        assert client.get("/").status_code == 200
