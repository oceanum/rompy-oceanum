"""Pipeline template management command for rompy-oceanum CLI."""

import logging
from pathlib import Path
from typing import Any, Dict

import click
import yaml
from oceanum.cli.models import ContextObject

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--model-type",
    type=click.Choice(["swan", "schism", "ww3"]),
    help="Model type for template selection",
)
@click.option(
    "--show-templates", is_flag=True, help="Show available pipeline templates"
)
@click.option("--create-template", help="Create a new pipeline template file")
@click.option(
    "--project-name",
    default="rompy-pipelines",
    help="Prax project name for rompy pipelines (default: rompy-pipelines)",
)
@click.option("--run-image", help="Custom Docker image for the run task")
@click.option("--cpu", help="CPU resources for the run task (e.g., '4')")
@click.option("--memory", help="Memory resources for the run task (e.g., '8G')")
@click.pass_obj
def pipelines(
    obj: ContextObject,
    model_type,
    show_templates,
    create_template,
    project_name,
    run_image,
    cpu,
    memory,
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
        _create_pipeline_template(create_template, model_type, run_image, cpu, memory)
        return

    # Default action - show help
    click.echo("💡 Use --help to see available options")
    click.echo("Quick commands:")
    click.echo("  oceanum rompy pipelines --show-templates")
    click.echo(
        "  oceanum rompy pipelines --create-template my-template.yaml --model-type swan"
    )
    click.echo(
        f"\nFor pipeline deployment and management, use the 'oceanum prax' commands:"
    )
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
                    with open(template, "r") as f:
                        template_data = yaml.safe_load(f)

                    name = template.stem
                    desc = template_data.get("metadata", {}).get(
                        "description", "No description"
                    )
                    model_type = (
                        template_data.get("metadata", {})
                        .get("labels", {})
                        .get("model-type", "generic")
                    )

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
    click.echo(
        "   oceanum rompy pipelines --create-template my-template.yaml --model-type swan"
    )


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
                    with open(template, "r") as f:
                        template_data = yaml.safe_load(f)

                    name = template.stem
                    desc = template_data.get("metadata", {}).get(
                        "description", "No description"
                    )
                    model_type = (
                        template_data.get("metadata", {})
                        .get("labels", {})
                        .get("model-type", "generic")
                    )

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
    click.echo(
        "   oceanum rompy pipelines --create-template my-template.yaml --model-type swan"
    )


def _create_pipeline_template(
    template_path: str,
    model_type: str = None,
    run_image: str = None,
    cpu: str = None,
    memory: str = None,
):
    """Create a new pipeline template file."""
    click.echo(f"📝 Creating pipeline template: {template_path}")

    if not model_type:
        model_type = click.prompt(
            "Model type", type=click.Choice(["swan", "schism", "ww3", "generic"])
        )

    template_data = _get_template_structure(model_type, run_image, cpu, memory)

    try:
        output_file = Path(template_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            yaml.dump(template_data, f, default_flow_style=False, indent=2)

        click.echo(f"✅ Template created: {output_file}")
        click.echo("💡 Customize the template and deploy with oceanum prax commands:")
        click.echo(f"   oceanum prax deloy {template_path}")
        click.echo("   oceanum prax deloy {template_path}")

    except Exception as e:
        click.echo(f"❌ Failed to create template: {e}", err=True)


def _get_template_structure(
    model_type: str, run_image: str = None, cpu: str = None, memory: str = None
) -> Dict[str, Any]:
    """Get template structure for a model type."""

    # Model-specific configurations
    model_configs = {
        "swan": {
            "generate_image": "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/rompy:latest",
            "run_image": run_image
            or "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/swan:latest",
            "run_command": "mpirun -n 2 /usr/local/bin/swan.exe",
            "cpu": cpu or "4",
            "memory": memory or "2G",
            "env_vars": {
                "ROMPY_MODEL": "swan",
                "OMPI_ALLOW_RUN_AS_ROOT": "1",
                "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                "OMP_NUM_THREADS": "2",
            },
        },
        "schism": {
            "generate_image": "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/rompy:latest",
            "run_image": run_image
            or "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/schism:latest",
            "run_command": "mpirun -n 4 /usr/local/bin/pschism",
            "cpu": cpu or "8",
            "memory": memory or "16G",
            "env_vars": {
                "ROMPY_MODEL": "schism",
                "OMPI_ALLOW_RUN_AS_ROOT": "1",
                "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                "OMP_NUM_THREADS": "4",
            },
        },
        "ww3": {
            "generate_image": "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/rompy:latest",
            "run_image": run_image
            or "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/ww3:latest",
            "run_command": "mpirun -n 2 /usr/local/bin/ww3_shel",
            "cpu": cpu or "4",
            "memory": memory or "8G",
            "env_vars": {
                "ROMPY_MODEL": "ww3",
                "OMPI_ALLOW_RUN_AS_ROOT": "1",
                "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                "OMP_NUM_THREADS": "2",
            },
        },
    }

    # Get model config or use generic defaults
    model_config = model_configs.get(
        model_type,
        {
            "generate_image": "us-central1-docker.pkg.dev/oceanum-procd/oceanum-public/rompy:latest",
            "run_image": run_image
            or "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/rompy:latest",
            "run_command": "python -m rompy run",
            "cpu": cpu or "2",
            "memory": memory or "4G",
            "env_vars": {"ROMPY_MODEL": model_type},
        },
    )

    base_template = {
        "name": f"rompy-{model_type}",
        "resources": {
            "tasks": [
                {
                    "name": "generate",
                    "image": model_config["generate_image"],
                    "command": "rompy generate --config-from-env -v",
                    "outputs": {"artifacts": [{"name": "workspace", "path": "/app"}]},
                    "resources": {"cpu": "1", "memory": "1G"},
                    "env": [
                        {"name": "ROMPY_MODEL", "value": model_type},
                        {"name": "ROMPY_LOG_LEVEL", "value": "INFO"},
                    ],
                },
                {
                    "name": "run",
                    "image": model_config["run_image"],
                    "inputs": {"artifacts": [{"name": "workspace", "path": "/app"}]},
                    "command": f"rompy run --config-from-env --run-backend local -v",
                    "resources": {
                        "cpu": model_config["cpu"],
                        "memory": model_config["memory"],
                    },
                    "outputs": {"artifacts": [{"name": "output", "path": "/app"}]},
                    "env": [
                        {"name": "ROMPY_MODEL", "value": model_type},
                        {"name": "ROMPY_BACKEND_TYPE", "value": "local"},
                        {
                            "name": "ROMPY_BACKEND_COMMAND",
                            "value": model_config["run_command"],
                        },
                        {"name": "ROMPY_BACKEND_SHELL", "value": "true"},
                        {"name": "ROMPY_BACKEND_CAPTURE_OUTPUT", "value": "true"},
                    ]
                    + [
                        {"name": k, "value": v}
                        for k, v in model_config["env_vars"].items()
                    ],
                },
                {
                    "name": "register",
                    "image": model_config["generate_image"],
                    "command": "rompy postprocess --config-from-env --processor datamesh -v",
                    "inputs": {"artifacts": [{"name": "output", "path": "/app"}]},
                    "resources": {"cpu": "1", "memory": "1G"},
                    "env": [
                        {"name": "ROMPY_MODEL", "value": model_type},
                        {"name": "DATAMESH_PROCESSOR", "value": "datamesh"},
                        {
                            "name": "DATAMESH_OUTPUT_PATTERNS",
                            "value": "*.nc,*.dat,*.csv,*.log",
                        },
                        {
                            "name": "DATAMESH_TAGS",
                            "value": f"{model_type},wave-model,oceanum,rompy",
                        },
                    ],
                },
            ],
            "pipelines": [
                {
                    "name": f"{model_type}-from-rompy",
                    "arguments": {
                        "parameters": [
                            {"name": "datamesh-token", "env": "DATAMESH_TOKEN"},
                            {"name": "rompy-config", "env": "ROMPY_CONFIG"},
                        ]
                    },
                    "defaults": {
                        "env": [{"name": "ROMPY_MODEL", "value": model_type}]
                        + [
                            {"name": k, "value": v}
                            for k, v in model_config["env_vars"].items()
                        ],
                        "retryStrategy": {"limit": 1},
                    },
                    "dag": [
                        {"name": "generate", "taskRef": "generate", "dependencies": []},
                        {
                            "name": "run",
                            "taskRef": "run",
                            "arguments": {
                                "artifacts": [
                                    {
                                        "name": "workspace",
                                        "stepRef": {
                                            "name": "generate",
                                            "artifactRef": "workspace",
                                        },
                                    }
                                ]
                            },
                            "dependencies": [{"name": "generate"}],
                        },
                        {
                            "name": "register",
                            "taskRef": "register",
                            "arguments": {
                                "artifacts": [
                                    {
                                        "name": "output",
                                        "stepRef": {
                                            "name": "run",
                                            "artifactRef": "output",
                                        },
                                    }
                                ]
                            },
                            "dependencies": [{"name": "run"}],
                        },
                    ],
                }
            ],
            "stages": [
                {
                    "name": "dev",
                    "resources": {"pipelines": [f"{model_type}-from-rompy"]},
                }
            ],
        },
    }

    return base_template
