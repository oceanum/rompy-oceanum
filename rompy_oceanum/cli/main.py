"""Main CLI plugin entry point for oceanum rompy integration."""

import click
from oceanum.cli.models import ContextObject


from oceanum.cli import main as oceanum_main

@oceanum_main.group(name='rompy', help='ROMPY integration for Oceanum Prax execution.')
@click.pass_obj
def rompy(obj: ContextObject):
    """ROMPY integration for Oceanum Prax execution.

    Prepare and submit rompy ocean model configurations
    for execution on the Oceanum Prax platform.
    
    For deployment and monitoring of runs, use the 'oceanum prax' commands.
    """
    pass

# Import and register subcommands
from .rompy.run import run
from .rompy.init import init
from .rompy.pipelines import pipelines

# Add commands to the rompy group
rompy.add_command(run)
rompy.add_command(init)
rompy.add_command(pipelines)

# For plugin system compatibility
cli = rompy

