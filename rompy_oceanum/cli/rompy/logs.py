"""Clean logs command implementation that delegates to oceanum prax."""

import subprocess
from typing import Optional

import click
from oceanum.cli.common.models import ContextObject

from .utils import format_pipeline_filters


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
    "--task",
    help="Specific task name to get logs for"
)
@click.option(
    "--follow",
    "-f",
    is_flag=True,
    help="Follow log output (like tail -f)"
)
@click.option(
    "--tail",
    type=int,
    default=100,
    help="Number of lines to show from the end"
)
@click.option(
    "--since",
    help="Show logs since timestamp (e.g., '10m', '1h', '2023-01-01')"
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output"
)
@click.pass_obj
def logs(
    obj: ContextObject,
    run_id: str,
    project: Optional[str],
    stage: str,
    task: Optional[str],
    follow: bool,
    tail: int,
    since: Optional[str],
    no_color: bool,
):
    """Get logs for a rompy pipeline run.

    This command wraps 'oceanum prax logs pipeline-run' to retrieve
    logs from a rompy model execution.

    Example:
        oceanum rompy logs abc123def --tail 50
        oceanum rompy logs abc123def --follow
    """
    # Build prax command
    cmd = ['oceanum', 'prax', 'logs', 'pipeline-run', run_id]

    # Add context parameters
    filters = format_pipeline_filters(
        project or obj.project,
        obj.org,
        stage
    )
    for key, value in filters.items():
        cmd.extend([f'--{key}', value])

    # Add optional parameters
    if task:
        cmd.extend(['--task', task])
    if follow:
        cmd.append('--follow')
    if tail:
        cmd.extend(['--tail', str(tail)])
    if since:
        cmd.extend(['--since', since])
    if no_color:
        cmd.append('--no-color')

    # Execute command
    if follow:
        # For follow mode, we need to stream output
        click.echo(f"Following logs for pipeline run {run_id} (press Ctrl+C to stop)...")
        try:
            # Use Popen for streaming output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            # Stream output line by line
            try:
                for line in process.stdout:
                    click.echo(line, nl=False)
            except KeyboardInterrupt:
                click.echo("\n⏸️  Stopped following logs")
                process.terminate()
                return

            # Wait for process to complete
            process.wait()

            if process.returncode != 0:
                error = process.stderr.read()
                raise click.ClickException(f"Failed to get logs: {error}")

        except subprocess.SubprocessError as e:
            raise click.ClickException(f"Failed to execute command: {e}")

    else:
        # Non-follow mode - just execute and print
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            click.echo(result.stdout)

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or str(e)
            raise click.ClickException(f"Failed to get logs: {error_msg}")
