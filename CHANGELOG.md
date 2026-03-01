# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-03-01

### Added

- Runtime-configurable options in `config.toml`: log level, notifications toggle, D-Bus toggle, notification urgency/threshold, max retries, `notify_on_first_poll`, and GitHub Enterprise base URL
- `update.sh` script for in-place upgrades with git-aware safety checks
- `systemctl --user reload github-monitor` support via `ExecReload` in systemd service
- Pre-commit hooks for ruff and mypy (`.pre-commit-config.yaml`)

### Changed

- Config dataclass is now frozen (immutable) to prevent accidental mutation
- Notification threshold and urgency are configurable (previously hardcoded)
- GitHub API base URL and max retries are configurable, enabling GitHub Enterprise support
- D-Bus interface can be disabled via config for headless/container environments

### Fixed

- Notification click-to-open broken under systemd sandbox — now uses XDG Desktop Portal over D-Bus with fallback to `xdg-open`
- Config reload (SIGHUP) ignored the `-c` config path, always reloading from default location

### Improved

- Reuse single aiohttp session for avatar downloads within a notification batch, reducing connection overhead

## [1.0.0] - 2026-03-01

### Added

- GitHub PR polling via Search Issues API with pagination and rate limiting
- In-memory state store with diff computation (new/closed/updated PRs)
- Desktop notifications via `notify-send` with author avatars and clickable links
- D-Bus session bus interface (`org.github_monitor.Daemon`) with methods: `GetPullRequests`, `GetStatus`, `Refresh` and signal: `PullRequestsChanged`
- TOML configuration with environment variable override support (`GITHUB_TOKEN`)
- Exponential backoff retries for API failures
- Graceful shutdown (SIGTERM/SIGINT) and config reload (SIGHUP)
- Systemd user service with security hardening
- 151 tests with full coverage
