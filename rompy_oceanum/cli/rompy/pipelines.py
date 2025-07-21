"""Pipeline management command for rompy-oceanum CLI."""

import logging
from pathlib import Path
from typing import Dict, Any

import click
import yaml
from oceanum.cli.common.models import ContextObject

from ...config import PraxConfig
from ...client import PraxClient

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--project",
    envvar="PRAX_PROJECT",
    help="Prax project (overrides oceanum context)"
)
@click.option(
    "--stage",
    default="dev",
    envvar="PRAX_STAGE",
    help="Deployment stage"
)
@click.option(
    "--list",
    "list_pipelines",
    is_flag=True,
    help="List all available pipelines"
)
@click.option(
    "--deploy",
    help="Deploy pipeline from template file"
)
@click.option(
    "--pipeline-name",
    help="Pipeline name for deployment"
)
@click.option(
    "--model-type",
    type=click.Choice(["swan", "schism", "ww3"]),
    help="Model type for template selection"
)
@click.option(
    "--show-templates",
    is_flag=True,
    help="Show available pipeline templates"
)
@click.option(
    "--create-template",
    help="Create a new pipeline template file"
)
@click.pass_obj
def pipelines(
    obj: ContextObject,
    project,
    stage,
    list_pipelines,
    deploy,
    pipeline_name,
    model_type,
    show_templates,
    create_template
):
    """Manage Prax pipelines for rompy execution.

    Examples:
        oceanum rompy pipelines --list
        oceanum rompy pipelines --show-templates
        oceanum rompy pipelines --deploy template.yaml --pipeline-name my-swan-pipeline
        oceanum rompy pipelines --create-template my-template.yaml --model-type swan
    """

    if show_templates:
        _show_available_templates()
        return

    if create_template:
        _create_pipeline_template(create_template, model_type)
        return

    # Create Prax configuration
    try:
        prax_config_data = {
            "org": obj.domain.split('.')[0] if '.' in obj.domain else obj.domain,
            "stage": stage
        }

        if project:
            prax_config_data["project"] = project

        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token

        prax_config = PraxConfig.from_env(**prax_config_data)

    except ValueError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        return

    if list_pipelines:
        _list_pipelines(prax_config)
        return

    if deploy:
        if not pipeline_name:
            click.echo("❌ --pipeline-name is required when deploying", err=True)
            return
        _deploy_pipeline(prax_config, deploy, pipeline_name)
        return

    # Default action - show help
    click.echo("💡 Use --help to see available options")
    click.echo("Quick commands:")
    click.echo("  oceanum rompy pipelines --list")
    click.echo("  oceanum rompy pipelines --show-templates")


def _list_pipelines(prax_config: PraxConfig):
    """List available pipelines."""
    click.echo("🔍 Listing available pipelines...")

    try:
        client = PraxClient(prax_config)
        pipelines = client.list_pipelines()

        if pipelines:
            click.echo(f"✅ Found {len(pipelines)} pipelines in {prax_config.org}/{prax_config.project}:")
            click.echo()

            for pipeline in pipelines:
                name = pipeline.get('name', 'unknown')
                desc = pipeline.get('description', 'No description')
                status = pipeline.get('status', 'unknown')
                created = pipeline.get('created_at', 'unknown')

                click.echo(f"📋 {name}")
                click.echo(f"   Description: {desc}")
                click.echo(f"   Status: {status}")
                click.echo(f"   Created: {created}")
                click.echo()

            click.echo("💡 Usage:")
            click.echo("   oceanum rompy run config.yml swan --pipeline-name <pipeline_name>")

        else:
            click.echo("📭 No pipelines found in this project")
            click.echo("💡 Deploy a pipeline:")
            click.echo("   oceanum rompy pipelines --deploy template.yaml --pipeline-name my-pipeline")

    except Exception as e:
        click.echo(f"❌ Failed to list pipelines: {e}", err=True)
        click.echo("💡 Make sure you're authenticated: oceanum auth login")


def _deploy_pipeline(prax_config: PraxConfig, template_path: str, pipeline_name: str):
    """Deploy a pipeline from template."""
    click.echo(f"🚀 Deploying pipeline '{pipeline_name}' from template: {template_path}")

    try:
        template_file = Path(template_path)
        if not template_file.exists():
            # Try to find template in package
            package_template = (
                Path(__file__).parent.parent.parent
                / "pipeline_templates"
                / template_path
            )
            if package_template.exists():
                template_file = package_template
                click.echo(f"📁 Using packaged template: {package_template}")
            else:
                click.echo(f"❌ Template file not found: {template_path}", err=True)
                click.echo("💡 Available templates:")
                _show_available_templates()
                return

        client = PraxClient(prax_config)

        if client.deploy_pipeline(pipeline_name, str(template_file)):
            click.echo(f"✅ Pipeline '{pipeline_name}' deployed successfully!")
            click.echo("💡 You can now use it:")
            click.echo(f"   oceanum rompy run config.yml <model> --pipeline-name {pipeline_name}")
        else:
            click.echo(f"❌ Failed to deploy pipeline '{pipeline_name}'", err=True)

    except Exception as e:
        click.echo(f"❌ Deployment failed: {e}", err=True)


def _show_available_templates():
    """Show available pipeline templates."""
    click.echo("📚 Available Pipeline Templates:")
    click.echo()

    # Check for built-in templates
    template_dir = Path(__file__).parent.parent.parent / "pipeline_templates"

    if template_dir.exists():
        templates = list(template_dir.glob("*.yaml")) + list(template_dir.glob("*.yml"))

        if templates:
            click.echo("🔧 Built-in templates:")
            for template in templates:
                try:
                    with open(template, 'r') as f:
                        template_data = yaml.safe_load(f)

                    name = template.stem
                    desc = template_data.get('metadata', {}).get('description', 'No description')
                    model_type = template_data.get('metadata', {}).get('labels', {}).get('model-type', 'generic')

                    click.echo(f"   📋 {name}.yaml - {model_type}")
                    click.echo(f"      {desc}")

                except Exception:
                    click.echo(f"   📋 {template.name}")

            click.echo()
        else:
            click.echo("⚠️  No built-in templates found")

    # Show example usage
    click.echo("💡 Usage:")
    click.echo("   oceanum rompy pipelines --deploy swan-basic.yaml --pipeline-name my-swan")
    click.echo("   oceanum rompy pipelines --create-template my-template.yaml --model-type swan")


def _create_pipeline_template(template_path: str, model_type: str = None):
    """Create a new pipeline template file."""
    click.echo(f"📝 Creating pipeline template: {template_path}")

    if not model_type:
        model_type = click.prompt("Model type", type=click.Choice(["swan", "schism", "ww3", "generic"]))

    template_data = _get_template_structure(model_type)

    try:
        output_file = Path(template_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False, indent=2)

        click.echo(f"✅ Template created: {output_file}")
        click.echo("💡 Customize the template and deploy with:")
        click.echo(f"   oceanum rompy pipelines --deploy {template_path} --pipeline-name my-pipeline")

    except Exception as e:
        click.echo(f"❌ Failed to create template: {e}", err=True)


def _get_template_structure(model_type: str) -> Dict[str, Any]:
    """Get template structure for a model type."""

    base_template = {
        "apiVersion": "v1",
        "kind": "Pipeline",
        "metadata": {
            "name": f"rompy-{model_type}-pipeline",
            "description": f"ROMPY {model_type.upper()} model execution pipeline",
            "labels": {
                "model-type": model_type,
                "framework": "rompy",
                "created-by": "rompy-oceanum-cli"
            }
        },
        "spec": {
            "resources": {
                "cpu": "4",
                "memory": "8Gi",
                "timeout": "1h"
            },
            "environment": {
                "ROMPY_MODEL": model_type,
                "OMP_NUM_THREADS": "4"
            },
            "steps": [
                {
                    "name": "setup",
                    "image": "oceanum/rompy:latest",
                    "command": ["python", "-c", "import rompy; print('ROMPY initialized')"]
                },
                {
                    "name": "execute",
                    "image": "oceanum/rompy:latest",
                    "command": ["python", "-m", "rompy.cli", "run", "${rompy-config}"],
                    "env": [
                        {"name": "ROMPY_CONFIG", "value": "${rompy-config}"},
                        {"name": "DATAMESH_TOKEN", "value": "${datamesh-token}"}
                    ]
                },
                {
                    "name": "postprocess",
                    "image": "oceanum/rompy:latest",
                    "command": ["python", "-m", "rompy.postprocess"],
                    "condition": "success"
                }
            ],
            "postprocess": {
                "processor": "datamesh",
                "tags": [model_type, "oceanum", "rompy"],
                "metadata": {
                    "model_type": model_type,
                    "generated_by": "rompy-oceanum-cli"
                }
            }
        }
    }

    # Model-specific customizations
    if model_type == "swan":
        base_template["spec"]["resources"]["memory"] = "4Gi"
        base_template["spec"]["environment"]["SWAN_THREADS"] = "4"

    elif model_type == "schism":
        base_template["spec"]["resources"]["cpu"] = "8"
        base_template["spec"]["resources"]["memory"] = "16Gi"
        base_template["spec"]["environment"]["SCHISM_NPROCS"] = "8"

    elif model_type == "ww3":
        base_template["spec"]["resources"]["memory"] = "8Gi"
        base_template["spec"]["environment"]["WW3_THREADS"] = "4"

    return base_template
