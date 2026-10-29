"""Config loader tests."""

import pytest

from dirtbag_data.config import load_settings


def test_loads_development_config():
    settings = load_settings("configs/development.yaml")
    assert settings.database.url.endswith("@localhost:5433/dirtbag")
    assert settings.crawlers.enabled_sources() == ["thecrag"]
    assert settings.http.rate_limit_seconds == 1.5


def test_env_database_override(monkeypatch):
    monkeypatch.setenv("DIRTBAG_DATABASE_URL", "postgresql+psycopg://u:p@db:5432/prod")
    settings = load_settings("configs/development.yaml")
    assert settings.database.url == "postgresql+psycopg://u:p@db:5432/prod"


def test_env_expansion_with_default(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        "database:\n  url: ${MISSING_VAR_FALLBACK:-postgresql+psycopg://localhost/fallback}\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MISSING_VAR_FALLBACK", raising=False)
    settings = load_settings(cfg)
    assert settings.database.url == "postgresql+psycopg://localhost/fallback"


def test_missing_config_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_settings(tmp_path / "nope.yaml")
