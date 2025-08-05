"""CRUD operations for projects in rompy-oceanum CLI."""

import sys
import logging
from typing import Optional, Dict, Any
from pathlib import Path

import click
import yaml
from oceanum.cli.models import ContextObject

from oceanum.cli.prax.client import PRAXClient
from ...config import PraxConfig

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
@click.pass_context
def create(ctx: click.Context, spec_file: str, name: str, wait: bool):
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
        
        # Get Prax configuration
        obj = ctx.obj['context_obj']
        prax_config_data = {
            "org": ctx.obj['org'] or (obj.domain.split('.')[0] if '.' in obj.domain else obj.domain),
        }
        
        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token
        
        prax_config = PraxConfig.from_env(**prax_config_data)
        if not getattr(prax_config, 'base_url', None):
    click.echo("❌ Prax base_url is missing. Please set PRAX_BASE_URL in your environment or config.", err=True)
    raise click.Abort()
client = PRAXClient(token=prax_config.token, service=prax_config.base_url)
        
        # Submit project spec
        result = client.submit_project_spec(spec_data, wait=wait)
        
        click.echo(f"✅ Project '{name}' created successfully")
        click.echo(f"📝 Project details: {result}")
        
    except Exception as e:
        click.echo(f"❌ Failed to create project: {e}", err=True)
        raise click.Abort()


@project_crud.command()
@click.pass_context
def list_projects(ctx: click.Context):
    """List all projects accessible to the user."""
    try:
        # Get Prax configuration
        obj = ctx.obj['context_obj']
        prax_config_data = {
            "org": ctx.obj['org'] or (obj.domain.split('.')[0] if '.' in obj.domain else obj.domain),
        }
        
        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token
        
        prax_config = PraxConfig.from_env(**prax_config_data)
        if not getattr(prax_config, 'base_url', None):
    click.echo("❌ Prax base_url is missing. Please set PRAX_BASE_URL in your environment or config.", err=True)
    raise click.Abort()
client = PRAXClient(token=prax_config.token, service=prax_config.base_url)
        
        # List projects
        projects = client.list_projects()
        
        if not projects:
            click.echo("📭 No projects found")
            return
        
        click.echo("📋 Projects:")
        for project in projects:
            name = project.get('name', 'Unknown')
            status = project.get('status', 'Unknown')
            click.echo(f"   📋 {name} - Status: {status}")
            
    except Exception as e:
        click.echo(f"❌ Failed to list projects: {e}", err=True)
        raise click.Abort()


@project_crud.command()
@click.argument("project_name")
@click.pass_context
def get(ctx: click.Context, project_name: str):
    """Get details of a specific project."""
    try:
        # Get Prax configuration
        obj = ctx.obj['context_obj']
        prax_config_data = {
            "org": ctx.obj['org'] or (obj.domain.split('.')[0] if '.' in obj.domain else obj.domain),
        }
        
        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token
        
        prax_config = PraxConfig.from_env(**prax_config_data)
        if not getattr(prax_config, 'base_url', None):
    click.echo("❌ Prax base_url is missing. Please set PRAX_BASE_URL in your environment or config.", err=True)
    raise click.Abort()
client = PRAXClient(token=prax_config.token, service=prax_config.base_url)
        
        # Get project details
        project = client.get_project(project_name)
        
        click.echo(f"📋 Details for project '{project_name}':")
        click.echo(yaml.dump(project, default_flow_style=False, indent=2))
            
    except Exception as e:
        click.echo(f"❌ Failed to get project: {e}", err=True)
        raise click.Abort()


@project_crud.command()
@click.argument("project_name")
@click.confirmation_option(prompt="Are you sure you want to delete this project?")
@click.pass_context
def delete(ctx: click.Context, project_name: str):
    """Delete a project."""
    try:
        # Get Prax configuration
        obj = ctx.obj['context_obj']
        prax_config_data = {
            "org": ctx.obj['org'] or (obj.domain.split('.')[0] if '.' in obj.domain else obj.domain),
        }
        
        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token
        
        prax_config = PraxConfig.from_env(**prax_config_data)
        if not getattr(prax_config, 'base_url', None):
    click.echo("❌ Prax base_url is missing. Please set PRAX_BASE_URL in your environment or config.", err=True)
    raise click.Abort()
client = PRAXClient(token=prax_config.token, service=prax_config.base_url)
        
        # Delete project
        client.delete_project(project_name)
        
        click.echo(f"✅ Project '{project_name}' deleted successfully")
        
    except Exception as e:
        click.echo(f"❌ Failed to delete project: {e}", err=True)
        raise click.Abort()