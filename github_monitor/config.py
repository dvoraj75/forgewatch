"""Configuration loading and validation for github-monitor."""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "github-monitor"
CONFIG_PATH = CONFIG_DIR / "config.toml"

_REPO_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$")


class ConfigError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""


@dataclass
class Config:
    """Validated configuration for github-monitor."""

    github_token: str
    github_username: str
    poll_interval: int = 300
    repos: list[str] = field(default_factory=list)


def load_config(path: Path | str | None = None) -> Config:
    """Load and validate config from TOML file.

    Path resolution precedence:
        1. Explicit ``path`` argument
        2. ``GITHUB_MONITOR_CONFIG`` env var
        3. Default: ``~/.config/github-monitor/config.toml``

    The ``github_token`` value can be overridden by the
    ``GITHUB_TOKEN`` env var (takes precedence over the file value).
    """
    config_path = _resolve_path(path)

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {config_path}: {exc}") from exc

    # Env var override for token
    env_token = os.environ.get("GITHUB_TOKEN")
    if env_token:
        raw["github_token"] = env_token

    return _validate(raw)


def _resolve_path(path: Path | str | None) -> Path:
    """Determine which config file path to use."""
    if path is not None:
        return Path(path)

    env_path = os.environ.get("GITHUB_MONITOR_CONFIG")
    if env_path:
        return Path(env_path)

    return CONFIG_PATH


def _validate(raw: dict) -> Config:
    """Validate raw TOML dict and return a Config instance."""
    # Required fields
    github_token = raw.get("github_token", "")
    if not github_token or not isinstance(github_token, str):
        raise ConfigError(
            "github_token is required (set in config or GITHUB_TOKEN env var)"
        )

    github_username = raw.get("github_username", "")
    if not github_username or not isinstance(github_username, str):
        raise ConfigError("github_username is required")

    # Poll interval
    poll_interval = raw.get("poll_interval", 300)
    if not isinstance(poll_interval, int):
        raise ConfigError(
            f"poll_interval must be an integer, got {type(poll_interval).__name__}"
        )
    if poll_interval < 30:
        raise ConfigError(f"poll_interval must be >= 30 seconds, got {poll_interval}")

    # Repos
    repos = raw.get("repos", [])
    if not isinstance(repos, list):
        raise ConfigError("repos must be a list")
    for repo in repos:
        if not isinstance(repo, str) or not _REPO_PATTERN.match(repo):
            raise ConfigError(f"Invalid repo format: {repo!r} (expected 'owner/name')")

    return Config(
        github_token=github_token,
        github_username=github_username,
        poll_interval=poll_interval,
        repos=repos,
    )
