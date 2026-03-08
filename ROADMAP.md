# Roadmap

This document outlines the planned development direction for `forgewatch`.

---

## v1.3.1 — Polish & Ship

**Theme:** Finalize current dev work, last release under the `github-monitor` name.

### Added

- Dynamic tooltip on the tray icon showing connection state, open PR count, and review-requested status
- Version read from package metadata (`importlib.metadata`) instead of hardcoded

### Changed

- Move avatar cache from `/tmp/github-monitor-avatars` to `XDG_CACHE_HOME` (`~/.cache/forgewatch/avatars`)

### Fixed

- Indicator tests failing on systems with GTK installed — `gi` module stubs now always override `sys.modules`

---

## v1.4.0 — Rebrand + PyPI Publishing

**Theme:** New identity and public distribution on PyPI.

This is the largest near-term milestone, broken into two phases.

### Phase 1: Rebrand

| Task | Detail |
|---|---|
| Remove deprecated shell scripts | Remove `install.sh`, `update.sh`, `uninstall.sh` — CLI replacements shipped in v1.3.0 |
| Finalize new name | Verify PyPI availability, GitHub repo/org availability, no trademark conflicts |
| Rename Python package | `forgewatch/` → `<new_name>/`, update all internal imports |
| Rename CLI entry points | `forgewatch` → `<new-cli>`, `forgewatch-indicator` → `<new-cli>-indicator` |
| Update D-Bus bus name | `org.forgewatch.Daemon` → `org.<new_name>.Daemon` |
| Update systemd service files | Bundled templates and reference copies — new unit names, new `ExecStart` paths |
| Update config directory | `~/.config/forgewatch/` → `~/.config/<new-name>/` with migration logic for existing users |
| Update all metadata | `pyproject.toml`, README, CHANGELOG, AGENTS.md, all docs |
| Update icon/notification identity | `--app-name` in notify-send, icon filenames, resource paths |
| Update CI workflow | Branch names, paths, action references |
| Rename GitHub repository | `dvoraj75/forgewatch` → new name |
| Add migration path | Detect old config dir, old systemd units, old D-Bus name — auto-migrate or print instructions |

### Phase 2: PyPI Publishing

| Task | Detail |
|---|---|
| Test on TestPyPI | Publish a release candidate to test.pypi.org, verify `pip install` works end-to-end |
| Add GitHub Actions publish workflow | Trigger on GitHub Release creation, use `pypa/gh-action-pypi-publish` with OIDC trusted publisher |
| Set up Trusted Publisher (OIDC) | Configure PyPI to trust the GitHub Actions workflow (preferred over API tokens) |
| Verify build output | Ensure `hatchling` produces correct sdist + wheel with all package data (SVG icons, systemd templates) |
| Add `py.typed` marker | For downstream type checking support |
| Write installation docs | `pip install <new-name>`, `pipx install <new-name>`, `uv tool install <new-name>` |
| First PyPI release | Tag `v1.4.0`, create GitHub Release, automated publish |

---

## v1.5.0 — Quality of Life

**Theme:** Polish the user experience based on early PyPI feedback.

| Task | Detail |
|---|---|
| Multi-Python CI testing | Add Python 3.14 to the test matrix (currently only 3.13) |
| Configurable reconnect interval | Expose `_RECONNECT_INTERVAL_S` (hardcoded 10s) in config |
| Configurable indicator window size | Expose `_WINDOW_WIDTH` / `_MAX_WINDOW_HEIGHT` (400×500) in config |
| Pagination cap warning | Log a warning when `_MAX_PAGES` (10) is reached — user may be missing PRs |
| Better first-run experience | Detect missing config and print actionable setup instructions instead of a traceback |
| Notification grouping improvements | Group notifications by repo, allow per-repo notification settings |
| Config validation improvements | More descriptive error messages, suggest fixes for common mistakes |
| Shell completions | Generate Bash/Zsh/Fish completions for the CLI |

---

## v1.6.0 — Broader GitHub Monitoring

**Theme:** Expand beyond pull requests to become a full GitHub monitor.

| Task | Detail |
|---|---|
| **Issue monitoring** | Watch issues assigned to you or where you're mentioned — new dataclass, new query in poller, new notification type |
| **CI/Actions status** | Monitor workflow run status for your PRs — show pass/fail in indicator, notify on failure |
| **Review comments/threads** | Notify when someone comments on your PR or requests changes |
| **Release monitoring** | Watch specific repos for new releases |
| Unified event model | Refactor `PullRequest` into a polymorphic event system (`GitHubEvent` base + specialized subclasses) |
| Filter configuration | Per-event-type enable/disable in config (e.g. `[events.issues]`, `[events.ci]`, `[events.releases]`) |
| Update D-Bus interface | New methods/signals for different event types, backward-compatible with v1.x indicator |
| Update indicator window | Tabs or sections for different event types, filtering controls |
| Update notification logic | Different urgency/grouping per event type |

---

## v1.7.0 — Advanced Features

**Theme:** Power user capabilities for engaged users.

| Task | Detail |
|---|---|
| **Multiple accounts/orgs** | Monitor multiple GitHub accounts or Enterprise instances simultaneously |
| **Webhook mode (optional)** | Tiny HTTP server to receive GitHub webhooks for near-instant notifications; falls back to polling when not configured |
| **Custom notification actions** | Shell commands triggered by specific events (e.g. auto-checkout a PR branch) |
| **Persistent state** | SQLite-backed store for PR history, seen/unseen tracking across daemon restarts |
| **Quiet hours** | Configurable time windows when notifications are suppressed (D-Bus state still updates) |
| **PR label/team filtering** | Filter PRs by labels, teams, or draft status in config |
| **Metrics/stats** | Track response times, notification counts, API usage over time |
| **Plugin system** | Python plugins for custom event handlers (hook into the poll cycle) |

---

## v2.0.0 — Cross-Platform (Future Vision)

**Theme:** Beyond Linux — macOS and Windows support.

This is a long-term vision, not for immediate planning.

| Task | Detail |
|---|---|
| Abstract platform layer | Replace D-Bus with platform-agnostic IPC (Unix socket + JSON-RPC or gRPC) |
| macOS support | `UNUserNotificationCenter` for notifications, `launchd` for service management, `rumps` or NSStatusItem for tray |
| Windows/WSL support | `win10toast`/PowerShell notifications, Windows service or Task Scheduler |
| Platform-specific packaging | Homebrew formula (macOS), AUR package (Arch), `.deb` (Debian/Ubuntu), Flatpak |
| Web dashboard alternative | Optional localhost web UI as a cross-platform alternative to the GTK indicator |
| GitHub App auth | Support GitHub App installation tokens for org-wide monitoring (in addition to PAT) |

---

## Ongoing / Cross-Cutting

These apply across all versions:

| Area | Tasks |
|---|---|
| **Testing** | Maintain 90%+ coverage, add integration tests, consider property-based testing (Hypothesis) for data models |
| **Documentation** | Keep docs in sync, add user guides for new features, consider a docs site (MkDocs) once on PyPI |
| **Security** | Continue `pip-audit` in CI, add Dependabot/Renovate for dependency updates, consider `bandit` for security linting |
| **Performance** | Profile memory for long-running daemon, connection pooling improvements, GitHub API response caching |
| **Community** | Respond to issues/PRs, add `SECURITY.md`, consider `GOVERNANCE.md` if contributors join |
