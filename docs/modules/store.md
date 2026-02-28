# `store.py` — API reference

Module: `github_monitor.store`

In-memory state management for tracked pull requests. Computes diffs between
poll cycles to identify new, updated, and closed PRs.

## Data models

### `StateDiff`

```python
@dataclass(frozen=True)
class StateDiff:
    new_prs: list[PullRequest]       # PRs not seen in previous cycle
    closed_prs: list[PullRequest]    # PRs no longer in results
    updated_prs: list[PullRequest]   # PRs where updated_at changed
```

Immutable value object representing what changed between two consecutive poll
cycles. All fields default to empty lists.

**Properties:**

| Property | Type | Description |
|---|---|---|
| `has_changes` | `bool` | `True` if any of the three lists is non-empty |

### `StoreStatus`

```python
@dataclass(frozen=True)
class StoreStatus:
    pr_count: int
    last_updated: datetime | None
```

Immutable snapshot of store metadata.

| Field | Type | Description |
|---|---|---|
| `pr_count` | `int` | Number of PRs currently tracked |
| `last_updated` | `datetime \| None` | UTC timestamp of last `update()` call, or `None` if never updated |

## `PRStore`

Main class — holds the current set of PRs and computes diffs.

### Constructor

```python
PRStore()
```

Creates an empty store with no PRs and `last_updated = None`.

### Methods

#### `update(current_prs: list[PullRequest]) -> StateDiff`

Compare incoming PRs with stored state, replace stored state, return the diff.

**Diff logic:**

1. Build sets of current and stored URLs
2. `new_prs` = URLs in current but not stored
3. `closed_prs` = URLs in stored but not current
4. `updated_prs` = URLs in both where `updated_at` differs
5. Replace internal state with `current_prs`
6. Update `last_updated` to current UTC time

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `current_prs` | `list[PullRequest]` | Fresh PR list from the poller |

**Returns:** `StateDiff` with the changes detected.

#### `get_all() -> list[PullRequest]`

Return all currently tracked PRs as a list.

#### `get_status() -> StoreStatus`

Return a `StoreStatus` snapshot with the current PR count and last update
timestamp.

#### `clear() -> None`

Remove all stored PRs and reset `last_updated` to `None`. A subsequent
`update()` call will treat all incoming PRs as new (same as first poll).

## Usage example

```python
from github_monitor.store import PRStore

store = PRStore()

# First poll — all PRs are new
diff = store.update(prs_from_poller)
print(f"New: {len(diff.new_prs)}, Closed: {len(diff.closed_prs)}")

# Second poll — compute what changed
diff = store.update(prs_from_poller_again)
if diff.has_changes:
    # notify, emit D-Bus signal, etc.
    ...

# Check store state
status = store.get_status()
print(f"Tracking {status.pr_count} PRs, last updated {status.last_updated}")
```

## Design notes

- PRs are keyed by `html_url` (the clickable GitHub URL), which is unique per PR
- Only `updated_at` is compared for the "updated" diff — title or other field
  changes without a timestamp change are not detected (GitHub updates the
  timestamp on any meaningful change)
- The store is not thread-safe; it is designed for single-threaded asyncio use
- `StateDiff` and `StoreStatus` are frozen dataclasses (immutable value objects)
