"""Clean download command implementation that delegates to oceanum prax."""

import subprocess
from pathlib import Path
from typing import Optional

import click
from oceanum.cli.models import ContextObject

from .utils import format_pipeline_filters


@click.command()
@click.argument("run_id")
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    help="Output directory for downloads (default: outputs/<run_id>)"
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
    "--include",
    multiple=True,
    help="Include only files matching pattern (can be used multiple times)"
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude files matching pattern (can be used multiple times)"
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing files"
)
@click.pass_obj
def download(
    obj: ContextObject,
    run_id: str,
    output_dir: Optional[str],
    project: Optional[str],
    stage: str,
    include: tuple,
    exclude: tuple,
    overwrite: bool,
):
    """Download outputs from a rompy pipeline run.

    This command wraps 'oceanum prax download pipeline-run' to retrieve
    output files from a completed rompy model execution.

    Example:
        oceanum rompy download abc123def -o my_outputs/
        oceanum rompy download abc123def --include "*.nc" --include "*.log"
    """
    # Set default output directory if not specified
    if not output_dir:
        output_dir = f"outputs/{run_id}"

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    click.echo(f"Downloading outputs for run {run_id}...")
    click.echo(f"Output directory: {output_path.absolute()}")

    # Build prax command
    cmd = ['oceanum', 'prax', 'download', 'pipeline-run', run_id]

    # Add context parameters
    filters = format_pipeline_filters(
        project or obj.project,
        obj.org,
        stage
    )
    for key, value in filters.items():
        cmd.extend([f'--{key}', value])

    # Add output directory
    cmd.extend(['--output-dir', str(output_dir)])

    # Add include patterns
    for pattern in include:
        cmd.extend(['--include', pattern])

    # Add exclude patterns
    for pattern in exclude:
        cmd.extend(['--exclude', pattern])

    # Add overwrite flag
    if overwrite:
        cmd.append('--overwrite')

    # Execute download command
    # Don't capture output to show download progress
    try:
        result = subprocess.run(cmd, check=True)

        # List downloaded files
        click.echo("\n✅ Download complete!")
        click.echo("\nDownloaded files:")

        # Find all files in output directory
        downloaded_files = []
        for file_path in output_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(output_path)
                downloaded_files.append(relative_path)
                click.echo(f"  - {relative_path}")

        if not downloaded_files:
            click.echo("  No files downloaded (run may still be in progress)")
        else:
            click.echo(f"\nTotal files: {len(downloaded_files)}")

    except subprocess.CalledProcessError as e:
        error_msg = getattr(e, 'stderr', str(e))
        raise click.ClickException(f"Failed to download outputs: {error_msg}")
    except Exception as e:
        raise click.ClickException(f"Unexpected error during download: {e}")
