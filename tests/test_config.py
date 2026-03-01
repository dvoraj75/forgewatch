"""Tests for github_monitor.config."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from github_monitor.config import Config, ConfigError, load_config

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_TOML = """\
github_token = "ghp_test1234567890"
github_username = "testuser"
poll_interval = 60
repos = ["owner/repo1", "org/repo2"]
"""

MINIMAL_TOML = """\
github_token = "ghp_test1234567890"
github_username = "testuser"
"""


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    """Write a valid config and return its path."""
    p = tmp_path / "config.toml"
    p.write_text(VALID_TOML)
    return p


@pytest.fixture
def minimal_config_file(tmp_path: Path) -> Path:
    """Write a minimal config (only required fields) and return its path."""
    p = tmp_path / "config.toml"
    p.write_text(MINIMAL_TOML)
    return p


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_load_valid_config(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert cfg.github_token == "ghp_test1234567890"
    assert cfg.github_username == "testuser"
    assert cfg.poll_interval == 60
    assert cfg.repos == ["owner/repo1", "org/repo2"]


def test_load_minimal_config_uses_defaults(minimal_config_file: Path) -> None:
    cfg = load_config(minimal_config_file)
    assert cfg.poll_interval == 300
    assert cfg.repos == []
    assert cfg.log_level == "info"
    assert cfg.notify_on_first_poll is False
    assert cfg.notifications_enabled is True
    assert cfg.dbus_enabled is True
    assert cfg.github_base_url == "https://api.github.com"
    assert cfg.max_retries == 3
    assert cfg.notification_threshold == 3
    assert cfg.notification_urgency == "normal"


def test_config_path_as_string(config_file: Path) -> None:
    cfg = load_config(str(config_file))
    assert isinstance(cfg, Config)


# ---------------------------------------------------------------------------
# Environment variable overrides
# ---------------------------------------------------------------------------


def test_env_github_token_overrides_file(
    config_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_from_env")
    cfg = load_config(config_file)
    assert cfg.github_token == "ghp_from_env"


def test_env_github_monitor_config_path(
    config_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_MONITOR_CONFIG", str(config_file))
    # Call without explicit path — should pick up env var
    cfg = load_config()
    assert cfg.github_username == "testuser"


def test_env_token_provides_missing_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Config file without token + GITHUB_TOKEN env var should succeed."""
    p = tmp_path / "config.toml"
    p.write_text('github_username = "testuser"\n')
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_from_env")
    cfg = load_config(p)
    assert cfg.github_token == "ghp_from_env"


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_missing_config_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Config file not found"):
        load_config(tmp_path / "nonexistent.toml")


def test_invalid_toml(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text("this is [not valid toml =")
    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_config(p)


def test_missing_token(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_username = "testuser"\n')
    with pytest.raises(ConfigError, match="github_token is required"):
        load_config(p)


def test_missing_username(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\n')
    with pytest.raises(ConfigError, match="github_username is required"):
        load_config(p)


def test_poll_interval_too_low(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\npoll_interval = 10\n')
    with pytest.raises(ConfigError, match="poll_interval must be >= 30"):
        load_config(p)


def test_poll_interval_wrong_type(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\npoll_interval = "fast"\n')
    with pytest.raises(ConfigError, match="poll_interval must be an integer"):
        load_config(p)


def test_invalid_repo_format(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nrepos = ["not-a-valid-repo"]\n')
    with pytest.raises(ConfigError, match="Invalid repo format"):
        load_config(p)


def test_repos_not_a_list(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nrepos = "owner/repo"\n')
    with pytest.raises(ConfigError, match="repos must be a list"):
        load_config(p)


# ---------------------------------------------------------------------------
# Validation errors — new config fields
# ---------------------------------------------------------------------------


def test_invalid_log_level(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nlog_level = "trace"\n')
    with pytest.raises(ConfigError, match="log_level must be one of"):
        load_config(p)


def test_log_level_wrong_type(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nlog_level = 42\n')
    with pytest.raises(ConfigError, match="log_level must be a string"):
        load_config(p)


def test_log_level_case_insensitive(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nlog_level = "DEBUG"\n')
    cfg = load_config(p)
    assert cfg.log_level == "debug"


def test_notify_on_first_poll_wrong_type(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nnotify_on_first_poll = "yes"\n')
    with pytest.raises(ConfigError, match="notify_on_first_poll must be a boolean"):
        load_config(p)


def test_notifications_enabled_wrong_type(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nnotifications_enabled = 0\n')
    with pytest.raises(ConfigError, match="notifications_enabled must be a boolean"):
        load_config(p)


def test_dbus_enabled_wrong_type(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\ndbus_enabled = "false"\n')
    with pytest.raises(ConfigError, match="dbus_enabled must be a boolean"):
        load_config(p)


def test_github_base_url_wrong_type(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\ngithub_base_url = 123\n')
    with pytest.raises(ConfigError, match="github_base_url must be a string"):
        load_config(p)


def test_github_base_url_invalid_scheme(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\ngithub_base_url = "ftp://example.com"\n')
    with pytest.raises(ConfigError, match="github_base_url must start with http"):
        load_config(p)


def test_github_base_url_strips_trailing_slash(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\ngithub_base_url = "https://gh.example.com/"\n')
    cfg = load_config(p)
    assert cfg.github_base_url == "https://gh.example.com"


def test_max_retries_wrong_type(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nmax_retries = "three"\n')
    with pytest.raises(ConfigError, match="max_retries must be an integer"):
        load_config(p)


def test_max_retries_negative(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nmax_retries = -1\n')
    with pytest.raises(ConfigError, match="max_retries must be >= 0"):
        load_config(p)


def test_max_retries_zero_allowed(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nmax_retries = 0\n')
    cfg = load_config(p)
    assert cfg.max_retries == 0


def test_notification_threshold_wrong_type(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nnotification_threshold = "high"\n')
    with pytest.raises(ConfigError, match="notification_threshold must be an integer"):
        load_config(p)


def test_notification_threshold_too_low(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nnotification_threshold = 0\n')
    with pytest.raises(ConfigError, match="notification_threshold must be >= 1"):
        load_config(p)


def test_invalid_notification_urgency(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nnotification_urgency = "urgent"\n')
    with pytest.raises(ConfigError, match="notification_urgency must be one of"):
        load_config(p)


def test_notification_urgency_wrong_type(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nnotification_urgency = 1\n')
    with pytest.raises(ConfigError, match="notification_urgency must be a string"):
        load_config(p)


def test_notification_urgency_case_insensitive(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\nnotification_urgency = "Critical"\n')
    cfg = load_config(p)
    assert cfg.notification_urgency == "critical"


def test_all_new_fields_set(tmp_path: Path) -> None:
    """All new config fields can be set together."""
    content = """\
github_token = "ghp_abc"
github_username = "user"
log_level = "warning"
notify_on_first_poll = true
notifications_enabled = false
dbus_enabled = false
github_base_url = "https://gh.corp.example.com/api/v3"
max_retries = 5
notification_threshold = 10
notification_urgency = "critical"
"""
    p = tmp_path / "config.toml"
    p.write_text(content)
    cfg = load_config(p)
    assert cfg.log_level == "warning"
    assert cfg.notify_on_first_poll is True
    assert cfg.notifications_enabled is False
    assert cfg.dbus_enabled is False
    assert cfg.github_base_url == "https://gh.corp.example.com/api/v3"
    assert cfg.max_retries == 5
    assert cfg.notification_threshold == 10
    assert cfg.notification_urgency == "critical"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_token_string(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = ""\ngithub_username = "user"\n')
    with pytest.raises(ConfigError, match="github_token is required"):
        load_config(p)


def test_empty_username_string(tmp_path: Path) -> None:
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = ""\n')
    with pytest.raises(ConfigError, match="github_username is required"):
        load_config(p)


def test_poll_interval_at_boundary(tmp_path: Path) -> None:
    """poll_interval = 30 should be accepted (minimum allowed)."""
    p = tmp_path / "config.toml"
    p.write_text('github_token = "ghp_abc"\ngithub_username = "user"\npoll_interval = 30\n')
    cfg = load_config(p)
    assert cfg.poll_interval == 30
