# Configuration

github-monitor is configured via a TOML file and optional environment variable
overrides.

## Config file location

The config file path is resolved in this order:

1. **Explicit path** — passed directly to `load_config(path)` or via the `-c` /
   `--config` CLI flag
2. **`GITHUB_MONITOR_CONFIG` env var** — if set, its value is used as the config
   file path
3. **Default path** — `~/.config/github-monitor/config.toml`

If no config file is found at the resolved path, a `ConfigError` is raised.

## Fields

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `github_token` | string | Yes | — | GitHub personal access token (PAT) with `repo` scope |
| `github_username` | string | Yes | — | Your GitHub username (used in search queries) |
| `poll_interval` | integer | No | `300` | Seconds between poll cycles (minimum: 30) |
| `repos` | list of strings | No | `[]` | Repository filter in `owner/name` format; empty = all repos |

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

- `github_token` — must be a non-empty string
- `github_username` — must be a non-empty string
- `poll_interval` — must be an integer >= 30
- `repos` — must be a list; each entry must match the pattern
  `^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$` (i.e., `owner/name`)

## Example config

A minimal configuration with only required fields:

```toml
github_token    = "ghp_abc123def456"
github_username = "janedoe"
```

This uses defaults: `poll_interval = 300`, `repos = []` (all repositories).

A full configuration:

```toml
github_token    = "ghp_abc123def456"
github_username = "janedoe"
poll_interval   = 60
repos           = ["myorg/frontend", "myorg/backend", "otherorg/shared-lib"]
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
# GitHub personal access token (classic) – needs `repo` scope
github_token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Your GitHub username (used in search queries)
github_username = "your-username"

# How often to poll GitHub, in seconds (minimum 30)
poll_interval = 300

# Limit to specific repos (empty list = all repos you have access to)
repos = []
# repos = ["owner/repo1", "owner/repo2"]
```

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
print(cfg.github_token)       # "ghp_..."
print(cfg.github_username)    # "janedoe"
print(cfg.poll_interval)      # 300
print(cfg.repos)              # ["owner/repo1", ...]
```
