"""CRUD operations for pipelines in rompy-oceanum CLI."""

import logging
from typing import Optional, Dict, Any

import click
import yaml
from ...client import PraxClient

logger = logging.getLogger(__name__)

@click.group()
@click.option("--base-url", required=True, help="Oceanum Prax API base URL")
@click.option("--token", required=True, help="Oceanum API token")
@click.option("--org", required=True, help="Organization name")
@click.option("--project", required=True, help="Project name")
@click.option("--stage", default="dev", help="Stage name (default: dev)")
@click.option("--user", required=False, help="User email (optional)")
@click.pass_context
def pipeline_crud(ctx: click.Context, base_url: str, token: str, org: str, project: str, stage: str, user: Optional[str]):
    """CRUD operations for rompy pipelines in Oceanum Prax.
    
    Examples:
        oceanum rompy pipelines create my-pipeline.yaml --project my-project --base-url ... --token ... --org ...
        oceanum rompy pipelines list --project my-project --base-url ... --token ... --org ...
        oceanum rompy pipelines get my-pipeline --project my-project --base-url ... --token ... --org ...
        oceanum rompy pipelines update my-pipeline my-updated-pipeline.yaml --project my-project --base-url ... --token ... --org ...
        oceanum rompy pipelines delete my-pipeline --project my-project --base-url ... --token ... --org ...
    """
    ctx.ensure_object(dict)
    ctx.obj['base_url'] = base_url
    ctx.obj['token'] = token
    ctx.obj['org'] = org
    ctx.obj['project'] = project
    ctx.obj['stage'] = stage
    ctx.obj['user'] = user

@pipeline_crud.command()
@click.argument("template_file", type=click.Path(exists=True))
@click.option("--name", help="Pipeline name (defaults to filename without extension)")
@click.pass_context
def create(ctx: click.Context, template_file: str, name: str):
    """Create a new pipeline from a template file."""
    try:
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)
        if not name:
            name = template_file.split('/')[-1].replace('.yaml', '').replace('.yml', '')
        if 'name' not in template_data:
            template_data['name'] = name
        client = PraxClient(
            base_url=ctx.obj['base_url'],
            token=ctx.obj['token'],
            org=ctx.obj['org'],
            project=ctx.obj['project'],
            stage=ctx.obj['stage'],
            user=ctx.obj['user'],
        )
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
        client = PraxClient(
            base_url=ctx.obj['base_url'],
            token=ctx.obj['token'],
            org=ctx.obj['org'],
            project=ctx.obj['project'],
            stage=ctx.obj['stage'],
            user=ctx.obj['user'],
        )
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
        client = PraxClient(
            base_url=ctx.obj['base_url'],
            token=ctx.obj['token'],
            org=ctx.obj['org'],
            project=ctx.obj['project'],
            stage=ctx.obj['stage'],
            user=ctx.obj['user'],
        )
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
        with open(template_file, 'r') as f:
            template_data = yaml.safe_load(f)
        template_data['name'] = pipeline_name
        client = PraxClient(
            base_url=ctx.obj['base_url'],
            token=ctx.obj['token'],
            org=ctx.obj['org'],
            project=ctx.obj['project'],
            stage=ctx.obj['stage'],
            user=ctx.obj['user'],
        )
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
        client = PraxClient(
            base_url=ctx.obj['base_url'],
            token=ctx.obj['token'],
            org=ctx.obj['org'],
            project=ctx.obj['project'],
            stage=ctx.obj['stage'],
            user=ctx.obj['user'],
        )
        client.delete_pipeline(pipeline_name)
        click.echo(f"✅ Pipeline '{pipeline_name}' deleted successfully")
    except Exception as e:
        click.echo(f"❌ Failed to delete pipeline: {e}", err=True)
        raise click.Abort()
