"""Clean rompy CLI implementation that delegates to oceanum prax."""

import click
from oceanum.cli import main
from .run import run
from .status import status
from .logs import logs
from .download import download
from .list import list_group
from .init import init
from .generate import generate_backend_config

@main.group(name="rompy")
def rompy():
    """Rompy model execution commands using Oceanum Prax.

    This CLI provides a simple interface for running rompy wave and ocean
    models on Oceanum's Prax platform. All operations delegate to the
    oceanum prax CLI for execution.
    """
    pass

# Register all subcommands
rompy.add_command(run)
rompy.add_command(status)
rompy.add_command(logs)
rompy.add_command(download)
rompy.add_command(list_group)
rompy.add_command(init)
rompy.add_command(generate_backend_config)

__all__ = ["rompy"]

def get_cli():
    return rompy
