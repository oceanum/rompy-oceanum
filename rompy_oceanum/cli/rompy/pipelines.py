'''Pipeline template management command for rompy-oceanum CLI.'''

import logging
from pathlib import Path
from typing import Dict, Any

import click
import yaml
from oceanum.cli.models import ContextObject

logger = logging.getLogger(__name__)


@click.command()
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
@click.option(
    "--project-name",
    default="rompy-pipelines",
    help="Prax project name for rompy pipelines (default: rompy-pipelines)"
)
@click.pass_obj
def pipelines(
    obj: ContextObject,
    model_type,
    show_templates,
    create_template,
    project_name
):
    """Manage pipeline templates for rompy execution.

    This command focuses on template management. For actual pipeline operations,
    use the 'oceanum prax' commands with project name: {project_name}

    Examples:
        oceanum rompy pipelines --show-templates
        oceanum rompy pipelines --create-template my-template.yaml --model-type swan
        
    For pipeline deployment and management, use the 'oceanum prax' commands:
        oceanum prax --project {project_name} list pipelines
        oceanum prax --project {project_name} create pipeline --help
        oceanum prax --project {project_name} submit pipeline <pipeline-name>
    """

    if show_templates:
        _show_available_templates()
        return

    if create_template:
        _create_pipeline_template(create_template, model_type)
        return

    # Default action - show help
    click.echo("💡 Use --help to see available options")
    click.echo("Quick commands:")
    click.echo("  oceanum rompy pipelines --show-templates")
    click.echo("  oceanum rompy pipelines --create-template my-template.yaml --model-type swan")
    click.echo(f"\nFor pipeline deployment and management, use the 'oceanum prax' commands:")
    click.echo(f"  oceanum prax --project {project_name} list pipelines")
    click.echo(f"  oceanum prax --project {project_name} create pipeline --help")


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
    click.echo("   oceanum rompy run config.yml swan --pipeline-name my-pipeline")
    click.echo("   oceanum rompy pipelines --create-template my-template.yaml --model-type swan")


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
    click.echo("   oceanum rompy run config.yml swan --pipeline-name my-pipeline")
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
        click.echo("💡 Customize the template and deploy with oceanum prax commands:")
        click.echo("   oceanum prax create pipeline --help")

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