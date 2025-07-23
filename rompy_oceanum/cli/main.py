"""Main CLI plugin entry point for oceanum rompy integration."""

import click
from oceanum.cli.models import ContextObject


@click.group()
@click.pass_obj
def main(obj: ContextObject):
    """ROMPY integration for Oceanum Prax execution.

    Execute, monitor, and manage rompy ocean model configurations
    using the Oceanum Prax platform with seamless authentication.
    """
    pass


# Import our rompy group command which has all subcommands registered
from .rompy import rompy

# Add the rompy group command directly to main
main.add_command(rompy)

# Alias for oceanum CLI plugin system compatibility
cli = main
