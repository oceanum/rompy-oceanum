"""Describe command for rompy-oceanum CLI."""

import sys
import logging
from typing import Optional

import click
import yaml
from oceanum.cli.models import ContextObject

from ...client import PraxClient
from ...config import PraxConfig

logger = logging.getLogger(__name__)

# Common options for describe commands
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


@click.command(name="describe", help="Describe a resource in Prax")
@click.argument("resource_type", type=click.Choice(["project", "pipeline"]))
@click.argument("resource_name")
@project_option
@org_option
@user_option
@stage_option
@click.pass_obj
def describe_resource(
    obj: ContextObject,
    resource_type: str,
    resource_name: str,
    project: str,
    org: Optional[str],
    user: Optional[str],
    stage: str,
):
    """Describe a resource in Prax.
    
    RESOURCE_TYPE: Type of resource to describe (project or pipeline)
    RESOURCE_NAME: Name of the resource to describe
    """
    try:
        if resource_type == "project":
            # Get Prax configuration
            prax_config_data = {
                "org": org or (obj.domain.split(".")[0] if "." in obj.domain else obj.domain),
            }

            # Use oceanum's token for authentication
            if obj.token and obj.token.access_token:
                prax_config_data["token"] = obj.token.access_token

            prax_config = PraxConfig.from_env(**prax_config_data)
            client = PraxClient(prax_config)

            # Get project details
            project_details = client.get_project(resource_name)

            click.echo(f"📋 Details for project '{resource_name}':")
            click.echo(yaml.dump(project_details, default_flow_style=False, indent=2))
            
        elif resource_type == "pipeline":
            # Get Prax configuration
            prax_config_data = {
                "org": org or (obj.domain.split(".")[0] if "." in obj.domain else obj.domain),
                "project": project,
                "stage": stage,
            }

            # Use oceanum's token for authentication
            if obj.token and obj.token.access_token:
                prax_config_data["token"] = obj.token.access_token

            prax_config = PraxConfig.from_env(**prax_config_data)
            client = PraxClient(prax_config)

            # Get pipeline details
            pipeline = client.get_pipeline(resource_name)

            click.echo(f"📋 Details for pipeline '{resource_name}':")
            click.echo(yaml.dump(pipeline, default_flow_style=False, indent=2))

    except Exception as e:
        click.echo(f"❌ Failed to describe {resource_type}: {e}", err=True)
        sys.exit(1)