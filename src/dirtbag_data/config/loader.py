"""Settings model and loader.

Precedence (highest wins):
1. Explicit environment variables (DIRTBAG_*)
2. .env file (if present)
3. YAML config file (DIRTBAG_CONFIG or configs/development.yaml)

Values of the form ``${VAR}`` or ``${VAR:-default}`` inside YAML files are
expanded against the environment.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

_ENV_PATTERN = re.compile(r"\$\{(?P<name>[A-Z0-9_]+)(?::-(?P<default>[^}]*))?\}")


class DatabaseConfig(BaseModel):
    url: str


class StorageConfig(BaseModel):
    raw_path: Path = Path("./data/local/raw")


class HttpConfig(BaseModel):
    timeout: float = 20.0
    max_retries: int = 3
    rate_limit_seconds: float = 1.5
    user_agent: str = "DirtBagBot/0.1"


class SourceConfig(BaseModel):
    enabled: bool = False
    base_url: str
    seeds: dict[str, str] = Field(default_factory=dict)


class CrawlersConfig(BaseModel):
    sources: dict[str, SourceConfig] = Field(default_factory=dict)

    def enabled_sources(self) -> list[str]:
        return [name for name, cfg in self.sources.items() if cfg.enabled]


class LoggingConfig(BaseModel):
    level: str = "INFO"


class Settings(BaseModel):
    database: DatabaseConfig
    storage: StorageConfig = StorageConfig()
    http: HttpConfig = HttpConfig()
    crawlers: CrawlersConfig = CrawlersConfig()
    logging: LoggingConfig = LoggingConfig()


def _expand_env(value: object) -> object:
    if isinstance(value, str):

        def repl(match: re.Match[str]) -> str:
            name = match.group("name")
            default = match.group("default") or ""
            return os.environ.get(name, default)

        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_settings(path: str | Path | None = None) -> Settings:
    """Load settings from YAML + environment.

    ``path`` overrides DIRTBAG_CONFIG; ``.env`` in the project root is loaded
    if it exists. DIRTBAG_DATABASE_URL and DIRTBAG_RAW_STORAGE_PATH take
    precedence over values coming from the YAML file.
    """
    load_dotenv()

    config_path = Path(path or os.environ.get("DIRTBAG_CONFIG", "configs/development.yaml"))
    with config_path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    data = _expand_env(raw)
    settings = Settings.model_validate(data)

    if db_url := os.environ.get("DIRTBAG_DATABASE_URL"):
        settings.database.url = db_url
    if raw_path := os.environ.get("DIRTBAG_RAW_STORAGE_PATH"):
        settings.storage.raw_path = Path(raw_path)

    return settings
