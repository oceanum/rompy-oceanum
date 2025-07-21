"""Sync command for downloading and managing rompy pipeline outputs."""

import logging
import shutil
from pathlib import Path
from typing import List, Optional

import click
from oceanum.cli.common.models import ContextObject

from ...config import PraxConfig
from ...client import PraxClient


logger = logging.getLogger(__name__)


@click.command()
@click.argument("run_id", required=True)
@click.argument("output_dir", required=True)
@click.option(
    "--project",
    envvar="PRAX_PROJECT",
    help="Prax project (overrides oceanum context)"
)
@click.option(
    "--pattern",
    default="*",
    help="File pattern to download (glob pattern)"
)
@click.option(
    "--stage",
    help="Download outputs from specific pipeline stage only"
)
@click.option(
    "--format",
    "file_format",
    multiple=True,
    help="Filter by file format (e.g., .nc, .dat, .csv). Can be specified multiple times"
)
@click.option(
    "--organize/--no-organize",
    default=True,
    help="Organize files by stage and type"
)
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    help="Overwrite existing files"
)
@click.option(
    "--verify/--no-verify",
    default=True,
    help="Verify file integrity after download"
)
@click.option(
    "--compress/--no-compress",
    default=False,
    help="Create compressed archive of downloaded files"
)
@click.option(
    "--metadata/--no-metadata",
    default=True,
    help="Download metadata and manifest files"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be downloaded without actually downloading"
)
@click.pass_obj
def sync(
    obj: ContextObject,
    run_id,
    output_dir,
    project,
    pattern,
    stage,
    file_format,
    organize,
    overwrite,
    verify,
    compress,
    metadata,
    dry_run
):
    """Sync outputs from a rompy pipeline run to local directory.

    Args:
        run_id: Prax pipeline run identifier
        output_dir: Local directory to download files to

    Usage:
        oceanum rompy sync abc123-def456-789 ./outputs
        oceanum rompy sync abc123 ./data --pattern "*.nc" --stage postprocess
        oceanum rompy sync abc123 ./results --format .nc --format .dat --organize
        oceanum rompy sync abc123 ./test --dry-run
    """
    # Create Prax configuration using oceanum context
    prax_config_data = {
        "org": obj.domain.split('.')[0] if '.' in obj.domain else obj.domain,
    }

    # Override project if specified
    if project:
        prax_config_data["project"] = project

    # Use oceanum's token for authentication
    if obj.token and obj.token.access_token:
        prax_config_data["token"] = obj.token.access_token

    try:
        prax_config = PraxConfig.from_env(**prax_config_data)
    except ValueError as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        return

    client = PraxClient(prax_config)
    output_path = Path(output_dir)

    # Create output directory if it doesn't exist
    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)

    def _filter_files(file_list: List[dict]) -> List[dict]:
        """Apply filters to file list."""
        filtered = file_list

        # Filter by stage
        if stage:
            filtered = [
                f for f in filtered
                if f.get('stage', '').lower() == stage.lower()
            ]

        # Filter by file format
        if file_format:
            formats = [fmt.lower() if fmt.startswith('.') else f'.{fmt.lower()}'
                      for fmt in file_format]
            filtered = [
                f for f in filtered
                if any(f.get('name', '').lower().endswith(fmt) for fmt in formats)
            ]

        # Filter by pattern (basic glob-like matching)
        if pattern and pattern != "*":
            import fnmatch
            filtered = [
                f for f in filtered
                if fnmatch.fnmatch(f.get('name', ''), pattern)
            ]

        return filtered

    def _organize_file_path(file_info: dict, base_path: Path) -> Path:
        """Determine organized file path based on stage and type."""
        if not organize:
            return base_path / file_info.get('name', 'unknown')

        # Create subdirectories by stage and file type
        stage_name = file_info.get('stage', 'unknown')
        file_name = file_info.get('name', 'unknown')
        file_ext = Path(file_name).suffix.lower() or 'other'

        # Map file extensions to categories
        file_categories = {
            '.nc': 'netcdf',
            '.dat': 'data',
            '.csv': 'tables',
            '.txt': 'text',
            '.log': 'logs',
            '.yaml': 'config',
            '.yml': 'config',
            '.json': 'config',
            '.png': 'plots',
            '.jpg': 'plots',
            '.jpeg': 'plots',
            '.pdf': 'reports'
        }

        category = file_categories.get(file_ext, 'other')
        return base_path / stage_name / category / file_name

    def _format_file_size(size_bytes: Optional[int]) -> str:
        """Format file size in human readable format."""
        if size_bytes is None:
            return "Unknown"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _verify_file(local_path: Path, expected_size: Optional[int] = None) -> bool:
        """Verify downloaded file integrity."""
        if not local_path.exists():
            return False

        if expected_size is not None:
            actual_size = local_path.stat().st_size
            if actual_size != expected_size:
                logger.warning(f"Size mismatch for {local_path}: expected {expected_size}, got {actual_size}")
                return False

        return True

    try:
        # Get available files from Prax
        click.echo(f"🔍 Discovering files for run: {run_id}")
        available_files = client.list_run_artifacts(run_id)

        if not available_files:
            click.echo("📭 No files found for this run.")
            return

        # Apply filters
        filtered_files = _filter_files(available_files)

        if not filtered_files:
            click.echo("📭 No files match the specified filters.")
            return

        # Show what will be downloaded
        total_size = sum(f.get('size', 0) for f in filtered_files if f.get('size'))
        click.echo(f"📋 Found {len(filtered_files)} files ({_format_file_size(total_size)} total)")

        if dry_run:
            click.echo("\n🔍 Dry run - files that would be downloaded:")
            click.echo("=" * 60)

        # Process each file
        downloaded_files = []
        skipped_files = []
        failed_files = []

        for i, file_info in enumerate(filtered_files, 1):
            file_name = file_info.get('name', f'file_{i}')
            file_size = file_info.get('size')
            file_stage = file_info.get('stage', 'unknown')

            # Determine local path
            local_path = _organize_file_path(file_info, output_path)

            progress_prefix = f"[{i}/{len(filtered_files)}]"

            if dry_run:
                size_str = _format_file_size(file_size) if file_size else "Unknown size"
                click.echo(f"  {progress_prefix} {file_name} ({size_str}) -> {local_path}")
                continue

            # Check if file exists and handle overwrite
            if local_path.exists() and not overwrite:
                click.echo(f"⏭️  {progress_prefix} Skipping {file_name} (already exists)")
                skipped_files.append(file_name)
                continue

            try:
                # Create parent directories
                local_path.parent.mkdir(parents=True, exist_ok=True)

                # Download file
                size_str = f" ({_format_file_size(file_size)})" if file_size else ""
                click.echo(f"📥 {progress_prefix} Downloading {file_name}{size_str}")

                success = client.download_run_artifact(
                    run_id,
                    file_info.get('path', file_name),
                    local_path
                )

                if success:
                    # Verify file if requested
                    if verify and not _verify_file(local_path, file_size):
                        click.echo(f"⚠️  Verification failed for {file_name}")
                        failed_files.append(file_name)
                    else:
                        downloaded_files.append(str(local_path))
                else:
                    click.echo(f"❌ Failed to download {file_name}")
                    failed_files.append(file_name)

            except Exception as e:
                click.echo(f"❌ Error downloading {file_name}: {e}")
                failed_files.append(file_name)

        if dry_run:
            click.echo(f"\n📊 Summary: {len(filtered_files)} files would be downloaded")
            return

        # Download metadata if requested
        if metadata:
            try:
                click.echo("📄 Downloading run metadata...")
                metadata_path = output_path / "run_metadata.json"
                if client.download_run_metadata(run_id, metadata_path):
                    downloaded_files.append(str(metadata_path))
            except Exception as e:
                click.echo(f"⚠️  Could not download metadata: {e}")

        # Create compressed archive if requested
        if compress and downloaded_files:
            try:
                click.echo("📦 Creating compressed archive...")
                archive_path = output_path / f"{run_id}_outputs.tar.gz"
                import tarfile

                with tarfile.open(archive_path, 'w:gz') as tar:
                    for file_path in downloaded_files:
                        file_obj = Path(file_path)
                        if file_obj.exists():
                            # Use relative path in archive
                            arcname = file_obj.relative_to(output_path)
                            tar.add(file_path, arcname=arcname)

                click.echo(f"📦 Archive created: {archive_path}")

            except Exception as e:
                click.echo(f"⚠️  Could not create archive: {e}")

        # Summary
        click.echo("\n📊 Sync Summary:")
        click.echo("=" * 30)
        click.echo(f"✅ Downloaded: {len(downloaded_files)} files")
        if skipped_files:
            click.echo(f"⏭️  Skipped: {len(skipped_files)} files")
        if failed_files:
            click.echo(f"❌ Failed: {len(failed_files)} files")

        click.echo(f"\n📁 Files saved to: {output_path}")

        if organize:
            click.echo("📂 Files organized by stage and type")

        # Show helpful next steps
        if downloaded_files:
            click.echo(f"\n💡 View downloaded files with: ls -la {output_path}")
            if any(f.endswith('.nc') for f in downloaded_files):
                click.echo("💡 Analyze NetCDF files with: ncdump -h <file.nc>")

    except Exception as e:
        click.echo(f"❌ Sync error: {e}", err=True)
        logger.exception("File sync failed")
