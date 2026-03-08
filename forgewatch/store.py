"""In-memory state store for tracked pull requests with diff computation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .poller import PullRequest


@dataclass(frozen=True)
class StateDiff:
    """Result of comparing two poll cycles.

    All fields are lists of PullRequest objects representing what changed
    between the previous and current poll result.
    """

    new_prs: list[PullRequest] = field(default_factory=list)
    closed_prs: list[PullRequest] = field(default_factory=list)
    updated_prs: list[PullRequest] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Return True if any changes were detected."""
        return bool(self.new_prs or self.closed_prs or self.updated_prs)


@dataclass(frozen=True)
class StoreStatus:
    """Metadata about the current store state."""

    pr_count: int
    last_updated: datetime | None


class PRStore:
    """In-memory store for current PR state with diff computation.

    Holds the latest set of pull requests (keyed by ``html_url``) and
    computes a :class:`StateDiff` each time :meth:`update` is called
    with fresh data from the poller.
    """

    def __init__(self) -> None:
        self._prs: dict[str, PullRequest] = {}
        self._last_updated: datetime | None = None

    def update(self, current_prs: list[PullRequest]) -> StateDiff:
        """Compare *current_prs* with stored state, update store, return diff.

        The diff is computed as follows:

        1. **new** — PRs whose URL is in *current_prs* but not in the store.
        2. **closed** — PRs whose URL is in the store but not in *current_prs*.
        3. **updated** — PRs present in both where ``updated_at`` has changed.

        After computing the diff the internal state is replaced with
        *current_prs*.
        """
        current_by_url = {pr.url: pr for pr in current_prs}
        current_urls = set(current_by_url.keys())
        stored_urls = set(self._prs.keys())

        new_prs = [current_by_url[url] for url in current_urls - stored_urls]

        closed_prs = [self._prs[url] for url in stored_urls - current_urls]

        updated_prs = [
            current_by_url[url]
            for url in current_urls & stored_urls
            if current_by_url[url].updated_at != self._prs[url].updated_at
        ]

        # Replace stored state with current
        self._prs = current_by_url
        self._last_updated = datetime.now(tz=UTC)

        return StateDiff(
            new_prs=new_prs,
            closed_prs=closed_prs,
            updated_prs=updated_prs,
        )

    def get_all(self) -> list[PullRequest]:
        """Return all currently tracked PRs."""
        return list(self._prs.values())

    def get_status(self) -> StoreStatus:
        """Return store metadata."""
        return StoreStatus(
            pr_count=len(self._prs),
            last_updated=self._last_updated,
        )

    def clear(self) -> None:
        """Clear all stored state."""
        self._prs.clear()
        self._last_updated = None
