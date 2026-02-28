# `daemon.py` -- API reference

Module: `github_monitor.daemon`

> **Status:** Not yet implemented (Phase 7).

This module will contain the main `Daemon` class that orchestrates all
components: configuration loading, poll loop, state management, notifications,
D-Bus registration, and Unix signal handling (SIGTERM/SIGINT for shutdown,
SIGHUP for config reload).

See `implementation.md` Phase 7 for the planned API and implementation details.
