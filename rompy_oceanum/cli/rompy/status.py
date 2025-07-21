"""Clean status command implementation that delegates to oceanum prax."""

import subprocess
from typing import Optional

import click
from oceanum.cli.common.models import ContextObject

from .utils import format_pipeline_filters, parse_prax_response, format_status_output


@click.command()
@click.argument("run_id")
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
    "--format",
    "output_format",
    type=click.Choice(["json", "table", "summary"]),
    default="summary",
    help="Output format"
)
@click.option(
    "--watch",
    is_flag=True,
    help="Continuously watch status until completion"
)
@click.option(
    "--interval",
    default=10,
    type=int,
    help="Watch interval in seconds"
)
@click.pass_obj
def status(
    obj: ContextObject,
    run_id: str,
    project: Optional[str],
    stage: str,
    output_format: str,
    watch: bool,
    interval: int,
):
    """Check status of a rompy pipeline run.

    This command wraps 'oceanum prax get pipeline-run' to check the
    status of a submitted rompy model run.

    Example:
        oceanum rompy status abc123def
    """
    import time

    # Build prax command
    cmd = ['oceanum', 'prax', 'get', 'pipeline-run', run_id]

    # Add context parameters
    filters = format_pipeline_filters(
        project or obj.project,
        obj.org,
        stage
    )
    for key, value in filters.items():
        cmd.extend([f'--{key}', value])

    # Handle watch mode
    if watch:
        click.echo(f"Watching pipeline run {run_id} (press Ctrl+C to stop)...")
        last_status = None

        try:
            while True:
                # Get status in JSON format for parsing
                json_cmd = cmd + ['--output', 'json']
                result = subprocess.run(
                    json_cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )

                if result.returncode == 0:
                    try:
                        status_data = parse_prax_response(result.stdout)
                        current_status = status_data.get('status', 'unknown').lower()

                        # Clear screen and show formatted status
                        click.clear()
                        click.echo(format_status_output(status_data))
                        click.echo(f"\nLast checked: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                        click.echo(f"Watching every {interval}s... (Ctrl+C to stop)")

                        # Check if complete
                        if current_status in ['completed', 'succeeded', 'success', 'failed', 'error', 'cancelled']:
                            click.echo(f"\n✅ Pipeline run finished with status: {current_status}")
                            break

                        last_status = current_status
                    except Exception as e:
                        click.echo(f"Error parsing status: {e}", err=True)
                else:
                    click.echo(f"Error getting status: {result.stderr}", err=True)

                time.sleep(interval)

        except KeyboardInterrupt:
            click.echo("\n⏸️  Stopped watching")
            return

    # Non-watch mode
    else:
        # Set output format
        if output_format == 'json':
            cmd.extend(['--output', 'json'])
        elif output_format == 'table':
            cmd.extend(['--output', 'table'])
        else:
            # For summary format, get JSON and format it ourselves
            cmd.extend(['--output', 'json'])

        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            raise click.ClickException(f"Failed to get status: {result.stderr}")

        # Handle output based on format
        if output_format == 'summary':
            status_data = parse_prax_response(result.stdout)
            click.echo(format_status_output(status_data))
        else:
            # For JSON and table, output as-is
            click.echo(result.stdout)
