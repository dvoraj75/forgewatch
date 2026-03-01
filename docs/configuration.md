# Configuration

github-monitor is configured via a TOML file and optional environment variable
overrides.

## Config file location

The config file path is resolved in this order:

1. **Explicit path** -- passed directly to `load_config(path)` or via the `-c` /
   `--config` CLI flag
2. **`GITHUB_MONITOR_CONFIG` env var** -- if set, its value is used as the config
   file path
3. **Default path** -- `~/.config/github-monitor/config.toml`

If no config file is found at the resolved path, a `ConfigError` is raised.

## Fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `github_token` | string | Yes | -- | GitHub personal access token (PAT) with `repo` scope |
| `github_username` | string | Yes | -- | Your GitHub username (used in search queries) |
| `poll_interval` | integer | No | `300` | Seconds between poll cycles (minimum: 30) |
| `repos` | list of strings | No | `[]` | Repository filter in `owner/name` format; empty = all repos |
| `log_level` | string | No | `"info"` | Log level: `"debug"`, `"info"`, `"warning"`, or `"error"` |
| `notify_on_first_poll` | boolean | No | `false` | Send notifications for PRs found on the first poll |
| `notifications_enabled` | boolean | No | `true` | Enable/disable desktop notifications entirely |
| `dbus_enabled` | boolean | No | `true` | Enable/disable the D-Bus interface |
| `github_base_url` | string | No | `"https://api.github.com"` | GitHub API base URL (for GitHub Enterprise Server) |
| `max_retries` | integer | No | `3` | Max HTTP retries for 5xx errors (minimum: 0) |
| `notification_threshold` | integer | No | `3` | PRs above this count get a summary notification instead of individual ones (minimum: 1) |
| `notification_urgency` | string | No | `"normal"` | Notification urgency: `"low"`, `"normal"`, or `"critical"` |

## Environment variable overrides

| Variable | Overrides | Notes |
|---|---|---|
| `GITHUB_TOKEN` | `github_token` | Takes precedence over the file value. Useful for keeping tokens out of config files. |
| `GITHUB_MONITOR_CONFIG` | Config file path | Alternative to passing `-c` on the command line. |

`GITHUB_TOKEN` is applied after the config file is loaded, so you can have a
config file without a token and supply it via the environment instead.

## Validation rules

All validation happens at config load time. If any rule fails, a `ConfigError`
is raised with a descriptive message.

- `github_token` -- must be a non-empty string
- `github_username` -- must be a non-empty string
- `poll_interval` -- must be an integer >= 30
- `repos` -- must be a list; each entry must match the pattern
  `^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$` (i.e., `owner/name`)
- `log_level` -- must be one of `debug`, `info`, `warning`, `error` (case-insensitive)
- `notify_on_first_poll` -- must be a boolean
- `notifications_enabled` -- must be a boolean
- `dbus_enabled` -- must be a boolean
- `github_base_url` -- must be a string starting with `http://` or `https://`; trailing slashes are stripped
- `max_retries` -- must be an integer >= 0
- `notification_threshold` -- must be an integer >= 1
- `notification_urgency` -- must be one of `low`, `normal`, `critical` (case-insensitive)

## Example config

A minimal configuration with only required fields:

```toml
github_token    = "ghp_abc123def456"
github_username = "janedoe"
```

This uses defaults: `poll_interval = 300`, `repos = []` (all repositories),
`log_level = "info"`, notifications enabled, D-Bus enabled.

A full configuration:

```toml
github_token            = "ghp_abc123def456"
github_username         = "janedoe"
poll_interval           = 60
repos                   = ["myorg/frontend", "myorg/backend", "otherorg/shared-lib"]
log_level               = "debug"
notify_on_first_poll    = true
notifications_enabled   = true
dbus_enabled            = true
github_base_url         = "https://github.example.com/api/v3"
max_retries             = 5
notification_threshold  = 5
notification_urgency    = "low"
```

Using environment variables instead of a token in the file:

```bash
export GITHUB_TOKEN="ghp_abc123def456"
```

```toml
# github_token is omitted — will be picked up from GITHUB_TOKEN
github_username = "janedoe"
poll_interval   = 120
repos           = ["myorg/frontend"]
```

## Config file template

The repository includes a `config.example.toml` at the project root:

```toml
# GitHub personal access token
# Required scopes: repo (for private repos) or public_repo (public only)
github_token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Your GitHub username
github_username = "your-username"

# Polling interval in seconds (default: 300 = 5 minutes)
poll_interval = 300

# Optional: filter to specific repos (owner/name format)
# If empty, monitors all repos where you have review requests
# repos = ["owner/repo1", "owner/repo2"]
repos = []

# Log level: "debug", "info", "warning", or "error" (default: "info")
# log_level = "info"

# Send notifications for PRs found on the first poll (default: false)
# notify_on_first_poll = false

# Enable/disable desktop notifications (default: true)
# notifications_enabled = true

# Enable/disable D-Bus interface (default: true)
# dbus_enabled = true

# GitHub API base URL (default: "https://api.github.com")
# github_base_url = "https://github.example.com/api/v3"

# Max HTTP retries for 5xx errors with exponential backoff (default: 3)
# max_retries = 3

# Number of new PRs that trigger individual notifications (default: 3)
# notification_threshold = 3

# Notification urgency: "low", "normal", or "critical" (default: "normal")
# notification_urgency = "normal"
```

## Runtime changes via SIGHUP

Configuration can be reloaded at runtime by sending `SIGHUP` to the daemon:

```bash
systemctl --user reload github-monitor
# or
kill -HUP $(pidof github-monitor)
```

On reload, the daemon re-reads the config file (respecting the original `-c`
path if one was provided at startup), updates the GitHub client settings
(token, username, repos, base URL, retries), and applies the new log level
immediately.

## Programmatic usage

```python
from pathlib import Path
from github_monitor.config import load_config

# Load from default path
cfg = load_config()

# Load from explicit path
cfg = load_config(Path("/etc/github-monitor/config.toml"))

# Load from string path
cfg = load_config("/tmp/test-config.toml")

# Access fields
print(cfg.github_token)              # "ghp_..."
print(cfg.github_username)           # "janedoe"
print(cfg.poll_interval)             # 300
print(cfg.repos)                     # ["owner/repo1", ...]
print(cfg.log_level)                 # "info"
print(cfg.notifications_enabled)     # True
print(cfg.dbus_enabled)              # True
print(cfg.github_base_url)           # "https://api.github.com"
print(cfg.max_retries)               # 3
print(cfg.notification_threshold)    # 3
print(cfg.notification_urgency)      # "normal"
```
