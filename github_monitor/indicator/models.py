from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class PRInfo:
    """Pull request data as received from the daemon over D-Bus."""

    url: str
    title: str
    repo: str
    author: str
    author_avatar_url: str
    number: int
    updated_at: datetime
    review_requested: bool
    assigned: bool


@dataclass(frozen=True)
class DaemonStatus:
    """Daemon status metadata as received over D-Bus."""

    pr_count: int
    last_updated: datetime | None
