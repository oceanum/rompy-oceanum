"""Main CLI plugin entry point for oceanum rompy integration."""

import click
from oceanum.cli.models import ContextObject


from oceanum.cli import main as oceanum_main

@oceanum_main.group(name='rompy', help='ROMPY integration for Oceanum Prax execution.')
@click.pass_obj
def rompy(obj: ContextObject):
    """ROMPY integration for Oceanum Prax execution.

    Execute, monitor, and manage rompy ocean model configurations
    using the Oceanum Prax platform with seamless authentication.
    """
    pass

# Import and register subcommands directly
from .rompy.run import run
from .rompy.status import status
from .rompy.logs import logs
from .rompy.sync import sync
from .rompy.init import init
from .rompy.pipelines import pipelines

# Add commands to the rompy group
rompy.add_command(run)
rompy.add_command(status)
rompy.add_command(logs)
rompy.add_command(sync)
rompy.add_command(init)
rompy.add_command(pipelines)

# For plugin system compatibility
cli = rompy

