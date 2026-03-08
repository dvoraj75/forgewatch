"""Configuration loading and validation for forgewatch."""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "forgewatch"
CONFIG_PATH = CONFIG_DIR / "config.toml"

_REPO_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$")

_MIN_POLL_INTERVAL = 30
_VALID_LOG_LEVELS = frozenset({"debug", "info", "warning", "error"})
_VALID_URGENCIES = frozenset({"low", "normal", "critical"})
_VALID_ICON_THEMES = frozenset({"light", "dark"})


class ConfigError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""


@dataclass(frozen=True)
class Config:
    """Validated configuration for forgewatch."""

    github_token: str
    github_username: str
    poll_interval: int = 300
    repos: list[str] = field(default_factory=list)
    log_level: str = "info"
    notify_on_first_poll: bool = False
    notifications_enabled: bool = True
    dbus_enabled: bool = True
    github_base_url: str = "https://api.github.com"
    max_retries: int = 3
    notification_threshold: int = 3
    notification_urgency: str = "normal"
    icon_theme: str = "light"


def load_config(path: Path | str | None = None) -> Config:
    """Load and validate config from TOML file.

    Path resolution precedence:
        1. Explicit ``path`` argument
        2. ``FORGEWATCH_CONFIG`` env var
        3. Default: ``~/.config/forgewatch/config.toml``

    The ``github_token`` value can be overridden by the
    ``GITHUB_TOKEN`` env var (takes precedence over the file value).
    """
    config_path = _resolve_path(path)

    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise ConfigError(msg)

    try:
        with config_path.open("rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        msg = f"Invalid TOML in {config_path}: {exc}"
        raise ConfigError(msg) from exc

    # Env var override for token
    env_token = os.environ.get("GITHUB_TOKEN")
    if env_token:
        raw["github_token"] = env_token

    return _validate(raw)


def _resolve_path(path: Path | str | None) -> Path:
    """Determine which config file path to use."""
    if path is not None:
        return Path(path)

    env_path = os.environ.get("FORGEWATCH_CONFIG")
    if env_path:
        return Path(env_path)

    return CONFIG_PATH


def _require_str(raw: dict[str, object], key: str, error_msg: str) -> str:
    """Extract a required non-empty string field."""
    value = raw.get(key, "")
    if not value or not isinstance(value, str):
        raise ConfigError(error_msg)
    return value


def _validate_bool(raw: dict[str, object], key: str, *, default: bool) -> bool:
    """Extract and validate an optional boolean field."""
    value = raw.get(key, default)
    if not isinstance(value, bool):
        msg = f"{key} must be a boolean, got {type(value).__name__}"
        raise ConfigError(msg)
    return value


def _validate_int_min(raw: dict[str, object], key: str, *, default: int, minimum: int) -> int:
    """Extract and validate an optional integer field with a minimum bound."""
    value = raw.get(key, default)
    if not isinstance(value, int):
        msg = f"{key} must be an integer, got {type(value).__name__}"
        raise ConfigError(msg)
    if value < minimum:
        msg = f"{key} must be >= {minimum}, got {value}"
        raise ConfigError(msg)
    return value


def _validate_choice(
    raw: dict[str, object],
    key: str,
    *,
    default: str,
    choices: frozenset[str],
) -> str:
    """Extract and validate an optional string field against allowed values."""
    value = raw.get(key, default)
    if not isinstance(value, str):
        msg = f"{key} must be a string, got {type(value).__name__}"
        raise ConfigError(msg)
    normalised = value.lower()
    if normalised not in choices:
        msg = f"{key} must be one of {sorted(choices)}, got {normalised!r}"
        raise ConfigError(msg)
    return normalised


def _validate_base_url(raw: dict[str, object]) -> str:
    """Extract and validate the GitHub base URL."""
    value = raw.get("github_base_url", "https://api.github.com")
    if not isinstance(value, str):
        msg = f"github_base_url must be a string, got {type(value).__name__}"
        raise ConfigError(msg)
    if not value.startswith(("http://", "https://")):
        msg = f"github_base_url must start with http:// or https://, got {value!r}"
        raise ConfigError(msg)
    return value.rstrip("/")


def _validate_repos(raw: dict[str, object]) -> list[str]:
    """Extract and validate the repos list."""
    repos = raw.get("repos", [])
    if not isinstance(repos, list):
        msg = "repos must be a list"
        raise ConfigError(msg)
    for repo in repos:
        if not isinstance(repo, str) or not _REPO_PATTERN.match(repo):
            msg = f"Invalid repo format: {repo!r} (expected 'owner/name')"
            raise ConfigError(msg)
    return repos


def _validate(raw: dict[str, object]) -> Config:
    """Validate raw TOML dict and return a Config instance."""
    github_token = _require_str(raw, "github_token", "github_token is required (set in config or GITHUB_TOKEN env var)")
    github_username = _require_str(raw, "github_username", "github_username is required")

    return Config(
        github_token=github_token,
        github_username=github_username,
        poll_interval=_validate_int_min(raw, "poll_interval", default=300, minimum=_MIN_POLL_INTERVAL),
        repos=_validate_repos(raw),
        log_level=_validate_choice(raw, "log_level", default="info", choices=_VALID_LOG_LEVELS),
        notify_on_first_poll=_validate_bool(raw, "notify_on_first_poll", default=False),
        notifications_enabled=_validate_bool(raw, "notifications_enabled", default=True),
        dbus_enabled=_validate_bool(raw, "dbus_enabled", default=True),
        github_base_url=_validate_base_url(raw),
        max_retries=_validate_int_min(raw, "max_retries", default=3, minimum=0),
        notification_threshold=_validate_int_min(raw, "notification_threshold", default=3, minimum=1),
        notification_urgency=_validate_choice(raw, "notification_urgency", default="normal", choices=_VALID_URGENCIES),
        icon_theme=_validate_choice(raw, "icon_theme", default="light", choices=_VALID_ICON_THEMES),
    )
