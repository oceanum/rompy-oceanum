"""Clean run command implementation that delegates to oceanum prax."""

import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any

import click
from oceanum.cli.common.models import ContextObject

from .utils import (
    load_rompy_config,
    convert_to_pipeline_params,
    format_pipeline_filters,
    parse_prax_response
)
from .list import list_pipelines_standalone


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


@click.command()
@click.argument("config", type=click.Path(exists=True), required=False)
@click.option(
    "--pipeline-name",
    required=False,
    help="Name of the Prax pipeline to execute"
)
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
    "--wait/--no-wait",
    default=False,
    help="Wait for pipeline completion"
)
@click.option(
    "--timeout",
    default=3600,
    type=int,
    help="Timeout in seconds when waiting"
)
@click.option(
    "--download/--no-download",
    default=False,
    help="Download outputs after completion"
)
@click.option(
    "--output-dir",
    type=click.Path(),
    help="Output directory for downloads"
)
@click.option(
    "--list-pipelines",
    is_flag=True,
    help="List available pipelines and exit"
)
@click.pass_obj
def run(
    obj: ContextObject,
    config: str,
    pipeline_name: str,
    project: Optional[str],
    stage: str,
    wait: bool,
    timeout: int,
    download: bool,
    output_dir: Optional[str],
    list_pipelines: bool,
):
    """Execute rompy model configuration on Oceanum Prax.

    This command converts rompy configuration files to pipeline parameters
    and submits them to Oceanum Prax for execution.

    Example:
        oceanum rompy run my_swan_model.yml --pipeline-name swan-from-rompy
    """
    # Handle list pipelines request
    if list_pipelines:
        # Use the standalone list function
        list_pipelines_standalone(obj, project, stage)
        return

    # Validate required arguments when not listing pipelines
    if not config:
        raise click.ClickException("CONFIG argument is required when not using --list-pipelines")
    if not pipeline_name:
        raise click.ClickException("--pipeline-name is required when not using --list-pipelines")

    # Load rompy configuration
    rompy_config = load_rompy_config(config)
    click.echo(f"Loaded rompy configuration from {config}")

    # Convert to pipeline parameters
    parameters = convert_to_pipeline_params(rompy_config, config)
    click.echo(f"Detected model type: {parameters['model_type']}")

    # Build prax submit command
    cmd = ['oceanum', 'prax', 'submit', 'pipeline', pipeline_name]

    # Add context parameters
    # Extract org from domain (e.g., "oceanum.example.com" -> "oceanum")
    org = obj.domain.split('.')[0] if '.' in obj.domain else obj.domain
    filters = format_pipeline_filters(
        project,  # project comes from CLI option or env var
        org,
        stage
    )
    for key, value in filters.items():
        cmd.extend([f'--{key}', value])

    # Add output format
    cmd.extend(['--output', 'json'])

    # Add parameters
    for key, value in parameters.items():
        if isinstance(value, str):
            cmd.extend(['--parameter', f'{key}={value}'])
        else:
            cmd.extend(['--parameter', f'{key}={json.dumps(value)}'])

    # Submit pipeline
    click.echo(f"Submitting pipeline '{pipeline_name}'...")
    result = execute_prax_command(cmd)

    # Parse response
    response = parse_prax_response(result.stdout)
    run_id = response.get('id') or response.get('run_id') or response.get('name')

    if not run_id:
        raise click.ClickException("No run ID returned from submission")

    click.echo(f"✅ Pipeline submitted successfully")
    click.echo(f"Run ID: {run_id}")

    # Wait for completion if requested
    if wait:
        click.echo(f"\n⏳ Waiting for completion (timeout: {timeout}s)...")

        start_time = time.time()
        last_status = None

        while time.time() - start_time < timeout:
            # Build status command
            status_cmd = ['oceanum', 'prax', 'get', 'pipeline-run', run_id]
            for key, value in filters.items():
                status_cmd.extend([f'--{key}', value])
            status_cmd.extend(['--output', 'json'])

            # Check status
            status_result = execute_prax_command(status_cmd, check=False)

            if status_result.returncode == 0:
                try:
                    status_data = parse_prax_response(status_result.stdout)
                    status = status_data.get('status', 'unknown').lower()

                    if status != last_status:
                        click.echo(f"Status: {status}")
                        last_status = status

                    if status in ['completed', 'succeeded', 'success']:
                        click.echo("\n✅ Pipeline completed successfully!")
                        break
                    elif status in ['failed', 'error', 'cancelled']:
                        raise click.ClickException(f"Pipeline failed with status: {status}")
                except json.JSONDecodeError:
                    pass

            time.sleep(10)  # Poll interval
        else:
            raise click.ClickException(f"Pipeline did not complete within {timeout} seconds")

    # Download outputs if requested
    if download and wait:
        if not output_dir:
            output_dir = f"outputs/{run_id}"

        click.echo(f"\n📥 Downloading outputs to {output_dir}...")

        download_cmd = ['oceanum', 'prax', 'download', 'pipeline-run', run_id]
        for key, value in filters.items():
            download_cmd.extend([f'--{key}', value])
        download_cmd.extend(['--output-dir', output_dir])

        # Run download command (don't capture output to show progress)
        subprocess.run(download_cmd, check=True)
        click.echo("✅ Downloads complete")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("Run Summary:")
    click.echo(f"  Pipeline: {pipeline_name}")
    click.echo(f"  Run ID: {run_id}")
    click.echo(f"  Status: {'completed' if wait else 'submitted'}")
    if download and wait:
        click.echo(f"  Outputs: {output_dir}")
