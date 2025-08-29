"""Delete command for rompy-oceanum CLI."""

import sys
import logging
from typing import Optional

import click
from oceanum.cli.prax.client import PRAXClient

logger = logging.getLogger(__name__)

@click.command(name="delete", help="Delete a resource from Oceanum Prax")
@click.argument("resource_type", type=click.Choice(["project", "pipeline"]))
@click.argument("resource_name")
@click.option("--org", envvar="PRAX_ORG", help="Prax organization (overrides oceanum context)")
@click.option("--user", envvar="PRAX_USER", help="Prax user email (overrides oceanum context)")
@click.option("--project", envvar="PRAX_PROJECT", help="Prax project (overrides oceanum context)")
@click.option("--stage", envvar="PRAX_STAGE", help="Prax stage (overrides oceanum context)")

@click.confirmation_option(prompt="Are you sure you want to delete this resource?")
@click.pass_context
def delete_resource(
    ctx,
    resource_type: str,
    resource_name: str,
    org,
    user,
    project,
    stage,
):
    """Delete a resource from Oceanum Prax.
    
    RESOURCE_TYPE: Type of resource to delete (project or pipeline)
    RESOURCE_NAME: Name of the resource to delete
    """
    try:
        client = PRAXClient(ctx)
        if resource_type == "project":
            result = client.delete_project(resource_name, org=org, user=user, project=project, stage=stage)
            if isinstance(result, str):
                click.echo(f"705 Project '{resource_name}' deleted successfully")
            else:
                click.echo(f"74c Failed to delete project: {getattr(result, 'detail', result)}", err=True)
                sys.exit(1)
        elif resource_type == "pipeline":
            click.echo("74c Pipeline deletion is not supported by the backend. Only project deletion is available.", err=True)
            sys.exit(1)
        elif resource_type == "pipeline":
            click.echo("❌ Pipeline deletion is not supported by the backend. Only project deletion is available.", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Failed to delete {resource_type}: {e}", err=True)
        sys.exit(1)
