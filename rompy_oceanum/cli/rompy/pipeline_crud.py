"""CRUD operations for pipelines in rompy-oceanum CLI."""

import logging
from typing import Optional, Dict, Any

import click
import yaml
from oceanum.cli.models import ContextObject

from ...client import PraxClient
from ...config import PraxConfig

logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--project",
    default="rompy-pipelines",
    help="Prax project name (default: rompy-pipelines)",
)
@click.option(
    "--org",
    help="Prax organization name (overrides oceanum context)",
)
@click.pass_obj
@click.pass_context
def pipeline_crud(ctx: click.Context, obj: ContextObject, project: str, org: str):
    """CRUD operations for rompy pipelines in Prax.
    
    This command provides Create, Read, Update, and Delete operations for 
    pipeline templates in a Prax project.
    
    Examples:
        oceanum rompy pipeline-crud create my-pipeline.yaml
        oceanum rompy pipeline-crud list
        oceanum rompy pipeline-crud get my-pipeline
        oceanum rompy pipeline-crud update my-pipeline my-updated-pipeline.yaml
        oceanum rompy pipeline-crud delete my-pipeline
    """
    # Store project and org in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['project'] = project
    ctx.obj['org'] = org
    ctx.obj['context_obj'] = obj


@pipeline_crud.command()
@click.argument("template_file", type=click.Path(exists=True))
@click.option("--name", help="Pipeline name (defaults to filename without extension)")
@click.pass_context
def create(ctx: click.Context, template_file: str, name: str):
    """Create a new pipeline from a template file."""
    try:
        # Load template
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)
        
        # Use provided name or derive from filename
        if not name:
            name = template_file.split('/')[-1].replace('.yaml', '').replace('.yml', '')
        
        # Set name in template if not already set
        if 'name' not in template_data:
            template_data['name'] = name
        
        # Get Prax configuration
        obj = ctx.obj['context_obj']
        prax_config_data = {
            "org": ctx.obj['org'] or (obj.domain.split('.')[0] if '.' in obj.domain else obj.domain),
            "project": ctx.obj['project'],
        }
        
        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token
        
        prax_config = PraxConfig.from_env(**prax_config_data)
        client = PraxClient(prax_config)
        
        # Submit pipeline template
        result = client.submit_pipeline_template(template_data)
        
        click.echo(f"✅ Pipeline '{name}' created successfully")
        click.echo(f"📝 Pipeline details: {result}")
        
    except Exception as e:
        click.echo(f"❌ Failed to create pipeline: {e}", err=True)
        raise click.Abort()


@pipeline_crud.command()
@click.pass_context
def list_pipelines(ctx: click.Context):
    """List all pipelines in the project."""
    try:
        # Get Prax configuration
        obj = ctx.obj['context_obj']
        prax_config_data = {
            "org": ctx.obj['org'] or (obj.domain.split('.')[0] if '.' in obj.domain else obj.domain),
            "project": ctx.obj['project'],
        }
        
        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token
        
        prax_config = PraxConfig.from_env(**prax_config_data)
        client = PraxClient(prax_config)
        
        # List pipelines
        pipelines = client.list_pipelines()
        
        if not pipelines:
            click.echo("📭 No pipelines found in project")
            return
        
        click.echo(f"📋 Pipelines in project '{ctx.obj['project']}':")
        for pipeline in pipelines:
            name = pipeline.get('name', 'Unknown')
            status = pipeline.get('status', 'Unknown')
            click.echo(f"   📋 {name} - Status: {status}")
            
    except Exception as e:
        click.echo(f"❌ Failed to list pipelines: {e}", err=True)
        raise click.Abort()


@pipeline_crud.command()
@click.argument("pipeline_name")
@click.pass_context
def get(ctx: click.Context, pipeline_name: str):
    """Get details of a specific pipeline."""
    try:
        # Get Prax configuration
        obj = ctx.obj['context_obj']
        prax_config_data = {
            "org": ctx.obj['org'] or (obj.domain.split('.')[0] if '.' in obj.domain else obj.domain),
            "project": ctx.obj['project'],
        }
        
        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token
        
        prax_config = PraxConfig.from_env(**prax_config_data)
        client = PraxClient(prax_config)
        
        # Get pipeline details
        pipeline = client.get_pipeline(pipeline_name)
        
        click.echo(f"📋 Details for pipeline '{pipeline_name}':")
        click.echo(yaml.dump(pipeline, default_flow_style=False, indent=2))
            
    except Exception as e:
        click.echo(f"❌ Failed to get pipeline: {e}", err=True)
        raise click.Abort()


@pipeline_crud.command()
@click.argument("pipeline_name")
@click.argument("template_file", type=click.Path(exists=True))
@click.pass_context
def update(ctx: click.Context, pipeline_name: str, template_file: str):
    """Update an existing pipeline with a new template."""
    try:
        # Load template
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)
        
        # Set name in template to match pipeline name
        template_data['name'] = pipeline_name
        
        # Get Prax configuration
        obj = ctx.obj['context_obj']
        prax_config_data = {
            "org": ctx.obj['org'] or (obj.domain.split('.')[0] if '.' in obj.domain else obj.domain),
            "project": ctx.obj['project'],
        }
        
        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token
        
        prax_config = PraxConfig.from_env(**prax_config_data)
        client = PraxClient(prax_config)
        
        # Update pipeline
        result = client.update_pipeline(pipeline_name, template_data)
        
        click.echo(f"✅ Pipeline '{pipeline_name}' updated successfully")
        click.echo(f"📝 Pipeline details: {result}")
        
    except Exception as e:
        click.echo(f"❌ Failed to update pipeline: {e}", err=True)
        raise click.Abort()


@pipeline_crud.command()
@click.argument("pipeline_name")
@click.confirmation_option(prompt="Are you sure you want to delete this pipeline?")
@click.pass_context
def delete(ctx: click.Context, pipeline_name: str):
    """Delete a pipeline from the project."""
    try:
        # Get Prax configuration
        obj = ctx.obj['context_obj']
        prax_config_data = {
            "org": ctx.obj['org'] or (obj.domain.split('.')[0] if '.' in obj.domain else obj.domain),
            "project": ctx.obj['project'],
        }
        
        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token
        
        prax_config = PraxConfig.from_env(**prax_config_data)
        client = PraxClient(prax_config)
        
        # Delete pipeline
        client.delete_pipeline(pipeline_name)
        
        click.echo(f"✅ Pipeline '{pipeline_name}' deleted successfully")
        
    except Exception as e:
        click.echo(f"❌ Failed to delete pipeline: {e}", err=True)
        raise click.Abort()