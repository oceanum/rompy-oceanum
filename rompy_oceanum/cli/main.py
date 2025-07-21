"""Main CLI plugin entry point for oceanum rompy integration."""

import click
from oceanum.cli.common.models import ContextObject


@click.group()
@click.pass_obj
def main(obj: ContextObject):
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

# Add commands to the main group
main.add_command(run)
main.add_command(status)
main.add_command(logs)
main.add_command(sync)
main.add_command(init)
main.add_command(pipelines)
