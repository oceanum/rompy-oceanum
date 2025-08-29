"""Describe command for rompy-oceanum CLI."""

import sys
import logging
from typing import Optional

import click
import yaml
from oceanum.cli.prax.client import PRAXClient

logger = logging.getLogger(__name__)

@click.command(name="describe", help="Describe a resource in Oceanum Prax")
@click.argument("resource_type", type=click.Choice(["project", "pipeline"]))
@click.argument("resource_name")
@click.option("--org", envvar="PRAX_ORG", help="Prax organization (overrides oceanum context)")
@click.option("--user", envvar="PRAX_USER", help="Prax user email (overrides oceanum context)")
@click.option("--project", envvar="PRAX_PROJECT", help="Prax project (overrides oceanum context)")
@click.option("--stage", envvar="PRAX_STAGE", help="Prax stage (overrides oceanum context)")

@click.pass_context
def describe_resource(
    ctx,
    resource_type: str,
    resource_name: str,
    org,
    user,
    project,
    stage,
):
    """Describe a resource in Oceanum Prax.
    
    RESOURCE_TYPE: Type of resource to describe (project or pipeline)
    RESOURCE_NAME: Name of the resource to describe
    """
    try:
        client = PRAXClient(ctx)
        if resource_type == "project":
            project_details = client.get_project(resource_name, org=org, user=user, project=project, stage=stage)
            click.echo(f"f4cb Details for project '{resource_name}':")
            click.echo(yaml.dump(project_details.dict(), default_flow_style=False, indent=2))
        elif resource_type == "pipeline":
            pipeline = client.get_pipeline(resource_name, org=org, user=user, project=project, stage=stage)
            click.echo(f"f4cb Details for pipeline '{resource_name}':")
            click.echo(yaml.dump(pipeline.dict(), default_flow_style=False, indent=2))
    except Exception as e:
        click.echo(f"❌ Failed to describe {resource_type}: {e}", err=True)
        sys.exit(1)
