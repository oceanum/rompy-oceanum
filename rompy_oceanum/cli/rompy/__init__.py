"""Clean rompy CLI implementation that delegates to oceanum prax."""

import click
from .run import run
from .status import status
from .logs import logs
from .download import download
from .list import list_group
from .init import init
from .generate import generate_backend_config


@click.group(name="rompy")
def rompy_group():
    """Rompy model execution commands using Oceanum Prax.

    This CLI provides a simple interface for running rompy wave and ocean
    models on Oceanum's Prax platform. All operations delegate to the
    oceanum prax CLI for execution.
    """
    pass


# Register all subcommands
rompy_group.add_command(run)
rompy_group.add_command(status)
rompy_group.add_command(logs)
rompy_group.add_command(download)
rompy_group.add_command(list_group)
rompy_group.add_command(init)
rompy_group.add_command(generate_backend_config)


# Export for entry point
__all__ = ["rompy_group", "rompy"]

# Alias for oceanum CLI discovery
rompy = rompy_group
