"""Status command for monitoring rompy pipeline runs via Oceanum Prax."""

import json
import logging
from datetime import datetime

import click
from oceanum.cli.models import ContextObject

from oceanum.cli.prax.client import PRAXClient


logger = logging.getLogger(__name__)


@click.command()
@click.argument("run_id", required=True)
@click.option("--pipeline-name", required=True, help="Pipeline name")
@click.option("--org", envvar="PRAX_ORG", help="Prax organization (overrides oceanum context)")
@click.option("--user", envvar="PRAX_USER", help="Prax user email (overrides oceanum context)")
@click.option("--project", envvar="PRAX_PROJECT", help="Prax project (overrides oceanum context)")
@click.option("--stage", envvar="PRAX_STAGE", help="Prax stage (overrides oceanum context)")

@click.option("--format", "output_format", type=click.Choice(["table", "json", "brief"]), default="table", help="Output format")
@click.option("--watch", is_flag=True, help="Watch status updates (refresh every 30 seconds)")
@click.option("--refresh-interval", default=30, help="Refresh interval in seconds when watching")
@click.pass_context
def status(
    ctx,
    run_id,
    pipeline_name,
    org,
    user,
    project,
    stage,
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
        
    For more detailed status information, use the 'oceanum prax describe' commands:
        oceanum prax describe pipeline-runs <run_id>
    """
    # Instantiate Oceanum client
    try:
        client = PRAXClient(ctx)
    except Exception as e:
        click.echo(f"\u274c Configuration error: {e}", err=True)
        return

    def _display_status():
        """Display status information."""
        try:
            status_info = client.get_run_status(run_id, pipeline_name)

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
        click.echo(f"📅 Started: {_format_timestamp(status_info.get('started_at'))}")
        click.echo(f"🕒 Finished: {_format_timestamp(status_info.get('finished_at'))}")

        # Message
        if status_info.get('message'):
            click.echo(f"💬 Message: {status_info['message']}")

        # Details
        if status_info.get('details'):
            click.echo(f"\n📋 Details:")
            for key, value in status_info['details'].items():
                click.echo(f"  • {key}: {value}")

        # Logs info
        click.echo(f"\n💡 View logs with: oceanum prax logs pipeline-runs {run_id}")

    def _display_brief_status(status_info):
        """Display brief status information."""
        status = status_info.get('status', 'Unknown')
        updated = _format_timestamp(status_info.get('finished_at') or status_info.get('started_at'), brief=True)

        click.echo(f"{_format_status(status)} | {updated}")

    def _format_status(status):
        """Format status with appropriate emoji and color."""
        status_map = {
            'running': '🏃 Running',
            'completed': '✅ Completed',
            'succeeded': '✅ Completed',
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
                    status_info = client.get_run_status(run_id, pipeline_name)
                    if status_info.get('status', '').lower() in ['completed', 'succeeded', 'failed', 'cancelled']:
                        click.echo("\n🏁 Run completed. Stopping watch mode.")
                        break
                except Exception:
                    pass

        except KeyboardInterrupt:
            click.echo("\n👋 Watch mode stopped.")