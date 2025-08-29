"""Logs command for viewing rompy pipeline run logs via Oceanum Prax."""

import logging
from datetime import datetime

import click
from oceanum.cli.models import ContextObject


from oceanum.cli.prax.client import PRAXClient


logger = logging.getLogger(__name__)


@click.command()
@click.argument("run_id", required=True)
@click.option(
    "--project",
    help="Prax project name (overrides oceanum context)",
)
@click.option(
    "--org",
    help="Prax organization name (overrides oceanum context)",
)
@click.option(
    "--user",
    help="Prax user email (overrides oceanum context)",
)
@click.option(
    "--stage",
    default="dev",
    help="Prax stage name (default: dev)",
)
@click.option(
    "--tail",
    default=100,
    help="Number of log lines to retrieve",
)
@click.option(
    "--follow",
    "-f",
    is_flag=True,
    help="Follow log output (like tail -f)",
)
@click.option(
    "--level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Filter logs by minimum level",
)
@click.option(
    "--since",
    help="Show logs since timestamp (ISO format: 2023-01-01T12:00:00)",
)
@click.option(
    "--timestamps/--no-timestamps",
    default=True,
    help="Show timestamps in log output",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude log lines containing these patterns (can be used multiple times)",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Output raw log lines without formatting",
)
@click.pass_context
def logs(
    ctx,
    run_id,
    project,
    org,
    user,
    stage,
    tail,
    follow,
    level,
    since,
    timestamps,
    exclude,
    raw
):
    """View logs for a rompy pipeline run.

    Args:
        run_id: Prax pipeline run identifier

    Usage:
        oceanum rompy logs abc123-def456-789
        oceanum rompy logs abc123 --tail 50 --follow
        oceanum rompy logs abc123 --stage generate --level ERROR
        oceanum rompy logs abc123 --since 2023-01-01T12:00:00
        
    For more advanced log viewing, use the 'oceanum prax logs' commands:
        oceanum prax logs pipeline-runs <run_id>
    """
    # Use official PRAXClient from oceanum.cli.prax.client
    from oceanum.cli.prax.client import PRAXClient

    # Instantiate PRAXClient with Click context for authentication/config
    client = PRAXClient(ctx)

    # Validate required parameters (project, org, etc.)
    if not project:
        click.echo("❌ Project is missing. Please specify --project or set PRAX_PROJECT.", err=True)
        return
    if not org:
        # Try to get org from context if not provided
        try:
            org = getattr(ctx.obj, "org", None) or getattr(ctx.obj, "domain", None)
        except Exception:
            org = None
        if not org:
            click.echo("❌ Organization is missing. Please specify --org or set PRAX_ORG.", err=True)
            return

    # Stage default
    if not stage:
        stage = "dev"

    def _format_log_line(log_entry):
        """Format a single log line for display."""
        if raw:
            if isinstance(log_entry, dict):
                return log_entry.get('message', '')
            return str(log_entry)

        # Handle string log entries
        if isinstance(log_entry, str):
            return log_entry

        # Extract components from dict log entries
        timestamp = log_entry.get('timestamp', '')
        log_level = log_entry.get('level', 'INFO')
        message = log_entry.get('message', '')
        stage_name = log_entry.get('stage', '')

        # Format timestamp
        formatted_time = ''
        if timestamps and timestamp:
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_time = str(timestamp)
            except Exception:
                formatted_time = str(timestamp)

        # Format level with colors/emojis
        level_map = {
            'DEBUG': '🔍 DEBUG',
            'INFO': 'ℹ️  INFO ',
            'WARNING': '⚠️  WARN ',
            'ERROR': '❌ ERROR',
            'CRITICAL': '🚨 CRIT '
        }
        formatted_level = level_map.get(log_level.upper(), f"   {log_level}")

        # Build output line
        parts = []
        if formatted_time:
            parts.append(f"[{formatted_time}]")
        parts.append(formatted_level)
        if stage_name:
            parts.append(f"[{stage_name}]")
        parts.append(message)

        return " ".join(parts)

    def _filter_logs(logs_list):
        """Apply filters to log entries."""
        filtered = logs_list

        # Filter by level
        if level:
            level_priority = {
                'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4
            }
            min_priority = level_priority.get(level.upper(), 0)
            filtered = [
                log for log in filtered
                if isinstance(log, dict) and level_priority.get(log.get('level', 'INFO').upper(), 1) >= min_priority
            ]

        # Filter by stage
        if stage:
            filtered = [
                log for log in filtered
                if isinstance(log, dict) and log.get('stage', '').lower() == stage.lower()
            ]

        # Filter by timestamp
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                filtered = [
                    log for log in filtered
                    if isinstance(log, dict) and _parse_timestamp(log.get('timestamp')) >= since_dt
                ]
            except ValueError:
                click.echo(f"⚠️  Invalid timestamp format: {since}", err=True)

        # Filter out excluded patterns
        if exclude:
            for pattern in exclude:
                filtered = [
                    log for log in filtered
                    if not (
                        (isinstance(log, dict) and pattern in log.get('message', '')) or
                        (isinstance(log, str) and pattern in log)
                    )
                ]

        return filtered

    def _parse_timestamp(timestamp_str):
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return datetime.min
        try:
            if isinstance(timestamp_str, str):
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return timestamp_str
        except Exception:
            return datetime.min

    def _display_logs():
        """Retrieve and display logs."""
        try:
            # Get logs from PRAXClient
            log_iter = client.get_pipeline_run_logs(
                run_id,
                lines=tail,
                follow=False,
                org=org,
                user=user,
                project=project,
                stage=stage,
            )
            logs_list = list(log_iter)

            # Handle error response
            if logs_list and hasattr(logs_list[0], 'detail'):
                click.echo(f"❌ Error retrieving logs: {getattr(logs_list[0], 'detail', logs_list[0])}", err=True)
                return False

            if not logs_list:
                click.echo("📭 No logs found for this run.")
                return True

            # Apply filters
            filtered_logs = _filter_logs(logs_list)

            if not filtered_logs:
                click.echo("📭 No logs match the specified filters.")
                return True

            # Display header
            if not raw and not follow:
                filter_info = []
                if stage:
                    filter_info.append(f"stage={stage}")
                if level:
                    filter_info.append(f"level>={level}")
                if since:
                    filter_info.append(f"since={since}")

                filter_str = f" ({', '.join(filter_info)})" if filter_info else ""
                click.echo(f"📋 Logs for run {run_id}{filter_str}:")
                click.echo("=" * 50)

            # Display logs
            for log_entry in filtered_logs:
                click.echo(_format_log_line(log_entry))

            return True

        except Exception as e:
            click.echo(f"❌ Error retrieving logs: {e}", err=True)
            return False

    # Initial log display
    if not _display_logs():
        return

    # Follow mode
    if follow:
        click.echo(f"\n👀 Following logs (streaming). Press Ctrl+C to stop.")
        try:
            for log_line in client.get_pipeline_run_logs(
                run_id,
                lines=tail,
                follow=True,
                org=org,
                user=user,
                project=project,
                stage=stage,
            ):
                # Handle error response
                if hasattr(log_line, 'detail'):
                    click.echo(f"❌ Error retrieving logs: {getattr(log_line, 'detail', log_line)}", err=True)
                    break
                # Optionally parse and filter log lines if needed
                click.echo(_format_log_line(log_line))
                # Optionally, check run status and break if completed
                status_info = client.get_pipeline_run(
                    run_id,
                    org=org,
                    user=user,
                    project=project,
                    stage=stage,
                )
                if hasattr(status_info, 'status') and getattr(status_info, 'status', '').lower() in ['completed', 'failed', 'cancelled']:
                    click.echo("\n🏁 Run completed. Stopping log following.")
                    break
        except KeyboardInterrupt:
            click.echo("\n👋 Log following stopped.")
