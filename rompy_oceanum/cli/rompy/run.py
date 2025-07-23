"""Clean run command implementation that delegates to oceanum prax."""

import json
import os
import subprocess
import time
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

import click
from oceanum.cli.models import ContextObject

from .utils import (
    load_rompy_config,
    convert_to_pipeline_params,
    format_pipeline_filters,
    parse_prax_response
)
from .list import list_pipelines_standalone


def execute_prax_command(cmd: list[str], check: bool = True, env=None) -> subprocess.CompletedProcess:
    """Execute oceanum prax command and return result.

    Args:
        cmd: Command list to execute
        check: Whether to check return code
        env: Optional environment variables dictionary

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
            check=check,
            env=env or os.environ.copy()
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
@click.option(
    "--token",
    help="Datamesh token (overrides DATAMESH_TOKEN environment variable)"
)
@click.option(
    "--run-id",
    help="Run ID for the model (optional, will be generated if not provided)"
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
    token: Optional[str] = None,
    run_id: Optional[str] = None,
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

    # Add parameters - use config_path instead of full configuration
    # This approach avoids passing huge JSON strings on command line
    # Get token from CLI parameter or environment variable
    datamesh_token = token or os.environ.get('DATAMESH_TOKEN', '')

    # Read and parse the original config file
    config_path = parameters.get('config_path', '')

    # Get run_id from config or use a default
    run_id = "rompy_run_" + time.strftime("%Y%m%d_%H%M%S")
    if 'run_id' in parameters:
        run_id = parameters['run_id']

    # Create a copy of the full rompy config and ensure essential fields are set
    full_rompy_config = rompy_config.copy()
    full_rompy_config["model_type"] = full_rompy_config.get("model_type", "modelrun")
    full_rompy_config["run_id"] = run_id
    full_rompy_config["output_dir"] = full_rompy_config.get("output_dir", "/tmp/rompy")
    full_rompy_config["run_id_subdir"] = full_rompy_config.get("run_id_subdir", False)

    # Always include the full configuration with required parameters
    simplified_params = {
        'config_path': config_path,
        'model_type': parameters.get('model_type', 'swan'),
        'datamesh-token': datamesh_token,  # Required parameter for SWAN pipeline
        # Include the full rompy configuration
        'rompy-config': full_rompy_config
    }

    # Add any metadata parameters and extract datamesh token if present
    for key, value in parameters.items():
        if key.startswith('metadata_') and isinstance(value, (str, int, float, bool)):
            simplified_params[key] = value
        # Override with token from config only if environment variable is not set
        if 'token' in key.lower() and value and not simplified_params['datamesh-token']:
            simplified_params['datamesh-token'] = value

    # Add parameters
    for key, value in simplified_params.items():
        if value is None:
            continue
        if key == 'rompy-config':
            # Use the full rompy config instead of a minimal one
            # Add/override some essential fields
            full_config = rompy_config.copy()
            full_config["model_type"] = full_config.get("model_type", "modelrun")
            full_config["run_id"] = run_id
            full_config["output_dir"] = full_config.get("output_dir", "/tmp/rompy")
            full_config["run_id_subdir"] = full_config.get("run_id_subdir", False)

            # Use a stable JSON format with no special chars
            config_json = json.dumps(full_config)
            # DO NOT use @ prefix or file references - pass the JSON content directly
            cmd.extend(['-p', f'{key}={config_json}'])
            click.echo(f"Using direct JSON string for rompy-config: {config_json[:30]}...", err=True)
        elif isinstance(value, str):
            cmd.extend(['-p', f'{key}={value}'])
        else:
            cmd.extend(['-p', f'{key}={json.dumps(value)}'])

    # Submit pipeline
    click.echo(f"Submitting pipeline '{pipeline_name}'...")

    # Create environment variables that avoid the @ prefix issue
    env = os.environ.copy()

    # CRITICAL: Set ROMPY_CONFIG to a direct JSON string with the full config that the container will use
    # rather than the file reference with @ that's causing problems
    full_config = rompy_config.copy()
    full_config["model_type"] = full_config.get("model_type", "modelrun")
    full_config["run_id"] = run_id
    full_config["output_dir"] = full_config.get("output_dir", "/tmp/rompy")
    full_config["run_id_subdir"] = full_config.get("run_id_subdir", False)

    env['ROMPY_CONFIG'] = json.dumps(full_config)

    # Print command for debugging
    cmd_str = ' '.join(cmd)
    click.echo(f"Executing: {cmd_str}", err=True)
    click.echo(f"ROMPY_CONFIG set to direct JSON in environment", err=True)

    # Execute with our modified environment to avoid @ prefix issue
    try:
        # CRITICAL FIX: Check for any @file references and replace them with file contents
        for i, arg in enumerate(cmd):
            if '=' in arg and '@' in arg:
                param_name, file_ref = arg.split('=', 1)
                if file_ref.startswith('@') and os.path.exists(file_ref[1:]):
                    try:
                        with open(file_ref[1:], 'r') as f:
                            file_content = f.read().strip()
                        # If this is rompy-config, replace with the full config
                        if param_name.endswith('rompy-config'):
                            full_config = rompy_config.copy()
                            full_config["model_type"] = full_config.get("model_type", "modelrun")
                            full_config["run_id"] = run_id
                            full_config["output_dir"] = full_config.get("output_dir", "/tmp/rompy")
                            full_config["run_id_subdir"] = full_config.get("run_id_subdir", False)
                            file_content = json.dumps(full_config)
                        # Replace the @file reference with actual content
                        cmd[i] = f"{param_name}={file_content}"
                        click.echo(f"Replaced file reference {file_ref} with content", err=True)
                    except Exception as e:
                        click.echo(f"Warning: Could not read file {file_ref[1:]}: {e}", err=True)
                        # Failsafe: If it's rompy-config and we can't read the file, provide the full config
                        if param_name.endswith('rompy-config'):
                            full_config = rompy_config.copy()
                            full_config["model_type"] = full_config.get("model_type", "modelrun")
                            full_config["run_id"] = run_id
                            full_config["output_dir"] = full_config.get("output_dir", "/tmp/rompy")
                            full_config["run_id_subdir"] = full_config.get("run_id_subdir", False)
                            full_json = json.dumps(full_config)
                            cmd[i] = f"{param_name}={full_json}"
                            click.echo(f"Applied failsafe direct config for rompy-config", err=True)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr or str(e)
        raise click.ClickException(f"Command failed: {error_msg}")

    # Show full output for debugging
    click.echo(f"Command output: {result.stdout}")

    # Parse response from text output
    response_text = result.stdout.strip()
    click.echo(f"Full response: {response_text}")

    # Extract run ID from text output (looking for patterns like "Run ID: xyz")
    run_id = None
    for line in response_text.split('\n'):
        if "Run ID:" in line:
            run_id = line.split("Run ID:")[1].strip()
            click.echo(f"Found Run ID in 'Run ID:' format: {run_id}")
            break
        if "successfully" in line and ":" in line:
            # Try to extract ID from success message
            run_id = line.split(":")[-1].strip()
            click.echo(f"Found Run ID in success message: {run_id}")
            break
        # Look for patterns like "pipeline-swan-from-rompy-d891-dev-2bnfk"
        if "pipeline-" in line:
            parts = line.split()
            for part in parts:
                if part.startswith("pipeline-"):
                    run_id = part
                    click.echo(f"Found Run ID in pipeline pattern: {run_id}")
                    break
            if run_id:
                break

    if not run_id:
        # If we couldn't extract a run ID but the command succeeded,
        # just inform the user the submission was successful
        click.echo(f"✅ Pipeline submitted successfully")
        click.echo("Note: Could not automatically extract run ID from response")
        # Don't continue with wait/download if we don't have a run ID
        if wait or download:
            click.echo("⚠️ Cannot wait or download without a run ID")
            wait = False
            download = False
    else:
        click.echo(f"✅ Pipeline submitted successfully")
        click.echo(f"Run ID: {run_id}")

    # Wait for completion if requested
    if wait and run_id:
        click.echo(f"\n⏳ Waiting for completion (timeout: {timeout}s)...")

        # Warn about missing required parameters
        if not simplified_params.get('datamesh-token'):
            click.echo("⚠️ Warning: No DATAMESH_TOKEN provided. Set this environment variable if the model requires datamesh access.")
        else:
            click.echo(f"Using DATAMESH_TOKEN: {simplified_params['datamesh-token'][:3]}..." if simplified_params['datamesh-token'] else "No token provided")

        if 'rompy-config' not in simplified_params:
            click.echo("⚠️ Warning: Could not parse rompy-config from the provided file. The pipeline may fail.")

        start_time = time.time()
        last_status = None

        while time.time() - start_time < timeout:
            # Build status command
            status_cmd = ['oceanum', 'prax', 'get', 'pipeline-run', run_id]
            for key, value in filters.items():
                status_cmd.extend([f'--{key}', value])

            # Debug the status command
            click.echo(f"Checking status with: {' '.join(status_cmd)}", err=True)

            # Check status
            status_result = execute_prax_command(status_cmd, check=False)

            if status_result.returncode == 0:
                # Debug - show raw output
                click.echo(f"Status response: {status_result.stdout}", err=True)

                try:
                    # Try to parse as text first
                    status = "unknown"
                    status_text = status_result.stdout.strip()
                    for line in status_text.split('\n'):
                        if line.startswith("Status:") or "Status:" in line:
                            status = line.split("Status:")[1].strip().lower()
                            break

                    if status != last_status:
                        click.echo(f"Status: {status}")
                        last_status = status

                    if status in ['completed', 'succeeded', 'success']:
                        click.echo("\n✅ Pipeline completed successfully!")
                        break
                    elif status in ['failed', 'error', 'cancelled']:
                        raise click.ClickException(f"Pipeline failed with status: {status}")
                except Exception as e:
                    click.echo(f"Error parsing status: {str(e)}", err=True)

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
