# Systemd integration

> **Status:** Not yet implemented (Phase 8).

This document will cover running github-monitor as a systemd user service,
including:

- The `github-monitor.service` unit file
- Installation to `~/.config/systemd/user/`
- Enabling and starting the service
- Viewing logs with `journalctl --user`
- Security hardening options (`ProtectSystem`, `NoNewPrivileges`, etc.)
- Automatic restart on failure

See `implementation.md` Phase 8 for the planned implementation details.
