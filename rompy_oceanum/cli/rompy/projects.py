"""Project management commands for rompy-oceanum CLI."""

import sys
import logging
from typing import Optional
from pathlib import Path

import click
import yaml
from oceanum.cli.models import ContextObject

from ...client import PraxClient
from ...config import PraxConfig

logger = logging.getLogger(__name__)

# Common options for project commands
org_option = click.option(
    "--org",
    help="Prax organization name (overrides oceanum context)",
)
user_option = click.option(
    "--user",
    help="Prax user email (overrides oceanum context)",
)


@click.group(name="projects", help="Manage rompy projects in Prax")
def projects():
    """Manage rompy projects in Prax.
    
    Projects are the top-level containers for pipelines and other resources in Prax.
    You need to create a project before you can deploy pipelines to it.
    
    Examples:
        oceanum rompy projects create my-project.yaml
        oceanum rompy projects list
        oceanum rompy projects describe my-project
    """
    pass


@projects.command(name="create", help="Create a new project from a spec file")
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--name", help="Project name (defaults to filename without extension)")
@click.option("--wait", help="Wait for project to be deployed", default=True, type=bool)
@org_option
@user_option
@click.pass_obj
def create_project(
    obj: ContextObject,
    spec_file: str,
    name: Optional[str],
    wait: bool,
    org: Optional[str],
    user: Optional[str],
):
    """Create a new project from a spec file."""
    try:
        # Load spec
        with open(spec_file, "r") as f:
            spec_data = yaml.safe_load(f)

        # Use provided name or derive from filename
        if not name:
            name = Path(spec_file).stem

        # Set name in spec if not already set
        if "name" not in spec_data:
            spec_data["name"] = name

        # Get Prax configuration
        prax_config_data = {
            "org": org or (obj.domain.split(".")[0] if "." in obj.domain else obj.domain),
        }

        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token

        prax_config = PraxConfig.from_env(**prax_config_data)
        client = PraxClient(prax_config)

        # Submit project spec
        result = client.submit_project_spec(spec_data, wait=wait)

        click.echo(f"✅ Project '{name}' created successfully")
        click.echo(f"📝 Project details: {result}")

    except Exception as e:
        click.echo(f"❌ Failed to create project: {e}", err=True)
        sys.exit(1)


@projects.command(name="list", help="List all projects accessible to the user")
@org_option
@user_option
@click.pass_obj
def list_projects(obj: ContextObject, org: Optional[str], user: Optional[str]):
    """List all projects accessible to the user."""
    try:
        # Get Prax configuration
        prax_config_data = {
            "org": org or (obj.domain.split(".")[0] if "." in obj.domain else obj.domain),
        }

        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token

        prax_config = PraxConfig.from_env(**prax_config_data)
        client = PraxClient(prax_config)

        # List projects
        projects = client.list_projects()

        if not projects:
            click.echo("📭 No projects found")
            return

        click.echo("📋 Projects:")
        for project in projects:
            name = project.get("name", "Unknown")
            status = project.get("status", "Unknown")
            click.echo(f"   📋 {name} - Status: {status}")

    except Exception as e:
        click.echo(f"❌ Failed to list projects: {e}", err=True)
        sys.exit(1)


@projects.command(name="describe", help="Describe a project")
@click.argument("project_name")
@org_option
@user_option
@click.pass_obj
def describe_project(
    obj: ContextObject, project_name: str, org: Optional[str], user: Optional[str]
):
    """Describe a project."""
    try:
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
        project = client.get_project(project_name)

        click.echo(f"📋 Details for project '{project_name}':")
        click.echo(yaml.dump(project, default_flow_style=False, indent=2))

    except Exception as e:
        click.echo(f"❌ Failed to describe project: {e}", err=True)
        sys.exit(1)


@projects.command(name="delete", help="Delete a project")
@click.argument("project_name")
@org_option
@user_option
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
@click.pass_obj
def delete_project(
    obj: ContextObject, project_name: str, org: Optional[str], user: Optional[str]
):
    """Delete a project."""
    try:
        # Get Prax configuration
        prax_config_data = {
            "org": org or (obj.domain.split(".")[0] if "." in obj.domain else obj.domain),
        }

        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token

        prax_config = PraxConfig.from_env(**prax_config_data)
        client = PraxClient(prax_config)

        # Delete project
        client.delete_project(project_name)

        click.echo(f"✅ Project '{project_name}' deleted successfully")

    except Exception as e:
        click.echo(f"❌ Failed to delete project: {e}", err=True)
        sys.exit(1)