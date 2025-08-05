"""List command for rompy-oceanum CLI."""

import sys
import logging
from typing import Optional

import click
import yaml
from oceanum.cli.models import ContextObject

from ...prax_client import PraxClientWrapper
from ...config import PraxConfig

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
@click.pass_obj
def list_resources(
    obj: ContextObject,
    resource_type: str,
    project: str,
    org: Optional[str],
    user: Optional[str],
    stage: str,
):
    """List resources in Prax.
    
    RESOURCE_TYPE: Type of resources to list (projects or pipelines)
    """
    try:
        if resource_type == "projects":
            # Get Prax configuration
            prax_config_data = {
                "org": org or (obj.domain.split(".")[0] if "." in obj.domain else obj.domain),
            }

            # Use oceanum's token for authentication
            if obj.token and obj.token.access_token:
                prax_config_data["token"] = obj.token.access_token

            prax_config = PraxConfig.from_env(**prax_config_data)
            if not getattr(prax_config, 'base_url', None):
                click.echo("❌ Prax base_url is missing. Please set PRAX_BASE_URL in your environment or config.", err=True)
                sys.exit(1)
            client = PraxClientWrapper(prax_config)
            # List projects with "rompy" filter
            projects = client.list_projects(search="rompy")

            if not projects:
                click.echo("📭 No rompy projects found")
                return

            click.echo("📋 Rompy Projects:")
            for project_item in projects:
                # Handle both dict and object representations
                if hasattr(project_item, 'name'):
                    name = project_item.name
                else:
                    name = project_item.get("name", "Unknown")
                    
                if hasattr(project_item, 'status'):
                    status = project_item.status
                else:
                    status = project_item.get("status", "Unknown")
                    
                click.echo(f"   📋 {name} - Status: {status}")
                
        elif resource_type == "pipelines":
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
            if not getattr(prax_config, 'base_url', None):
                click.echo("❌ Prax base_url is missing. Please set PRAX_BASE_URL in your environment or config.", err=True)
                sys.exit(1)
            client = PraxClientWrapper(prax_config)
            # List pipelines
            pipelines = client.list_pipelines()

            if not pipelines:
                click.echo("📭 No pipelines found in project")
                return

            click.echo(f"📋 Pipelines in project '{project}':")
            # Handle both list of dicts and list of objects
            for pipeline in pipelines:
                # Extract information from the pipeline object
                name = getattr(pipeline, 'name', 'Unknown')
                
                # Get last run status if available
                last_run_status = "Unknown"
                if hasattr(pipeline, 'last_run') and pipeline.last_run:
                    last_run_status = getattr(pipeline.last_run, 'status', 'Unknown')
                
                click.echo(f"   📋 {name} - Last Run Status: {last_run_status}")

    except Exception as e:
        click.echo(f"❌ Failed to list {resource_type}: {e}", err=True)
        sys.exit(1)