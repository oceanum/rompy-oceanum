"""Pipeline management commands for rompy-oceanum CLI."""

import sys
import logging
from pathlib import Path
from typing import Optional

import click
import yaml
from oceanum.cli.models import ContextObject

from ...client import PraxClient
from ...config import PraxConfig

logger = logging.getLogger(__name__)

# Common options for pipeline commands
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


@click.group(name="pipelines", help="Manage rompy pipelines in Prax projects")
def pipelines():
    """Manage rompy pipelines in Prax projects.
    
    Pipelines are resources within a Prax project. You need to create a project first,
    then deploy pipelines to that project.
    
    Examples:
        oceanum rompy projects create my-project.yaml
        oceanum rompy pipelines create swan-pipeline.yaml --project my-project
        oceanum rompy pipelines list --project my-project
    """
    pass


@pipelines.command(name="create", help="Create/deploy a pipeline template to a project")
@click.argument("template_file", type=click.Path(exists=True))
@click.option("--name", help="Pipeline name (defaults to filename without extension)")
@project_option
@org_option
@user_option
@stage_option
@click.pass_obj
def create_pipeline(
    obj: ContextObject,
    template_file: str,
    name: Optional[str],
    project: str,
    org: Optional[str],
    user: Optional[str],
    stage: str,
):
    """Create/deploy a pipeline template to a project."""
    try:
        # Load template
        with open(template_file, "r") as f:
            template_data = yaml.safe_load(f)

        # Use provided name or derive from filename
        if not name:
            name = Path(template_file).stem

        # Set name in template if not already set
        if "name" not in template_data:
            template_data["name"] = name

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

        # Submit pipeline template
        result = client.submit_pipeline_template(template_data)

        click.echo(f"✅ Pipeline '{name}' created successfully in project '{project}'")
        click.echo(f"📝 Pipeline details: {result}")

    except Exception as e:
        click.echo(f"❌ Failed to create pipeline: {e}", err=True)
        sys.exit(1)


@pipelines.command(name="list", help="List pipelines in a project")
@project_option
@org_option
@user_option
@stage_option
@click.pass_obj
def list_pipelines(
    obj: ContextObject, project: str, org: Optional[str], user: Optional[str], stage: str
):
    """List pipelines in a project."""
    try:
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
        click.echo(f"❌ Failed to list pipelines: {e}", err=True)
        sys.exit(1)


@pipelines.command(name="describe", help="Describe a pipeline")
@click.argument("pipeline_name")
@project_option
@org_option
@user_option
@stage_option
@click.pass_obj
def describe_pipeline(
    obj: ContextObject,
    pipeline_name: str,
    project: str,
    org: Optional[str],
    user: Optional[str],
    stage: str,
):
    """Describe a pipeline."""
    try:
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
        pipeline = client.get_pipeline(pipeline_name)

        click.echo(f"📋 Details for pipeline '{pipeline_name}':")
        click.echo(yaml.dump(pipeline, default_flow_style=False, indent=2))

    except Exception as e:
        click.echo(f"❌ Failed to describe pipeline: {e}", err=True)
        sys.exit(1)


@pipelines.command(name="delete", help="Delete a pipeline from a project")
@click.argument("pipeline_name")
@project_option
@org_option
@user_option
@stage_option
@click.confirmation_option(
    prompt="Are you sure you want to delete this pipeline from the project?"
)
@click.pass_obj
def delete_pipeline(
    obj: ContextObject,
    pipeline_name: str,
    project: str,
    org: Optional[str],
    user: Optional[str],
    stage: str,
):
    """Delete a pipeline from a project."""
    try:
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

        # Delete pipeline
        client.delete_pipeline(pipeline_name)

        click.echo(f"✅ Pipeline '{pipeline_name}' deleted successfully from project '{project}'")

    except Exception as e:
        click.echo(f"❌ Failed to delete pipeline: {e}", err=True)
        sys.exit(1)


@pipelines.command(name="deploy-default", help="Deploy the default pipeline template")
@project_option
@org_option
@user_option
@stage_option
@click.pass_obj
def deploy_default(
    obj: ContextObject, project: str, org: Optional[str], user: Optional[str], stage: str
):
    """Deploy the default pipeline template to a project."""
    try:
        click.echo(f"🚀 Deploying default pipeline template to project: {project}")

        # Get the path to the default template
        template_path = (
            Path(__file__).parent.parent.parent / "pipeline_templates" / "swan.yaml"
        )

        if not template_path.exists():
            click.echo(f"❌ Default template not found at {template_path}", err=True)
            sys.exit(1)

        # Load template
        with open(template_path, "r") as f:
            template_data = yaml.safe_load(f)

        # Get Prax configuration
        prax_config_data = {
            "org": org or (obj.domain.split(".")[0] if "." in obj.domain else obj.domain),
            "project": project,
            "stage": stage,
        }

        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token

        # Get user email from context if available
        if user:
            prax_config_data["user"] = user
        elif obj.token and hasattr(obj.token, "email"):
            prax_config_data["user"] = obj.token.email

        prax_config = PraxConfig.from_env(**prax_config_data)
        client = PraxClient(prax_config)

        # Submit pipeline template
        result = client.submit_pipeline_template(template_data)

        click.echo("✅ Default pipeline template deployed successfully!")
        click.echo(
            f"💡 You can now run models using: oceanum rompy run config.yml swan --pipeline-name swan-from-rompy --project {project}"
        )

    except Exception as e:
        click.echo(f"❌ Failed to deploy default pipeline template: {e}", err=True)
        sys.exit(1)