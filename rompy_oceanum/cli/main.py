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
from .rompy.pipeline_crud import pipeline_crud
from .rompy.project_crud import project_crud

# Add commands to the rompy group
rompy.add_command(run)
rompy.add_command(init)
rompy.add_command(pipelines)
rompy.add_command(pipeline_crud, name='pipeline-crud')  # Rename pipeline_crud to pipeline-crud
rompy.add_command(project_crud, name='projects')   # Add project CRUD operations

# For plugin system compatibility
cli = rompy

