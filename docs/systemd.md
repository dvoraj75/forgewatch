# Systemd integration

This document covers running github-monitor as a systemd user service, including
installation, management, security hardening, and troubleshooting.

## Overview

github-monitor is designed to run as a **systemd user service** — a background
process managed by your user session (not root). This means:

- It starts automatically when you log in
- It restarts on failure
- Logs are captured by journald
- No root privileges required

## Prerequisites

- github-monitor installed and accessible at `~/.local/bin/github-monitor`
  (e.g. via `uv tool install .` or `pip install --user .`)
- A valid configuration file at `~/.config/github-monitor/config.toml`
- D-Bus session bus available (standard on any Linux desktop)
- `systemd --user` running (standard on modern Linux distributions)

## The service unit file

The service file is located at `systemd/github-monitor.service` in the project
repository:

```ini
[Unit]
Description=GitHub PR Monitor
After=network-online.target dbus.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=%h/.local/bin/github-monitor
Restart=on-failure
RestartSec=10
Environment=GITHUB_TOKEN=

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=%h/.config/github-monitor

[Install]
WantedBy=default.target
```

### Directive reference

#### `[Unit]` section

| Directive | Value | Purpose |
|---|---|---|
| `Description` | `GitHub PR Monitor` | Human-readable name shown in `systemctl status` |
| `After` | `network-online.target dbus.service` | Wait for network and D-Bus before starting |
| `Wants` | `network-online.target` | Soft dependency on network (daemon still starts if network is delayed) |

#### `[Service]` section

| Directive | Value | Purpose |
|---|---|---|
| `Type` | `simple` | The process started by `ExecStart` is the main daemon process |
| `ExecStart` | `%h/.local/bin/github-monitor` | Path to the executable (`%h` expands to `$HOME`) |
| `Restart` | `on-failure` | Restart the service if it exits with a non-zero code |
| `RestartSec` | `10` | Wait 10 seconds before restarting after failure |
| `Environment` | `GITHUB_TOKEN=` | Placeholder for the GitHub token (see [Token configuration](#token-configuration)) |

#### Security hardening

| Directive | Value | Purpose |
|---|---|---|
| `NoNewPrivileges` | `true` | Prevent the process from gaining additional privileges via setuid/setgid |
| `ProtectSystem` | `strict` | Mount the entire filesystem read-only (except explicitly allowed paths) |
| `ProtectHome` | `read-only` | Mount `$HOME` read-only |
| `ReadWritePaths` | `%h/.config/github-monitor` | Allow write access to the config directory only |

These directives follow the principle of least privilege. The daemon only needs
to read its config file and make network requests — it does not need write
access to the filesystem.

#### `[Install]` section

| Directive | Value | Purpose |
|---|---|---|
| `WantedBy` | `default.target` | Start the service when the user session starts (i.e. on login) |

## Installation

### Automated (recommended)

The easiest way to install is with the included install script, which handles
prerequisites, package installation, interactive configuration, and systemd
setup:

```bash
./install.sh
```

### Manual

```bash
# 1. Create the systemd user directory (if it doesn't exist)
mkdir -p ~/.config/systemd/user/

# 2. Copy the service file
cp systemd/github-monitor.service ~/.config/systemd/user/

# 3. Reload systemd to pick up the new unit file
systemctl --user daemon-reload

# 4. Enable the service (starts on login) and start it now
systemctl --user enable --now github-monitor
```

## Token configuration

The service file includes an `Environment=GITHUB_TOKEN=` line as a placeholder.
You have several options for providing the token:

### Option 1: Edit the service file (simplest)

Set the token directly in the service file:

```ini
Environment=GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Then reload:

```bash
systemctl --user daemon-reload
systemctl --user restart github-monitor
```

### Option 2: Use the config file

If `github_token` is set in `~/.config/github-monitor/config.toml`, the
daemon will use that value. The `Environment=GITHUB_TOKEN=` line can be left
empty — it only takes effect if set to a non-empty value.

### Option 3: Environment drop-in file

Create an override file to keep secrets out of the main service file:

```bash
mkdir -p ~/.config/systemd/user/github-monitor.service.d/
cat > ~/.config/systemd/user/github-monitor.service.d/token.conf << 'EOF'
[Service]
Environment=GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
systemctl --user daemon-reload
systemctl --user restart github-monitor
```

This approach keeps the token separate from the service file and is not
overwritten when you update the service file from the repository.

## Managing the service

### Check status

```bash
systemctl --user status github-monitor
```

### View logs

```bash
# Follow logs in real time
journalctl --user -u github-monitor -f

# Show last 50 lines
journalctl --user -u github-monitor -n 50

# Show logs since last boot
journalctl --user -u github-monitor -b

# Show only errors
journalctl --user -u github-monitor -p err
```

### Restart / stop

```bash
# Restart (e.g. after config change)
systemctl --user restart github-monitor

# Stop
systemctl --user stop github-monitor
```

### Reload configuration (without restart)

The daemon handles `SIGHUP` for config reload:

```bash
systemctl --user kill -s HUP github-monitor
```

This reloads the config file and recreates the HTTP session (picks up new
token, poll interval, repo filter, etc.) without losing the current in-memory
state.

### Disable (prevent auto-start on login)

```bash
systemctl --user disable github-monitor
```

## Updating

To update to the latest version:

```bash
./update.sh
```

This pulls the latest code, re-installs the package, updates the systemd
service file, and restarts the daemon. Your configuration is never touched.

The script is git-aware -- it skips `git pull` if you have uncommitted changes
or are on a non-main branch (unless you confirm).

To update manually instead:

```bash
git pull
uv tool install . --force
cp systemd/github-monitor.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user restart github-monitor
```

## Troubleshooting

### Service fails to start

**Check the logs first:**

```bash
journalctl --user -u github-monitor -n 20 --no-pager
```

**Common causes:**

| Symptom | Cause | Fix |
|---|---|---|
| `ExecStart not found` | `github-monitor` is not installed at `~/.local/bin/` | Install with `uv tool install .` or `pip install --user .`, or edit `ExecStart` to point to the correct path |
| `ConfigError: github_token must be non-empty` | No token configured | Set the token via `Environment=GITHUB_TOKEN=...` in the service file, a drop-in, or the config file |
| `ConfigError: ... config.toml not found` | Missing config file | Create `~/.config/github-monitor/config.toml` from `config.example.toml` |
| `FileNotFoundError: notify-send` | `libnotify-bin` not installed | Install with `sudo apt install libnotify-bin` (notifications are optional — the daemon still runs) |

### Service starts but no D-Bus interface

**Check that the session bus is available:**

```bash
busctl --user list | grep github_monitor
```

If the service is running but the bus name does not appear, check that
`DBUS_SESSION_BUS_ADDRESS` is set in the systemd environment:

```bash
systemctl --user show-environment | grep DBUS
```

If it is not set, you may need to import the environment:

```bash
dbus-update-activation-environment --systemd DBUS_SESSION_BUS_ADDRESS
```

### Custom ExecStart path

If `github-monitor` is installed in a virtualenv or non-standard location,
edit the `ExecStart` line:

```ini
# Example: uv-managed virtualenv
ExecStart=/home/youruser/.venv/bin/github-monitor

# Example: pipx
ExecStart=/home/youruser/.local/bin/github-monitor
```

Remember to run `systemctl --user daemon-reload` after editing the service file.

### Clicking a notification does not open the browser

When running as a systemd service with security hardening, notification
click-to-open uses the **XDG Desktop Portal** (D-Bus) to open URLs instead of
calling `xdg-open` directly. This is necessary because `xdg-open` can fail
silently inside the sandbox — notably when the browser is a Snap package
(Snap's `snap-confine` rejects the restricted permissions set by
`ProtectSystem=strict` and `NoNewPrivileges=true`).

**Requirements for click-to-open:**

- The `xdg-desktop-portal` service must be running (standard on GNOME, KDE,
  XFCE, and most other desktop environments)
- A portal backend must be installed (e.g. `xdg-desktop-portal-gtk`,
  `xdg-desktop-portal-gnome`, or `xdg-desktop-portal-kde`)

**Verify the portal is available:**

```bash
gdbus call --session \
  -d org.freedesktop.portal.Desktop \
  -o /org/freedesktop/portal/desktop \
  -m org.freedesktop.portal.OpenURI.OpenURI \
  "" "https://example.com" {}
```

If this opens a browser tab, the portal is working. If it fails, install the
portal packages:

```bash
# Debian / Ubuntu
sudo apt install xdg-desktop-portal xdg-desktop-portal-gtk
```

If the portal is unavailable, the notifier falls back to `xdg-open`
automatically (which works when running outside the systemd sandbox, e.g.
during development).

## Uninstallation

```bash
# Stop and disable the service
systemctl --user stop github-monitor
systemctl --user disable github-monitor

# Remove the service file
rm ~/.config/systemd/user/github-monitor.service

# Remove any drop-in overrides
rm -rf ~/.config/systemd/user/github-monitor.service.d/

# Reload systemd
systemctl --user daemon-reload
```
