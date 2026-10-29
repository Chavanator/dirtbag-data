"""CLI smoke tests (spec §36)."""

from typer.testing import CliRunner

from dirtbag_data import __version__
from dirtbag_data.cli.main import app

runner = CliRunner()


def test_status_shows_version_and_config():
    result = runner.invoke(app, ["status", "--config", "configs/development.yaml"])
    assert result.exit_code == 0
    assert f"v{__version__}" in result.output
    assert "thecrag" in result.output


def test_status_masks_credentials():
    result = runner.invoke(app, ["status", "--config", "configs/development.yaml"])
    assert "dirtbag:dirtbag@" not in result.output


def test_crawl_unknown_scope_lists_seeds():
    """Sin red: rutas de error de la CLI (los crawls en vivo van por e2e offline)."""
    result = runner.invoke(app, ["crawl", "chihuahua", "--config", "configs/development.yaml"])
    assert result.exit_code == 1
    assert "Unknown scope" in result.output
    assert "el-salto" in result.output


def test_crawl_rejects_unknown_source():
    result = runner.invoke(
        app,
        ["crawl", "el-salto", "--source", "mountain_project", "--config", "configs/development.yaml"],
    )
    assert result.exit_code == 1
    assert "Adapter not available" in result.output


def test_missing_config_fails():
    result = runner.invoke(app, ["status", "--config", "missing.yaml"])
    assert result.exit_code == 1
