from app.core.config import Settings, settings


def test_settings_initialization():
    assert settings.PROJECT_NAME == "Nexus Studio API"
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
    assert len(settings.BACKEND_CORS_ORIGINS) > 0


def test_cors_origins_validator():
    cfg = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000,http://example.com")
    assert "http://localhost:3000" in cfg.BACKEND_CORS_ORIGINS
    assert "http://example.com" in cfg.BACKEND_CORS_ORIGINS
