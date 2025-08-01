"""Delete command for rompy-oceanum CLI."""

import sys
import logging
from typing import Optional

import click
import yaml
from oceanum.cli.models import ContextObject

from oceanum.cli.prax.client import PRAXClient
from ...config import PraxConfig

logger = logging.getLogger(__name__)

# Common options for delete commands
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


@click.command(name="delete", help="Delete a resource from Prax")
@click.argument("resource_type", type=click.Choice(["project", "pipeline"]))
@click.argument("resource_name")
@project_option
@org_option
@user_option
@stage_option
@click.confirmation_option(prompt="Are you sure you want to delete this resource?")
@click.pass_obj
def delete_resource(
    obj: ContextObject,
    resource_type: str,
    resource_name: str,
    project: str,
    org: Optional[str],
    user: Optional[str],
    stage: str,
):
    """Delete a resource from Prax.
    
    RESOURCE_TYPE: Type of resource to delete (project or pipeline)
    RESOURCE_NAME: Name of the resource to delete
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
            client = PRAXClient(token=prax_config.token, service=prax_config.base_url)

            # Delete project
            client.delete_project(resource_name)

            click.echo(f"✅ Project '{resource_name}' deleted successfully")
            
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
            client = PRAXClient(token=prax_config.token, service=prax_config.base_url)

            # Delete pipeline
            client.delete_pipeline(resource_name)

            click.echo(f"✅ Pipeline '{resource_name}' deleted successfully from project '{project}'")

    except Exception as e:
        click.echo(f"❌ Failed to delete {resource_type}: {e}", err=True)
        sys.exit(1)