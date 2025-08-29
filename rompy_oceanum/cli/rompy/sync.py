'''Sync command for downloading and managing rompy pipeline outputs.'''

import logging
import shutil
from pathlib import Path
from typing import List, Optional

import click
from oceanum.cli.prax.client import PRAXClient

logger = logging.getLogger(__name__)

@click.command()
@click.argument("run_id", required=True)
@click.argument("output_dir", required=True)
@click.option("--org", envvar="PRAX_ORG", help="Prax organization (overrides oceanum context)")
@click.option("--user", envvar="PRAX_USER", help="Prax user email (overrides oceanum context)")
@click.option("--project", envvar="PRAX_PROJECT", help="Prax project (overrides oceanum context)")
@click.option("--stage", envvar="PRAX_STAGE", help="Prax stage (overrides oceanum context)")

@click.option("--pattern", default="*", help="File pattern to download (glob pattern)")
@click.option("--file-format", "file_format", multiple=True, help="Filter by file format (e.g., .nc, .dat, .csv). Can be specified multiple times")
@click.option("--organize/--no-organize", default=True, help="Organize files by stage and type")
@click.option("--overwrite/--no-overwrite", default=False, help="Overwrite existing files")
@click.option("--verify/--no-verify", default=True, help="Verify file integrity after download")
@click.option("--compress/--no-compress", default=False, help="Create compressed archive of downloaded files")
@click.option("--metadata/--no-metadata", default=True, help="Download metadata and manifest files")
@click.option("--dry-run", is_flag=True, help="Show what would be downloaded without actually downloading")
@click.pass_context
def sync(
    ctx,
    run_id,
    output_dir,
    org,
    user,
    project,
    stage,
    pattern,
    file_format,
    organize,
    overwrite,
    verify,
    compress,
    metadata,
    dry_run
):
    '''Sync outputs from a rompy pipeline run to local directory.'''
    client = PRAXClient(ctx)
    output_path = Path(output_dir)
    if not dry_run:
        output_path.mkdir(parents=True, exist_ok=True)

    def _filter_files(file_list: List[dict]) -> List[dict]:
        filtered = file_list
        if stage:
            filtered = [f for f in filtered if f.get('stage', '').lower() == stage.lower()]
        if file_format:
            formats = [fmt.lower() if fmt.startswith('.') else f'.{fmt.lower()}' for fmt in file_format]
            filtered = [f for f in filtered if any(f.get('name', '').lower().endswith(fmt) for fmt in formats)]
        if pattern and pattern != "*":
            import fnmatch
            filtered = [f for f in filtered if fnmatch.fnmatch(f.get('name', ''), pattern)]
        return filtered

    def _organize_file_path(file_info: dict, base_path: Path) -> Path:
        if not organize:
            return base_path / file_info.get('name', 'unknown')
        stage_name = file_info.get('stage', 'unknown')
        file_name = file_info.get('name', 'unknown')
        file_ext = Path(file_name).suffix.lower() or 'other'
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
        try:
            if size_bytes is None or not isinstance(size_bytes, (int, float)):
                return "Unknown"
            size = float(size_bytes)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except Exception:
            return "Unknown"

    def _verify_file(local_path: Path, expected_size: Optional[int] = None) -> bool:
        if not local_path.exists():
            return False
        if expected_size is not None:
            actual_size = local_path.stat().st_size
            if actual_size != expected_size:
                logger.warning(f"Size mismatch for {local_path}: expected {expected_size}, got {actual_size}")
                return False
        return True

    try:
        click.echo(f"🔍 Discovering files for run: {run_id}")
        # NOTE: The new PraxClient does not have list_run_artifacts; this should be implemented or replaced with the correct method.
        # For now, we will raise NotImplementedError to indicate this needs to be completed.
        raise NotImplementedError("list_run_artifacts is not implemented in the new PraxClient. Please update this logic.")
    except Exception as e:
        click.echo(f"❌ Sync error: {e}", err=True)
        logger.exception("File sync failed")
