"""Main CLI plugin entry point for oceanum rompy integration."""

import click
from oceanum.cli.models import ContextObject

from oceanum.cli import main as oceanum_main

# Import commands
from .rompy.run import run
from .rompy.init import init
from .rompy.create import create_resource
from .rompy.list import list_resources
from .rompy.describe import describe_resource
from .rompy.delete import delete_resource
from .rompy.logs import logs

@oceanum_main.group(name='rompy', help='ROMPY integration for Oceanum Prax execution.')
@click.pass_obj
def rompy(obj: ContextObject):
    """ROMPY integration for Oceanum Prax execution.

    Prepare and submit rompy ocean model configurations
    for execution on the Oceanum Prax platform.
    
    For deployment and monitoring of runs, use the 'oceanum prax' commands.
    """
    pass

# Add commands to the rompy group - following prax pattern: oceanum rompy <action> <resource>
rompy.add_command(run)
rompy.add_command(init)
rompy.add_command(create_resource, name="create")
rompy.add_command(list_resources, name="list")
rompy.add_command(describe_resource, name="describe")
rompy.add_command(delete_resource, name="delete")
rompy.add_command(logs)

# For plugin system compatibility
cli = rompy

