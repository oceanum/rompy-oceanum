"""Utilities for rompy CLI - config loading and parameter conversion."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

import click
import yaml


def load_rompy_config(config_path: str) -> Dict[str, Any]:
    """Load and parse rompy configuration file.

    Args:
        config_path: Path to rompy configuration file (YAML or JSON)

    Returns:
        Dictionary containing rompy configuration

    Raises:
        click.ClickException: If file not found or invalid format
    """
    path = Path(config_path)
    if not path.exists():
        raise click.ClickException(f"Configuration file not found: {config_path}")

    try:
        with open(path) as f:
            if path.suffix in ['.yml', '.yaml']:
                return yaml.safe_load(f)
            elif path.suffix == '.json':
                return json.load(f)
            else:
                raise click.ClickException(
                    f"Unsupported config format: {path.suffix}. "
                    "Use .yml, .yaml, or .json"
                )
    except Exception as e:
        raise click.ClickException(f"Failed to load configuration: {e}")


def detect_model_type(config: Dict[str, Any]) -> str:
    """Detect the model type from rompy configuration.

    Args:
        config: Rompy configuration dictionary

    Returns:
        Model type string (swan, schism, ww3)
    """
    # Check explicit model_type field
    if 'model_type' in config:
        return config['model_type'].lower()

    # Check for model-specific sections
    if 'swan' in config or 'SWAN' in config:
        return 'swan'
    elif 'schism' in config or 'SCHISM' in config:
        return 'schism'
    elif 'ww3' in config or 'WW3' in config:
        return 'ww3'

    # Check class name if present
    if 'class' in config:
        class_name = config['class'].lower()
        if 'swan' in class_name:
            return 'swan'
        elif 'schism' in class_name:
            return 'schism'
        elif 'ww3' in class_name:
            return 'ww3'

    # Default to swan
    return 'swan'


def convert_to_pipeline_params(config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
    """Convert rompy configuration to pipeline parameters.

    Args:
        config: Rompy configuration dictionary
        config_path: Original path to config file

    Returns:
        Dictionary of parameters suitable for pipeline submission
    """
    # Detect model type
    model_type = detect_model_type(config)

    # Build parameters - keep it simple to avoid command line issues
    params = {
        'config_path': str(Path(config_path).absolute()),
        'model_type': model_type,
        'datamesh-token': '',  # Required by SWAN pipeline
    }

    # Extract datamesh token if present in the configuration
    # Look in common locations where tokens might be stored
    token = None

    # Check in inpgrid sources
    if 'config' in config and 'inpgrid' in config['config']:
        inpgrid = config['config']['inpgrid']

        # Check bottom source token
        if 'bottom' in inpgrid and 'source' in inpgrid['bottom'] and 'token' in inpgrid['bottom']['source']:
            token = inpgrid['bottom']['source']['token']

        # Check input sources
        if not token and 'input' in inpgrid and isinstance(inpgrid['input'], list):
            for input_src in inpgrid['input']:
                if 'source' in input_src and 'token' in input_src['source']:
                    token = input_src['source']['token']
                    if token:
                        break

    # If token found, add it
    if token:
        params['datamesh-token'] = token

    # Add run metadata if present - these are typically small values safe for command line
    if 'metadata' in config:
        params.update({
            f'metadata_{k}': v
            for k, v in config['metadata'].items()
            if isinstance(v, (str, int, float, bool))
        })

    return params


def format_pipeline_filters(project: Optional[str], org: Optional[str],
                          stage: str = "dev") -> Dict[str, str]:
    """Format filters for oceanum prax commands.

    Args:
        project: Project name (optional)
        org: Organization name (optional)
        stage: Deployment stage

    Returns:
        Dictionary of non-null filters
    """
    filters = {}
    if project:
        filters['project'] = project
    if org:
        filters['org'] = org
    if stage:
        filters['stage'] = stage
    return filters


def format_status_output(status_data: Dict[str, Any]) -> str:
    """Format pipeline status for display.

    Args:
        status_data: Status dictionary from prax API

    Returns:
        Formatted status string
    """
    status = status_data.get('status', 'unknown')
    run_id = status_data.get('id', status_data.get('run_id', 'unknown'))

    # Status emoji mapping
    status_emoji = {
        'running': '🔄',
        'pending': '⏳',
        'completed': '✅',
        'succeeded': '✅',
        'success': '✅',
        'failed': '❌',
        'error': '❌',
        'cancelled': '⛔',
    }

    emoji = status_emoji.get(status.lower(), '❓')

    lines = [
        f"{emoji} Pipeline Status",
        f"Run ID: {run_id}",
        f"Status: {status}",
    ]

    if 'started_at' in status_data:
        lines.append(f"Started: {status_data['started_at']}")

    if 'finished_at' in status_data:
        lines.append(f"Finished: {status_data['finished_at']}")

    if 'message' in status_data:
        lines.append(f"Message: {status_data['message']}")

    return '\n'.join(lines)


def parse_prax_response(response: str, expected_format: str = 'text') -> Any:
    """Parse response from oceanum prax command.

    Args:
        response: Raw response string
        expected_format: Expected format (json, text)

    Returns:
        Parsed response (dict for json, string for text)
        For text format, attempts to extract structured information like run IDs

    Raises:
        click.ClickException: If parsing fails when json is required
    """
    if not response:
        return {} if expected_format == 'json' else ''

    # For text format (default), extract structured info
    if expected_format == 'text':
        result = {}
        for line in response.strip().split('\n'):
            if "Run ID:" in line:
                result['id'] = line.split("Run ID:")[1].strip()
            elif "Status:" in line:
                result['status'] = line.split("Status:")[1].strip()

        # If we found structured info, return it as a dict
        if result:
            return result

        # Otherwise, just return the raw text
        return response

    # For JSON format (when explicitly requested)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from mixed output
        lines = response.strip().split('\n')
        for line in reversed(lines):
            try:
                return json.loads(line)
            except:
                continue

        # If we couldn't parse JSON but it was required, raise exception
        raise click.ClickException(f"Failed to parse JSON response")
