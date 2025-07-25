"""Status command for monitoring rompy pipeline runs via Oceanum Prax."""

import json
import logging
from datetime import datetime

import click
from oceanum.cli.models import ContextObject

from ...config import PraxConfig
from ...client import PraxClient


logger = logging.getLogger(__name__)


@click.command()
@click.argument("run_id", required=True)
@click.option(
    "--project",
    envvar="PRAX_PROJECT",
    help="Prax project (overrides oceanum context)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "brief"]),
    default="table",
    help="Output format"
)
@click.option(
    "--watch",
    is_flag=True,
    help="Watch status updates (refresh every 30 seconds)"
)
@click.option(
    "--refresh-interval",
    default=30,
    help="Refresh interval in seconds when watching"
)
@click.pass_obj
def status(
    obj: ContextObject,
    run_id,
    project,
    output_format,
    watch,
    refresh_interval
):
    """Get status for a rompy pipeline run.

    Args:
        run_id: Prax pipeline run identifier

    Usage:
        oceanum rompy status abc123-def456-789
        oceanum rompy status abc123 --format json
        oceanum rompy status abc123 --watch
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

    def _display_status():
        """Display status information."""
        try:
            status_info = client.get_run_status(run_id)

            if output_format == "json":
                click.echo(json.dumps(status_info, indent=2))
            elif output_format == "brief":
                _display_brief_status(status_info)
            else:
                _display_table_status(status_info, run_id)

        except Exception as e:
            click.echo(f"❌ Error retrieving status: {e}", err=True)
            return False
        return True

    def _display_table_status(status_info, run_id):
        """Display status in table format."""
        click.echo(f"📊 Status for run: {run_id}")
        click.echo("=" * 50)

        # Basic info
        click.echo(f"🏃 Status: {_format_status(status_info.get('status', 'Unknown'))}")
        click.echo(f"📅 Created: {_format_timestamp(status_info.get('created_at'))}")
        click.echo(f"🕒 Updated: {_format_timestamp(status_info.get('updated_at'))}")

        # Pipeline info
        if 'pipeline' in status_info:
            pipeline = status_info['pipeline']
            click.echo(f"🔧 Pipeline: {pipeline.get('name', 'Unknown')}")
            click.echo(f"📦 Version: {pipeline.get('version', 'Unknown')}")

        # Stage information
        if 'stages' in status_info:
            click.echo("\n📋 Stages:")
            for stage in status_info['stages']:
                stage_status = _format_status(stage.get('status', 'Unknown'))
                stage_name = stage.get('name', 'Unknown')
                click.echo(f"  • {stage_name}: {stage_status}")

                if stage.get('error'):
                    click.echo(f"    ❌ Error: {stage['error']}")

        # Resource usage
        if 'resources' in status_info:
            resources = status_info['resources']
            click.echo(f"\n💻 Resources:")
            if 'cpu' in resources:
                click.echo(f"  🖥️  CPU: {resources['cpu']}")
            if 'memory' in resources:
                click.echo(f"  🧠 Memory: {resources['memory']}")
            if 'duration' in resources:
                click.echo(f"  ⏱️  Duration: {_format_duration(resources['duration'])}")

        # Logs info
        if status_info.get('has_logs'):
            click.echo(f"\n💡 View logs with: oceanum rompy logs {run_id}")

        # Output info
        if status_info.get('outputs'):
            click.echo(f"\n💡 Download outputs with: oceanum rompy sync {run_id} ./outputs")

    def _display_brief_status(status_info):
        """Display brief status information."""
        status = status_info.get('status', 'Unknown')
        pipeline = status_info.get('pipeline', {}).get('name', 'Unknown')
        updated = _format_timestamp(status_info.get('updated_at'), brief=True)

        click.echo(f"{_format_status(status)} | {pipeline} | {updated}")

    def _format_status(status):
        """Format status with appropriate emoji and color."""
        status_map = {
            'running': '🏃 Running',
            'completed': '✅ Completed',
            'failed': '❌ Failed',
            'pending': '⏳ Pending',
            'cancelled': '🛑 Cancelled',
            'timeout': '⏰ Timeout'
        }
        return status_map.get(status.lower(), f"❓ {status}")

    def _format_timestamp(timestamp, brief=False):
        """Format timestamp for display."""
        if not timestamp:
            return "Unknown"

        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp

            if brief:
                return dt.strftime("%H:%M:%S")
            else:
                return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            return str(timestamp)

    def _format_duration(duration_seconds):
        """Format duration in human readable format."""
        if not duration_seconds:
            return "Unknown"

        try:
            duration = int(duration_seconds)
            hours, remainder = divmod(duration, 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        except Exception:
            return str(duration_seconds)

    # Initial status display
    if not _display_status():
        return

    # Watch mode
    if watch:
        import time
        click.echo(f"\n👀 Watching status (refresh every {refresh_interval}s). Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(refresh_interval)
                click.clear()
                if not _display_status():
                    break

                # Check if run is complete
                try:
                    status_info = client.get_run_status(run_id)
                    if status_info.get('status', '').lower() in ['completed', 'failed', 'cancelled']:
                        click.echo("\n🏁 Run completed. Stopping watch mode.")
                        break
                except Exception:
                    pass

        except KeyboardInterrupt:
            click.echo("\n👋 Watch mode stopped.")
