"""CRUD operations for projects in rompy-oceanum CLI."""

import sys
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import click
import yaml
from oceanum.cli.models import ContextObject

from ...client import PraxClient

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--org",
    help="Prax organization name (overrides oceanum context)",
)
@click.pass_obj
@click.pass_context
def project_crud(ctx: click.Context, obj: ContextObject, org: str):
    """CRUD operations for rompy projects in Prax.
    
    This command provides Create, Read, Update, and Delete operations for 
    projects in Prax where rompy pipelines will be deployed.
    
    Examples:
        oceanum rompy project-crud create my-project.yaml
        oceanum rompy project-crud list
        oceanum rompy project-crud get my-project
        oceanum rompy project-crud delete my-project
    """
    # Store org in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['org'] = org
    ctx.obj['context_obj'] = obj


@project_crud.command()
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--name", help="Project name (defaults to filename without extension)")
@click.option("--wait", help="Wait for project to be deployed", default=True, type=bool)
@click.option("--base-url", required=True, help="Oceanum API base URL")
@click.option("--token", required=True, help="Oceanum API token")
@click.option("--org", required=True, help="Organization name")
@click.option("--project", required=True, help="Project name")
@click.option("--stage", default="dev", help="Deployment stage")
@click.pass_context
def create(ctx: click.Context, spec_file: str, name: str, wait: bool, base_url: str, token: str, org: str, project: str, stage: str):
    """Create a new project from a spec file."""
    try:
        # Load spec
        with open(spec_file, 'r') as f:
            spec_data = yaml.safe_load(f)
        # Use provided name or derive from filename
        if not name:
            name = spec_file.split('/')[-1].replace('.yaml', '').replace('.yml', '')
        # Set name in spec if not already set
        if 'name' not in spec_data:
            spec_data['name'] = name
        # Instantiate Oceanum client
        client = PraxClient(base_url=base_url, token=token, org=org, project=project, stage=stage)
        # Submit project spec
        result = client.submit_project_spec(spec_data, wait=wait)
        click.echo(f"✅ Project '{name}' created successfully")
        click.echo(f"📝 Project details: {result}")
    except Exception as e:
        click.echo(f"❌ Failed to create project: {e}", err=True)
        raise click.Abort()


@project_crud.command()
@click.option("--base-url", required=True, help="Oceanum API base URL")
@click.option("--token", required=True, help="Oceanum API token")
@click.option("--org", required=True, help="Organization name")
@click.option("--project", required=True, help="Project name")
@click.option("--stage", default="dev", help="Deployment stage")
@click.pass_context
def list_projects(ctx: click.Context, base_url: str, token: str, org: str, project: str, stage: str):
    """List all projects accessible to the user."""
    try:
        client = PraxClient(base_url=base_url, token=token, org=org, project=project, stage=stage)
        projects = client.list_projects()
        if not projects:
            click.echo("📭 No projects found")
            return
        click.echo("📋 Projects:")
        for project in projects:
            if isinstance(project, dict):
                name = project.get('name', 'Unknown')
                status = project.get('status', 'Unknown')
            else:
                name = str(project)
                status = 'Unknown'
            click.echo(f"   📋 {name} - Status: {status}")
    except Exception as e:
        click.echo(f"❌ Failed to list projects: {e}", err=True)
        raise click.Abort()


@project_crud.command()
@click.argument("project_name")
@click.option("--base-url", required=True, help="Oceanum API base URL")
@click.option("--token", required=True, help="Oceanum API token")
@click.option("--org", required=True, help="Organization name")
@click.option("--project", required=True, help="Project name")
@click.option("--stage", default="dev", help="Deployment stage")
@click.pass_context
def get(ctx: click.Context, project_name: str, base_url: str, token: str, org: str, project: str, stage: str):
    """Get details of a specific project."""
    try:
        client = PraxClient(base_url=base_url, token=token, org=org, project=project, stage=stage)
        project_details = client.get_project(project_name)
        click.echo(f"📋 Details for project '{project_name}':")
        click.echo(yaml.dump(project_details, default_flow_style=False, indent=2))
    except Exception as e:
        click.echo(f"❌ Failed to get project: {e}", err=True)
        raise click.Abort()


@project_crud.command()
@click.argument("project_name")
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
@click.option("--base-url", required=True, help="Oceanum API base URL")
@click.option("--token", required=True, help="Oceanum API token")
@click.option("--org", required=True, help="Organization name")
@click.option("--project", required=True, help="Project name")
@click.option("--stage", default="dev", help="Deployment stage")
@click.pass_context
def delete(ctx: click.Context, project_name: str, base_url: str, token: str, org: str, project: str, stage: str):
    """Delete a project."""
    try:
        client = PraxClient(base_url=base_url, token=token, org=org, project=project, stage=stage)
        client.delete_project(project_name)
        click.echo(f"✅ Project '{project_name}' deleted successfully")
    except Exception as e:
        click.echo(f"❌ Failed to delete project: {e}", err=True)
        raise click.Abort()
