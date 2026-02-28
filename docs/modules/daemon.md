# `daemon.py` -- API reference

Module: `github_monitor.daemon`

The main orchestrator that wires together all components: configuration
loading, GitHub API polling, state management, desktop notifications, D-Bus
service registration, and Unix signal handling.

## `Daemon`

The central class that manages the daemon lifecycle.

### Constructor

```python
Daemon(config: Config)
```

| Parameter | Type | Description |
|---|---|---|
| `config` | `Config` | Validated configuration (from `load_config()`) |

Creates the following internal components:

| Attribute | Type | Description |
|---|---|---|
| `config` | `Config` | Current configuration (mutable — updated on SIGHUP reload) |
| `store` | `PRStore` | In-memory state store for tracked PRs |
| `client` | `GitHubClient` | Async GitHub API client |
| `bus` | `MessageBus \| None` | D-Bus connection (set during `start()`) |
| `interface` | `GithubMonitorInterface \| None` | D-Bus interface (set during `start()`) |

### `async start() -> None`

Initialise all components and enter the poll loop. This method blocks until
a shutdown signal is received. The startup sequence is:

1. Start the GitHub client (creates an `aiohttp` session)
2. Set up the D-Bus service (connect, export interface, request bus name)
3. Register Unix signal handlers (`SIGTERM`, `SIGINT`, `SIGHUP`)
4. Enter the poll loop

### `async stop() -> None`

Clean shutdown: close the HTTP session and disconnect from D-Bus. Should
always be called after `start()` returns — typically in a `try/finally` block.

### `async _poll_loop() -> None`

Main polling loop. Repeatedly calls `_poll_once()` and then waits for the
configured `poll_interval` seconds before polling again.

Uses an `asyncio.Event` for the wait, so that a shutdown signal (SIGTERM /
SIGINT) can wake the loop immediately rather than blocking up to
`poll_interval` seconds. This provides responsive shutdown behaviour.

### `async _poll_once() -> None`

Single poll cycle:

1. `client.fetch_all()` — fetch all review-requested and assigned PRs
2. `store.update(prs)` — compute the diff against previous state
3. If there are new PRs **and** this is not the first poll:
   `notify_new_prs(diff.new_prs)`
4. If the diff has any changes: emit `interface.PullRequestsChanged()`

**First-poll notification suppression:** On the very first poll cycle, all PRs
appear as "new" because the store starts empty. To avoid a flood of
notifications on daemon startup, desktop notifications are suppressed for the
first cycle. The D-Bus signal is still emitted so that external tools can
populate their state.

**Error handling:** All exceptions during a poll cycle are caught and logged.
The daemon continues running and retries on the next cycle.

### `_handle_shutdown() -> None`

Synchronous handler for `SIGTERM` and `SIGINT`. Sets `_running = False` and
signals the shutdown event to wake the poll loop immediately.

### `_handle_reload() -> None`

Synchronous handler for `SIGHUP`. Schedules an async config reload task on
the running event loop (signal handlers cannot be async).

### `async _reload_config() -> None`

Reload the configuration file and recreate the HTTP session:

1. Call `load_config()` (uses default path resolution)
2. Close the current aiohttp session
3. Call `client.update_config()` with the new values
4. Start a fresh aiohttp session (picks up new token/headers)

If any step fails, the error is logged and the daemon continues with its
previous configuration.

## Data flow

```
Timer fires
    │
    ▼
Daemon._poll_once()
    │
    ├── client.fetch_all()      ──► GitHub Search API
    │
    ├── store.update(prs)       ──► StateDiff
    │
    ├── if new PRs (and not first poll):
    │   └── notify_new_prs()    ──► notify-send
    │
    └── if any changes:
        └── interface.PullRequestsChanged()  ──► D-Bus signal
```

## Signal handling

| Signal | Handler | Behaviour |
|---|---|---|
| `SIGTERM` | `_handle_shutdown()` | Graceful shutdown — exits poll loop immediately |
| `SIGINT` | `_handle_shutdown()` | Same as SIGTERM (Ctrl+C in terminal) |
| `SIGHUP` | `_handle_reload()` | Reload config from disk, recreate HTTP session |

## Usage example

```python
import asyncio
from github_monitor.config import load_config
from github_monitor.daemon import Daemon

config = load_config()
daemon = Daemon(config)

async def run():
    try:
        await daemon.start()
    finally:
        await daemon.stop()

asyncio.run(run())
```

This is exactly what `__main__.py` does, with the addition of argument
parsing and logging setup.

## CLI entry point (`__main__.py`)

The `main()` function in `__main__.py` provides the command-line interface:

```
usage: github-monitor [-h] [-c CONFIG] [-v]

GitHub PR monitor daemon

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to config.toml
  -v, --verbose         Enable debug logging
```

| Flag | Description |
|---|---|
| `-c`, `--config` | Path to a TOML config file (overrides default path resolution) |
| `-v`, `--verbose` | Set log level to DEBUG (default: INFO) |

The entry point is registered in `pyproject.toml` as `github-monitor`, so
after installation it can be invoked directly:

```bash
github-monitor                          # run with defaults
github-monitor -v                       # debug logging
github-monitor -c /path/to/config.toml  # custom config
```

## Design notes

- The poll loop uses `asyncio.wait_for(event.wait(), timeout=...)` rather
  than `asyncio.sleep()`. This makes shutdown immediate — the event is set by
  the SIGTERM/SIGINT handler, waking the wait without blocking for the
  remaining poll interval
- First-poll notification suppression prevents a burst of notifications when
  the daemon starts with many existing review requests. The D-Bus signal still
  fires so panel plugins can populate their state
- SIGHUP config reload closes and restarts the HTTP session to ensure a new
  token (if changed) is picked up in the session headers. The reload is
  scheduled as a task because signal handlers cannot be async
- The `_reload_config()` task stores a reference via `add_done_callback()` to
  prevent garbage collection before completion (ruff RUF006)
- All poll cycle errors are caught and logged — the daemon never crashes from
  a transient GitHub API failure
