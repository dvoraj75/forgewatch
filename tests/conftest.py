from __future__ import annotations

from unittest.mock import AsyncMock


def _mock_process(returncode: int = 0, stderr: bytes = b"", stdout: bytes = b"") -> AsyncMock:
    """Build a mock process that has communicate() and returncode."""
    proc = AsyncMock()
    proc.communicate.return_value = (stdout, stderr)
    proc.returncode = returncode
    return proc
