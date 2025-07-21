"""Main entry point module for rompy run command."""

from .run import run

# Export the command for entry point discovery
__all__ = ["run"]
