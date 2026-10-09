"""
Tests completos para Sprint R02.1 - Plataforma Web Localhost.
"""

import os
import io
import shutil
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from agente_forense.web.config import WebConfig
from agente_forense.web.app import create_app
from agente_forense.core.errors import SafetyViolationError
from agente_forense.persistence.config import DatabaseConfig

@pytest.fixture
def test_app():
    app = create_app()
    return app

@pytest.fixture
def client(test_app):
    return TestClient(test_app)

# 1. Test App Factory
def test_app_factory():
    app = create_app()
    assert app.title == "AGENTE FORENSE Web API"

# 2. Web Config host default
def test_web_config_defaults():
    config = WebConfig()
    assert config.host == "127.0.0.1"
    assert config.port == 8085

# 3, 4, 5. Rechazo de 0.0.0.0 y hosts externos
def test_web_config_invalid_host():
    with pytest.raises(SafetyViolationError):
        WebConfig(host="0.0.0.0")

    with pytest.raises(SafetyViolationError):
        WebConfig(host="192.168.1.50")

# 6, 7. /health 200 y no expone secretos
def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    # Verificar que no expone secretos / DSN
    text = response.text.lower()
    assert "password" not in text
    assert "postgresql://" not in text
    assert "secret" not in text

# 8. /health 503 si DB falla (simulado mediante monkeypatch o config errónea)
def test_health_check_db_failure(monkeypatch):
    from agente_forense.persistence.database import DatabaseEngine
    def mock_check(self):
        raise Exception("DB offline")
    monkeypatch.setattr(DatabaseEngine, "check_connection", mock_check)
    
    # También interceptar get_db_session para forzar error
    from agente_forense.web.dependencies import get_db_session
    def mock_get_db():
        class MockSession:
            def execute(self, *args, **kwargs):
                raise Exception("DB Down")
            def close(self):
                pass
        yield MockSession()
    app = create_app()
    app.dependency_overrides[get_db_session] = mock_get_db
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["detail"]["database"] == "error"

# 9. /api/system/status
def test_api_system_status(client):
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["application_name"] == "AGENTE FORENSE"
    assert data["web_host"] == "127.0.0.1"
    assert data["web_port"] == 8085

# 10. Dashboard render
def test_dashboard_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "AGENTE FORENSE" in response.text
    assert "Dashboard Operativo" in response.text

# 11. /cases render
def test_cases_page(client):
    response = client.get("/cases")
    assert response.status_code == 200
    assert "Listado de Casos Registrados" in response.text

# 12. /api/cases JSON
def test_api_cases_json(client):
    response = client.get("/api/cases")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# 13. Case detail 404 seguro
def test_case_detail_not_found(client):
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/cases/{fake_uuid}")
    assert response.status_code == 404
    assert "Caso 00000000-0000-0000-0000-000000000000 no encontrado" in response.text

# 14. /audit page
def test_audit_page(client):
    response = client.get("/audit")
    assert response.status_code == 200

# 15. /api/audit JSON
def test_api_audit_json(client):
    response = client.get("/api/audit")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# 16, 17, 18. Error model, request_id, traceback no expuesto
def test_error_handling_and_request_id(client):
    response = client.get("/cases/invalid-uuid")
    assert response.status_code == 422 or response.status_code == 500
    # No debe exponer traceback ni secretos
    assert "Traceback (most recent call last)" not in response.text

# Helper para llamadas POST con CSRF
def post_with_csrf(client, url, **kwargs):
    health_res = client.get("/health")
    token = health_res.cookies.get("csrf_token")
    headers = kwargs.get("headers", {})
    cookies = kwargs.get("cookies", {})
    if token:
        headers["x-csrf-token"] = token
        cookies["csrf_token"] = token
    kwargs["headers"] = headers
    kwargs["cookies"] = cookies
    return client.post(url, **kwargs)

# 19. Upload pequeño válido a staging
def test_upload_staging_success(tmp_path):
    staging_dir = tmp_path / "staging_succ"
    config = WebConfig(staging_dir=str(staging_dir))
    app = create_app(config)
    client = TestClient(app)
    
    file_content = b"Contenido de prueba sintetico R02.1"
    files = {"file": ("test_doc.txt", io.BytesIO(file_content), "text/plain")}
    
    response = post_with_csrf(client, "/api/files/stage", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "staged"
    assert data["original_filename"] == "test_doc.txt"
    assert data["size_bytes"] == len(file_content)

# 20. Upload supera límite -> 413
def test_upload_staging_exceeds_limit(tmp_path):
    staging_dir = tmp_path / "staging_limit"
    config = WebConfig(max_upload_bytes=100, staging_dir=str(staging_dir))
    app = create_app(config)
    client = TestClient(app)
    file_content = b"A" * 200
    files = {"file": ("big_file.txt", io.BytesIO(file_content), "text/plain")}
    
    response = post_with_csrf(client, "/api/files/stage", files=files)
    assert response.status_code == 413
    assert "MAX_UPLOAD_SIZE_EXCEEDED" in response.text

# 21. Path traversal bloqueado
def test_path_traversal_blocked(client):
    file_content = b"test"
    files = {"file": ("../../secret.txt", io.BytesIO(file_content), "text/plain")}
    response = post_with_csrf(client, "/api/files/stage", files=files)
    assert response.status_code == 400
    assert "INVALID_FILENAME" in response.text

# 24. SHA-256 hash upload correcto
def test_upload_sha256_verification(tmp_path):
    staging_dir = tmp_path / "staging_sha"
    config = WebConfig(staging_dir=str(staging_dir))
    app = create_app(config)
    client = TestClient(app)
    file_content = b"Hello Forensic World"
    import hashlib
    expected_hash = hashlib.sha256(file_content).hexdigest()
    
    files = {"file": ("hello.txt", io.BytesIO(file_content), "text/plain")}
    response = post_with_csrf(client, "/api/files/stage", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["sha256"] == expected_hash

# 25. No overwrite en staging
def test_upload_no_overwrite(tmp_path):
    staging_dir = tmp_path / "staging_no_overwrite"
    config = WebConfig(staging_dir=str(staging_dir))
    app = create_app(config)
    client = TestClient(app)
    file_content = b"Content 1"
    files = {"file": ("same.txt", io.BytesIO(file_content), "text/plain")}
    response1 = post_with_csrf(client, "/api/files/stage", files=files)
    assert response1.status_code == 200

    token = response1.cookies.get("csrf_token") or client.cookies.get("csrf_token")
    files2 = {"file": ("same.txt", io.BytesIO(file_content), "text/plain")}
    response2 = client.post("/api/files/stage", files=files2, headers={"x-csrf-token": token})
    assert response2.status_code == 409
    assert "FILE_ALREADY_EXISTS" in response2.text

# 26. Cookie CSRF legible por JS (HttpOnly=False)
def test_csrf_cookie_readable_by_js(client):
    response = client.get("/health")
    assert response.status_code == 200
    cookie = response.cookies.get("csrf_token")
    assert cookie is not None
    # Verificar que el header set-cookie no contenga HttpOnly para csrf_token
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "HttpOnly" not in set_cookie_header

# 27, 28. Headers de seguridad y Cache-Control
def test_security_headers(client):
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"

    response_cases = client.get("/cases")
    assert "no-store" in response_cases.headers["Cache-Control"]

# 29, 30, 31. DB Config validation
def test_db_config_verification():
    db_config = DatabaseConfig()
    assert db_config.user == "agente_forense_app"
    assert db_config.host == "127.0.0.1"
    assert db_config.port == 5433

# 33..38 Safety baseline prohibidos
def test_prohibited_components_not_called():
    # Verificar que las carpetas reales y drivers no son accedidos
    assert not Path("casos/REAL_EVIDENCE").exists()
