"""Allow ``python -m github_monitor`` to launch the daemon."""

from .daemon import run


def main() -> None:
    """CLI entry point."""
    run()


if __name__ == "__main__":
    main()
