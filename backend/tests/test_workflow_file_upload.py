"""
Unit tests for POST /api/v1/uploads/workflow-files endpoint.
TDD — Sprint 10.8 hybrid file upload feature.
"""

import io
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client():
    """Import app lazily to avoid side-effects at module load."""
    from app.main import app
    return TestClient(app)


def _auth_headers(client):
    """Register + login a test user, return Bearer headers."""
    client.post(
        "/api/v1/auth/register",
        json={"username": "uploader", "email": "uploader@test.com", "password": "Test1234!"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "uploader", "password": "Test1234!"},
    )
    token = resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Happy-path uploads
# ---------------------------------------------------------------------------

class TestWorkflowFileUploadHappyPath:
    def test_jpeg_upload_returns_server_path(self, tmp_path):
        client = _make_client()
        headers = _auth_headers(client)

        jpeg_data = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # minimal JPEG-like bytes

        with patch("app.api.v1.endpoints.uploads.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/api/v1/uploads/workflow-files",
                files={"file": ("hkid.jpg", io.BytesIO(jpeg_data), "image/jpeg")},
                headers=headers,
            )

        assert response.status_code == 200
        body = response.json()
        assert "server_path" in body
        assert "filename" in body
        assert "size" in body
        assert body["size"] == len(jpeg_data)
        assert os.path.isabs(body["server_path"]), "server_path must be absolute for Playwright setInputFiles()"

    def test_png_upload_accepted(self, tmp_path):
        client = _make_client()
        headers = _auth_headers(client)

        png_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50

        with patch("app.api.v1.endpoints.uploads.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/api/v1/uploads/workflow-files",
                files={"file": ("photo.png", io.BytesIO(png_data), "image/png")},
                headers=headers,
            )

        assert response.status_code == 200

    def test_pdf_upload_accepted(self, tmp_path):
        client = _make_client()
        headers = _auth_headers(client)

        pdf_data = b"%PDF-1.4 " + b"\x00" * 50

        with patch("app.api.v1.endpoints.uploads.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/api/v1/uploads/workflow-files",
                files={"file": ("doc.pdf", io.BytesIO(pdf_data), "application/pdf")},
                headers=headers,
            )

        assert response.status_code == 200

    def test_server_path_in_response_points_to_saved_file(self, tmp_path):
        client = _make_client()
        headers = _auth_headers(client)

        data = b"fake image data"

        with patch("app.api.v1.endpoints.uploads.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/api/v1/uploads/workflow-files",
                files={"file": ("test.jpg", io.BytesIO(data), "image/jpeg")},
                headers=headers,
            )

        assert response.status_code == 200
        server_path = response.json()["server_path"]
        assert os.path.isabs(server_path), f"server_path must be absolute; got: {server_path}"
        assert os.path.exists(server_path)

    def test_each_upload_gets_unique_subdirectory(self, tmp_path):
        client = _make_client()
        headers = _auth_headers(client)
        data = b"img"

        paths = []
        with patch("app.api.v1.endpoints.uploads.UPLOAD_DIR", str(tmp_path)):
            for _ in range(2):
                r = client.post(
                    "/api/v1/uploads/workflow-files",
                    files={"file": ("img.jpg", io.BytesIO(data), "image/jpeg")},
                    headers=headers,
                )
                paths.append(r.json()["server_path"])

        assert paths[0] != paths[1]


# ---------------------------------------------------------------------------
# Security / rejection cases
# ---------------------------------------------------------------------------

class TestWorkflowFileUploadRejection:
    def test_unauthenticated_upload_rejected(self):
        client = _make_client()
        response = client.post(
            "/api/v1/uploads/workflow-files",
            files={"file": ("img.jpg", io.BytesIO(b"data"), "image/jpeg")},
        )
        assert response.status_code == 401

    def test_disallowed_extension_rejected(self, tmp_path):
        client = _make_client()
        headers = _auth_headers(client)

        with patch("app.api.v1.endpoints.uploads.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/api/v1/uploads/workflow-files",
                files={"file": ("script.exe", io.BytesIO(b"MZ\x00"), "application/octet-stream")},
                headers=headers,
            )

        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()

    def test_python_script_rejected(self, tmp_path):
        client = _make_client()
        headers = _auth_headers(client)

        with patch("app.api.v1.endpoints.uploads.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/api/v1/uploads/workflow-files",
                files={"file": ("evil.py", io.BytesIO(b"import os"), "text/x-python")},
                headers=headers,
            )

        assert response.status_code == 400

    def test_file_too_large_rejected(self, tmp_path):
        client = _make_client()
        headers = _auth_headers(client)

        # 51 MB — over the 50 MB limit
        large_data = b"\x00" * (51 * 1024 * 1024)

        with patch("app.api.v1.endpoints.uploads.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/api/v1/uploads/workflow-files",
                files={"file": ("big.jpg", io.BytesIO(large_data), "image/jpeg")},
                headers=headers,
            )

        assert response.status_code == 413

    def test_path_traversal_filename_sanitised(self, tmp_path):
        """../../etc/passwd as filename must not escape the upload directory."""
        client = _make_client()
        headers = _auth_headers(client)

        with patch("app.api.v1.endpoints.uploads.UPLOAD_DIR", str(tmp_path)):
            response = client.post(
                "/api/v1/uploads/workflow-files",
                files={"file": ("../../etc/passwd.jpg", io.BytesIO(b"data"), "image/jpeg")},
                headers=headers,
            )

        # Either accepted with a sanitised path inside tmp_path, or rejected
        if response.status_code == 200:
            server_path = response.json()["server_path"]
            assert str(tmp_path) in server_path, "Path must stay inside upload dir"
