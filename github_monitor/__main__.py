"""Allow ``python -m github_monitor`` to launch the daemon."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from .config import load_config
from .daemon import Daemon


def main() -> None:
    """CLI entry point for github-monitor.

    Parses command-line arguments, configures logging, loads the
    configuration file, and runs the daemon until a shutdown signal
    is received.
    """
    parser = argparse.ArgumentParser(
        description="GitHub PR monitor daemon",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        help="Path to config.toml",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    # CLI --verbose overrides config log_level
    log_level = logging.DEBUG if args.verbose else getattr(logging, config.log_level.upper())

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    daemon = Daemon(config, config_path)

    async def run() -> None:
        try:
            await daemon.start()
        finally:
            await daemon.stop()

    asyncio.run(run())


if __name__ == "__main__":
    main()
