"""List commands for rompy CLI that delegate to oceanum prax."""

import json
import subprocess
from typing import Optional, Dict, Any

import click
from oceanum.cli.common.models import ContextObject

from .utils import format_pipeline_filters, parse_prax_response


def execute_prax_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Execute oceanum prax command and return result.

    Args:
        cmd: Command list to execute
        check: Whether to check return code

    Returns:
        CompletedProcess result

    Raises:
        click.ClickException: If command fails
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        raise click.ClickException(f"Command failed: {error_msg}")


@click.group(name="list")
def list_group():
    """List rompy-related resources in Oceanum Prax.

    These commands provide convenient access to rompy-specific resources
    like pipelines, runs, and outputs.
    """
    pass


@list_group.command(name="pipelines")
@click.option(
    "--project",
    envvar="PRAX_PROJECT",
    help="Filter by project name"
)
@click.option(
    "--stage",
    default="dev",
    envvar="PRAX_STAGE",
    help="Filter by deployment stage"
)
@click.option(
    "--search",
    help="Search in pipeline names and descriptions"
)
@click.option(
    "--status",
    help="Filter by pipeline status"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format"
)
@click.pass_obj
def list_pipelines(
    obj: ContextObject,
    project: Optional[str],
    stage: str,
    search: Optional[str],
    status: Optional[str],
    output: str
):
    """List available rompy pipelines.

    This shows pipelines that can be used with 'oceanum rompy run'.
    Common pipeline names include:
    - swan-from-rompy
    - schism-from-rompy
    - ww3-from-rompy
    """
    # Build prax command
    cmd = ['oceanum', 'prax', 'list', 'pipelines']

    # Extract org from domain
    org = obj.domain.split('.')[0] if '.' in obj.domain else obj.domain
    filters = format_pipeline_filters(project, org, stage)

    for key, value in filters.items():
        cmd.extend([f'--{key}', value])

    if search:
        cmd.extend(['--search', search])
    if status:
        cmd.extend(['--status', status])

    cmd.extend(['--output', output])

    # Execute and display
    result = execute_prax_command(cmd)

    if output == 'table':
        # Add helpful context for rompy users
        click.echo("🌊 Rompy-compatible pipelines:")
        click.echo(result.stdout)
        click.echo("\n💡 To run a pipeline: oceanum rompy run <config> --pipeline-name <name>")
    else:
        click.echo(result.stdout)


@list_group.command(name="runs")
@click.option(
    "--project",
    envvar="PRAX_PROJECT",
    help="Filter by project name"
)
@click.option(
    "--stage",
    default="dev",
    envvar="PRAX_STAGE",
    help="Filter by deployment stage"
)
@click.option(
    "--pipeline",
    help="Filter by pipeline name"
)
@click.option(
    "--status",
    type=click.Choice(["running", "succeeded", "failed", "pending", "cancelled"]),
    help="Filter by run status"
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Maximum number of runs to show"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format"
)
@click.pass_obj
def list_runs(
    obj: ContextObject,
    project: Optional[str],
    stage: str,
    pipeline: Optional[str],
    status: Optional[str],
    limit: int,
    output: str
):
    """List recent rompy pipeline runs.

    Shows the status and details of recent pipeline executions.
    Use the run ID from this list with other commands like:
    - oceanum rompy status <run-id>
    - oceanum rompy logs <run-id>
    - oceanum rompy download <run-id>
    """
    # For runs, we need to use the pipeline runs endpoint
    # Since oceanum prax doesn't have a direct "list runs" command,
    # we'll need to get creative or show an informative message

    click.echo("🔄 Fetching recent pipeline runs...")

    # Build a command to get pipeline information
    cmd = ['oceanum', 'prax', 'list', 'pipelines']

    org = obj.domain.split('.')[0] if '.' in obj.domain else obj.domain
    filters = format_pipeline_filters(project, org, stage)

    for key, value in filters.items():
        cmd.extend([f'--{key}', value])

    if pipeline:
        cmd.extend(['--search', pipeline])

    cmd.extend(['--output', 'json'])

    try:
        result = execute_prax_command(cmd)
        pipelines = parse_prax_response(result.stdout)

        if not pipelines:
            click.echo("No pipelines found.")
            return

        # For each pipeline, we could potentially fetch recent runs
        # but since there's no direct API, we'll provide guidance
        click.echo(f"Found {len(pipelines)} pipeline(s).")
        click.echo("\n💡 To check the status of a specific run:")
        click.echo("   oceanum rompy status <run-id>")
        click.echo("\n📝 To get run IDs, check the output after running:")
        click.echo("   oceanum rompy run <config> --pipeline-name <name>")

        if output == 'json':
            # Output pipeline info as JSON for scripting
            click.echo(json.dumps(pipelines, indent=2))

    except Exception as e:
        click.echo(f"❌ Error fetching pipeline information: {e}", err=True)


@list_group.command(name="outputs")
@click.argument("run_id")
@click.option(
    "--project",
    envvar="PRAX_PROJECT",
    help="Project name (if not in run ID)"
)
@click.option(
    "--stage",
    default="dev",
    envvar="PRAX_STAGE",
    help="Deployment stage"
)
@click.option(
    "--task",
    help="Filter outputs by task name"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format"
)
@click.pass_obj
def list_outputs(
    obj: ContextObject,
    run_id: str,
    project: Optional[str],
    stage: str,
    task: Optional[str],
    output: str
):
    """List outputs available for a pipeline run.

    Shows what files are available to download from a completed run.
    Use this to see what outputs were generated before downloading.

    Example:
        oceanum rompy list outputs my-run-id-123
        oceanum rompy download my-run-id-123 --output-dir ./results
    """
    click.echo(f"📂 Checking outputs for run: {run_id}")

    # Since oceanum prax doesn't have a direct list outputs command,
    # we'll use the get pipeline-run command to fetch run details
    cmd = ['oceanum', 'prax', 'get', 'pipeline-run', run_id]

    org = obj.domain.split('.')[0] if '.' in obj.domain else obj.domain
    filters = format_pipeline_filters(project, org, stage)

    for key, value in filters.items():
        cmd.extend([f'--{key}', value])

    cmd.extend(['--output', 'json'])

    try:
        result = execute_prax_command(cmd, check=False)

        if result.returncode != 0:
            click.echo(f"❌ Could not fetch run details: {result.stderr}", err=True)
            return

        run_data = parse_prax_response(result.stdout)
        status = run_data.get('status', 'unknown').lower()

        if status not in ['completed', 'succeeded', 'success']:
            click.echo(f"⚠️  Run is not complete (status: {status})")
            click.echo("   Outputs are only available for completed runs.")
            return

        # Extract output information if available
        outputs = run_data.get('outputs', {})
        tasks = run_data.get('tasks', {})

        if output == 'json':
            click.echo(json.dumps(run_data, indent=2))
        else:
            click.echo(f"\n✅ Run completed successfully")
            click.echo(f"Status: {status}")

            if outputs:
                click.echo("\n📦 Available outputs:")
                for name, details in outputs.items():
                    if task and task not in name:
                        continue
                    click.echo(f"  - {name}")
                    if isinstance(details, dict):
                        for key, value in details.items():
                            click.echo(f"    {key}: {value}")

            if tasks:
                click.echo("\n📋 Tasks in pipeline:")
                for task_name, task_info in tasks.items():
                    if task and task != task_name:
                        continue
                    task_status = task_info.get('status', 'unknown') if isinstance(task_info, dict) else 'unknown'
                    click.echo(f"  - {task_name}: {task_status}")

            click.echo("\n💡 To download outputs:")
            click.echo(f"   oceanum rompy download {run_id} --output-dir ./results")

    except Exception as e:
        click.echo(f"❌ Error fetching run details: {e}", err=True)


@list_group.command(name="models")
@click.option(
    "--type",
    "model_type",
    type=click.Choice(["swan", "schism", "ww3", "all"]),
    default="all",
    help="Filter by model type"
)
@click.pass_obj
def list_models(obj: ContextObject, model_type: str):
    """List supported rompy model types and their pipelines.

    Shows which ocean/wave models are supported and which pipelines
    can run them.
    """
    models = {
        "swan": {
            "name": "SWAN (Simulating WAves Nearshore)",
            "pipelines": ["swan-from-rompy", "swan-operational", "swan-forecast"],
            "description": "Third-generation wave model for coastal regions",
            "config_example": "swan_config.yml"
        },
        "schism": {
            "name": "SCHISM (Semi-implicit Cross-scale Hydroscience Integrated System Model)",
            "pipelines": ["schism-from-rompy", "schism-3d", "schism-forecast"],
            "description": "3D baroclinic circulation model",
            "config_example": "schism_config.yml"
        },
        "ww3": {
            "name": "WAVEWATCH III",
            "pipelines": ["ww3-from-rompy", "ww3-global", "ww3-regional"],
            "description": "Third-generation wave model for deep water",
            "config_example": "ww3_config.yml"
        }
    }

    click.echo("🌊 Supported Rompy Models\n")

    for key, info in models.items():
        if model_type != "all" and model_type != key:
            continue

        click.echo(f"📦 {info['name']}")
        click.echo(f"   Model key: {key}")
        click.echo(f"   {info['description']}")
        click.echo(f"   Example config: {info['config_example']}")
        click.echo("   Compatible pipelines:")
        for pipeline in info['pipelines']:
            click.echo(f"     - {pipeline}")
        click.echo()

    click.echo("💡 To create a new model configuration:")
    click.echo("   oceanum rompy init --type <model>")
    click.echo("\n💡 To run a model:")
    click.echo("   oceanum rompy run <config.yml> --pipeline-name <pipeline>")


# Make list_pipelines available as standalone for backward compatibility
def list_pipelines_standalone(
    obj: ContextObject,
    project: Optional[str] = None,
    stage: str = "dev"
):
    """Standalone function for listing pipelines (used by run --list-pipelines)."""
    # Delegate to the list pipelines command with minimal options
    ctx = click.Context(list_pipelines)
    ctx.obj = obj
    ctx.invoke(list_pipelines, project=project, stage=stage,
               search=None, status=None, output="table")


# Export the group and standalone function
__all__ = ["list_group", "list_pipelines_standalone"]
