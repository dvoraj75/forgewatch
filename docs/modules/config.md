# `config.py` -- API reference

Module: `github_monitor.config`

Handles loading, validating, and representing the daemon's configuration.

## Constants

| Name | Type | Value | Description |
|---|---|---|---|
| `CONFIG_DIR` | `Path` | `~/.config/github-monitor` | Default config directory |
| `CONFIG_PATH` | `Path` | `~/.config/github-monitor/config.toml` | Default config file path |

Internal constants (prefixed with `_`):

| Name | Type | Value | Description |
|---|---|---|---|
| `_REPO_PATTERN` | `re.Pattern` | `^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$` | Regex for validating `owner/name` repo format |
| `_MIN_POLL_INTERVAL` | `int` | `30` | Minimum allowed poll interval in seconds |

## `ConfigError`

```python
class ConfigError(Exception): ...
```

Raised when configuration is invalid or missing. All validation failures produce
a `ConfigError` with a human-readable message describing what went wrong.

**Examples of error messages:**

- `"Config file not found: /path/to/config.toml"`
- `"Invalid TOML in /path/to/config.toml: ..."`
- `"github_token is required"`
- `"github_username is required"`
- `"poll_interval must be an integer, got str"`
- `"poll_interval must be >= 30 seconds, got 10"`
- `"repos must be a list"`
- `"Invalid repo format: 'not-valid' — expected 'owner/name'"`

## `Config`

```python
@dataclass(frozen=True)
class Config:
    github_token: str
    github_username: str
    poll_interval: int = 300
    repos: list[str] = field(default_factory=list)
```

An immutable (frozen) dataclass holding validated configuration values.

| Field | Type | Default | Description |
|---|---|---|---|
| `github_token` | `str` | (required) | GitHub PAT with `repo` scope |
| `github_username` | `str` | (required) | GitHub username for search queries |
| `poll_interval` | `int` | `300` | Poll interval in seconds (>= 30) |
| `repos` | `list[str]` | `[]` | Repo filter (`owner/name` format); empty = all |

The dataclass is frozen, so fields cannot be modified after creation:

```python
cfg = load_config()
cfg.poll_interval = 60  # raises AttributeError
```

## `load_config()`

```python
def load_config(path: Path | str | None = None) -> Config:
```

Load configuration from a TOML file and return a validated `Config` instance.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `Path \| str \| None` | `None` | Explicit config file path. If `None`, resolved via env var or default. |

### Returns

A `Config` instance with all fields validated.

### Raises

- `ConfigError` — if the config file is not found, contains invalid TOML, or
  fails validation

### Behavior

1. Resolves the file path via `_resolve_path(path)`
2. Reads and parses the TOML file
3. Applies `GITHUB_TOKEN` env var override (if set and non-empty)
4. Validates all fields via `_validate()`
5. Returns a `Config` instance

### Example

```python
from github_monitor.config import load_config

# Default path (~/.config/github-monitor/config.toml)
cfg = load_config()

# Explicit path
cfg = load_config("/etc/github-monitor/config.toml")

# String path also works
cfg = load_config("./my-config.toml")
```

## `_resolve_path()` (internal)

```python
def _resolve_path(path: Path | str | None) -> Path:
```

Resolves the config file path using three-tier precedence:

1. If `path` is provided, use it (converting `str` to `Path` if needed)
2. If `GITHUB_MONITOR_CONFIG` env var is set, use its value
3. Fall back to `CONFIG_PATH` (`~/.config/github-monitor/config.toml`)

### Raises

- `ConfigError` — if the resolved path does not exist

## `_validate()` (internal)

```python
def _validate(raw: dict[str, object]) -> Config:
```

Validates the raw TOML dict and returns a `Config` instance.

### Validation rules

1. `github_token` — must be a `str` and non-empty after stripping
2. `github_username` — must be a `str` and non-empty after stripping
3. `poll_interval` — must be an `int` and >= `_MIN_POLL_INTERVAL` (30)
4. `repos` — must be a `list`; each element must be a `str` matching
   `_REPO_PATTERN`

## Tests

17 tests in `tests/test_config.py` covering:

- Happy path (valid config, minimal config, string path)
- Environment variable overrides (`GITHUB_TOKEN`, `GITHUB_MONITOR_CONFIG`, token
  from env when missing in file)
- Validation errors (missing file, invalid TOML, missing token/username, invalid
  poll_interval type/value, invalid repo format, repos not a list)
- Edge cases (empty token/username strings, boundary poll_interval = 30)
