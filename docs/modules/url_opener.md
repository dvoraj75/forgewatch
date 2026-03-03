# `url_opener.py` -- API reference

Module: `github_monitor.url_opener`

Shared utility for opening URLs in the default browser. Used by both the
notifier (for notification click-to-open) and the indicator (for PR row
clicks). Tries the XDG Desktop Portal first (works from sandboxed systemd
services, Flatpak, and Snap environments), then falls back to `xdg-open`.

This module was extracted from the notifier to avoid code duplication once the
indicator also needed URL-opening capabilities.

## Constants

| Constant | Value | Description |
|---|---|---|
| `_PORTAL_BUS_NAME` | `org.freedesktop.portal.Desktop` | XDG Desktop Portal D-Bus bus name |
| `_PORTAL_OBJECT_PATH` | `/org/freedesktop/portal/desktop` | XDG Desktop Portal D-Bus object path |
| `_PORTAL_INTERFACE` | `org.freedesktop.portal.OpenURI` | XDG Desktop Portal OpenURI interface |

## Functions

### `open_url()`

```python
async def open_url(url: str) -> None:
```

Open a URL in the default browser. This is the main public entry point.

Tries the XDG Desktop Portal first via `_open_url_portal()`. If the portal
is unavailable (returns `False`), falls back to `_open_url_xdg()`.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `url` | `str` | The URL to open |

### `_open_url_portal()`

```python
async def _open_url_portal(url: str) -> bool:
```

Opens a URL via the XDG Desktop Portal over D-Bus. Sends a raw `Message` to
`org.freedesktop.portal.OpenURI.OpenURI` instead of using `dbus-next`'s
introspection + proxy pattern -- this avoids a `dbus-next` bug where
introspecting the portal object fails because other interfaces on that path
expose property names with hyphens (e.g. `power-saver-enabled` from
`org.freedesktop.portal.PowerProfileMonitor`), which `dbus-next` rejects as
invalid member names.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `url` | `str` | The URL to open |

**Returns:** `True` on success, `False` on any failure (connection error,
D-Bus error reply, timeout). The caller uses the return value to decide
whether to fall back to `xdg-open`.

**Error handling:** All exceptions (`DBusError`, `OSError`, `ValueError`,
`TimeoutError`) are caught and logged at debug level. The function never
raises.

**D-Bus message details:**

| Field | Value |
|---|---|
| Destination | `org.freedesktop.portal.Desktop` |
| Path | `/org/freedesktop/portal/desktop` |
| Interface | `org.freedesktop.portal.OpenURI` |
| Member | `OpenURI` |
| Signature | `ssa{sv}` |
| Body | `["", url, {}]` |

The bus connection is always disconnected in a `finally` block, even on
failure.

### `_open_url_xdg()`

```python
async def _open_url_xdg(url: str) -> None:
```

Opens a URL via `xdg-open` as an async subprocess. Used as a fallback when
the XDG Desktop Portal is unavailable.

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `url` | `str` | The URL to open |

**Error handling:**

- Non-zero exit code: logs a warning with the exit code and stderr output.
- `xdg-open` not found (`FileNotFoundError`): logs a warning.
- Other `OSError`: logs at debug level with traceback.

The function never raises exceptions.

## Usage example

```python
from github_monitor.url_opener import open_url

# Open a PR in the default browser
await open_url("https://github.com/owner/repo/pull/42")
```

## Design notes

- Uses a raw D-Bus `Message` instead of `dbus-next`'s `bus.introspect()` +
  proxy objects to work around a `dbus-next` bug with hyphenated property
  names on the portal object path
- The portal approach is necessary because `xdg-open` fails silently inside
  the systemd sandbox when the browser is a Snap package (Snap's
  `snap-confine` rejects the restricted permissions set by
  `ProtectSystem=strict` and `NoNewPrivileges=true`)
- The `xdg-open` fallback works for development (running outside systemd) and
  for minimal window managers that lack a portal backend
- Stdout is discarded for `xdg-open`; stderr is captured for error reporting
- The module is shared between the notifier and the indicator to avoid
  duplicating the portal workaround logic
