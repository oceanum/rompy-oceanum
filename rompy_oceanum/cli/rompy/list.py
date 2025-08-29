"""List command for rompy-oceanum CLI."""

import sys
import logging
from typing import Optional

import click
import yaml
from oceanum.cli.models import ContextObject

from oceanum.cli.prax.client import PRAXClient


logger = logging.getLogger(__name__)

# Common options for list commands
project_option = click.option(
    "--project",
    default="rompy-oceanum",
    help="Prax project name (default: rompy-oceanum)",
)
org_option = click.option(
    "--org",
    help="Prax organization name (overrides oceanum context)",
)
user_option = click.option(
    "--user",
    help="Prax user email (overrides oceanum context)",
)
stage_option = click.option(
    "--stage",
    default="dev",
    help="Prax stage name (default: dev)",
)


@click.command(name="list", help="List resources in Prax")
@click.argument("resource_type", type=click.Choice(["projects", "pipelines"]))
@project_option
@org_option
@user_option
@stage_option
@click.pass_context
def list_resources(
    ctx,
    resource_type: str,
    project: str,
    org: Optional[str],
    user: Optional[str],
    stage: str,
):
    """
    List resources in Prax using Oceanum CLI context for authentication/config.
    RESOURCE_TYPE: Type of resources to list (projects or pipelines)
    """
    try:
        if resource_type == "projects":
            # Use Oceanum CLI context for authentication/config
            client = PRAXClient(ctx)
            projects = client.list_projects(search="rompy")

            if not projects:
                click.echo("📭 No rompy projects found")
                return

            click.echo("📋 Rompy Projects:")
            for project_item in projects:
                name = getattr(project_item, 'name', 'Unknown')
                status = getattr(project_item, 'status', 'Unknown')
                click.echo(f"   📋 {name} - Status: {status}")
                
        elif resource_type == "pipelines":
            # Use Oceanum CLI context for authentication/config
            client = PRAXClient(ctx)
            pipelines = client.list_pipelines()

            if not pipelines:
                click.echo("📭 No pipelines found in project")
                return

            click.echo(f"📋 Pipelines in project '{project}':")
            for pipeline in pipelines:
                name = getattr(pipeline, 'name', 'Unknown')
                last_run_status = getattr(getattr(pipeline, 'last_run', None), 'status', 'Unknown')
                click.echo(f"   📋 {name} - Last Run Status: {last_run_status}")

    except Exception as e:
        click.echo(f"❌ Failed to list {resource_type}: {e}", err=True)
        sys.exit(1)