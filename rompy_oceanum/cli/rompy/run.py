"""Run command for executing rompy configurations via Oceanum Prax."""

import json
import logging
import time
from pathlib import Path

import click
import yaml
import rompy.model
from oceanum.cli.common.models import ContextObject

from ...config import PraxConfig, DataMeshConfig
from ...pipeline import PraxPipelineBackend

# Import model classes for different types
try:
    from rompy.swan.model import SwanModelRun
except ImportError:
    SwanModelRun = None

try:
    from rompy.schism.model import SchismModelRun
except ImportError:
    SchismModelRun = None

try:
    from rompy.ww3.model import Ww3ModelRun
except ImportError:
    Ww3ModelRun = None


logger = logging.getLogger(__name__)


@click.command()
@click.argument("config", envvar="ROMPY_CONFIG")
@click.argument("model", type=click.Choice(["swan", "schism", "ww3"]), envvar="ROMPY_MODEL")
@click.option(
    "--pipeline-name",
    required=True,
    help="Name of the Prax pipeline"
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
    "--template",
    help="Path to pipeline template file"
)
@click.option(
    "--deploy/--no-deploy",
    default=True,
    help="Deploy pipeline if needed"
)
@click.option(
    "--list-pipelines",
    is_flag=True,
    help="List available pipelines and exit"
)
@click.option(
    "--wait/--no-wait",
    default=False,
    help="Wait for completion"
)
@click.option(
    "--timeout",
    default=3600,
    help="Timeout in seconds"
)
@click.option(
    "--download/--no-download",
    default=False,
    help="Download outputs"
)
@click.option(
    "--output-dir",
    help="Output directory for downloads"
)
@click.option(
    "--zip/--no-zip",
    default=False,
    help="Create zip archive"
)
@click.pass_obj
def run(
    obj: ContextObject,
    config,
    model,
    pipeline_name,
    project,
    stage,
    template,
    deploy,
    wait,
    timeout,
    download,
    output_dir,
    zip,
    list_pipelines
):
    """Execute rompy configuration via Prax.

    Args:
        config: Path to rompy configuration file (YAML or JSON)
        model: Model type (swan, schism, ww3)
        pipeline_name: Name of the Prax pipeline to execute

    Usage:
        oceanum rompy run config.yml swan --pipeline-name my-swan-pipeline
        oceanum rompy run --list-pipelines  # List available pipelines
    """
    # Handle pipeline listing first
    if list_pipelines:
        _list_available_pipelines(obj, project, stage)
        return
    # Load configuration
    try:
        # First try to open it as a file
        config_path = Path(config)
        if config_path.exists():
            with open(config_path, "r") as f:
                content = f.read()
        else:
            # If not a file, treat it as raw content
            content = config
    except (FileNotFoundError, IsADirectoryError, OSError):
        # If not a file, treat it as raw content
        content = config

    try:
        # Try to parse as yaml first
        config_data = yaml.load(content, Loader=yaml.Loader)
    except yaml.YAMLError:
        try:
            # Fall back to JSON
            config_data = json.loads(content)
        except json.JSONDecodeError as e:
            click.echo(f"❌ Error parsing configuration: {e}", err=True)
            return

    # Create real rompy ModelRun instance or handle gracefully
    click.echo("🔄 Processing rompy configuration...")

    try:
        # First try to create proper ModelRun
        if model.lower() == 'swan' and SwanModelRun is not None:
            model_run = SwanModelRun.model_validate(config_data)
        elif model.lower() == 'schism' and SchismModelRun is not None:
            model_run = SchismModelRun.model_validate(config_data)
        elif model.lower() == 'ww3' and Ww3ModelRun is not None:
            model_run = Ww3ModelRun.model_validate(config_data)
        else:
            # Fallback to generic ModelRun
            model_run = rompy.model.ModelRun.model_validate(config_data)

        click.echo(f"✅ ModelRun created successfully: {model_run.run_id}")

    except Exception as e:
        click.echo(f"⚠️  Configuration validation failed: {e}")
        click.echo("🔄 Creating compatible configuration for Prax submission...")

        # Create a simplified ModelRun-like object for Prax submission
        run_id = config_data.get('run_id', f"{model}_run_{int(time.time())}")

        class PraxCompatibleRun:
            def __init__(self, run_id, config_data, model_type):
                self.run_id = run_id
                self.config_data = config_data
                self.model_type = model_type
                self.output_dir = config_data.get('output_dir', './outputs')
                self.staging_dir = None

            def dump_inputs_dict(self):
                """Return configuration suitable for Prax submission."""
                # Clean up config for Prax submission
                clean_config = dict(config_data)
                # Remove metadata that might cause issues
                clean_config.pop('_metadata', None)
                # Ensure basic structure
                if 'config' not in clean_config:
                    clean_config['config'] = {'model_type': self.model_type}
                elif 'model_type' not in clean_config['config']:
                    clean_config['config']['model_type'] = self.model_type

                return clean_config

        model_run = PraxCompatibleRun(run_id, config_data, model)
        click.echo(f"✅ Created Prax-compatible run: {model_run.run_id}")

    # Create Prax configuration using oceanum context
    # Use oceanum's authenticated context instead of manual token management
    prax_config_data = {
        "org": obj.domain.split('.')[0] if '.' in obj.domain else obj.domain,
        "stage": stage
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

    # Create DataMesh configuration if available
    datamesh_config = None
    try:
        datamesh_config = DataMeshConfig.from_env()
    except Exception:
        pass  # DataMesh is optional

    # Execute pipeline
    click.echo(f"🚀 Executing pipeline: {pipeline_name}")
    click.echo(f"📊 Model: {model}, Run ID: {model_run.run_id}")
    click.echo(f"🏢 Org: {prax_config.org}, Project: {prax_config.project}, Stage: {prax_config.stage}")

    if obj.domain != 'oceanum.io':
        click.echo(f"🌍 Environment: {obj.domain}")

    try:
        # Create PraxPipelineBackend instance
        prax_backend = PraxPipelineBackend()

        # Execute pipeline using the backend directly
        result = prax_backend.execute(
            model_run=model_run,
            pipeline_name=pipeline_name,
            prax_config=prax_config,
            datamesh_config=datamesh_config,
            template_path=template,
            deploy_pipeline=deploy,
            wait_for_completion=wait,
            timeout=timeout,
            download_outputs=download,
            output_dir=output_dir
        )

        if result["success"]:
            click.echo("✅ Pipeline executed successfully!")

            # Check if prax_run_id is available
            if result.get("prax_run_id"):
                click.echo(f"🆔 Prax run ID: {result['prax_run_id']}")
                click.echo(f"💡 Monitor with: oceanum rompy status {result['prax_run_id']}")
            else:
                click.echo("⚠️  No Prax run ID returned (pipeline may be running locally)")

            click.echo(f"📋 Completed stages: {', '.join(result['stages_completed'])}")

            if download and result.get("downloaded_files"):
                click.echo(f"📥 Downloaded {len(result['downloaded_files'])} files")

            if zip:
                # Create zip archive of outputs
                import zipfile
                zip_path = Path(output_dir or f"outputs/{model_run.run_id}") / f"{model_run.run_id}.zip"
                zip_path.parent.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(zip_path, 'w') as zf:
                    if result.get("downloaded_files"):
                        for file_path in result["downloaded_files"]:
                            zf.write(file_path, Path(file_path).name)

                click.echo(f"📦 Created zip archive: {zip_path}")
        else:
            click.echo(f"❌ Pipeline execution failed: {result.get('message', 'Unknown error')}", err=True)
            if result.get("error"):
                click.echo(f"🔍 Error details: {result['error']}", err=True)
            if result.get("stage"):
                click.echo(f"💥 Failed at stage: {result['stage']}", err=True)

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg and "pipelines" in error_msg:
            click.echo(f"❌ Pipeline '{pipeline_name}' not found", err=True)
            click.echo("💡 Try one of these options:")
            click.echo(f"   1. List available pipelines: oceanum rompy run --list-pipelines")
            click.echo(f"   2. Deploy pipeline first: oceanum rompy run {config} {model} --pipeline-name {pipeline_name} --deploy --template <template_file>")
            click.echo(f"   3. Use existing pipeline name from step 1")
        else:
            click.echo(f"❌ Execution error: {e}", err=True)
        logger.exception("Pipeline execution failed")


def _list_available_pipelines(obj: ContextObject, project=None, stage=None):
    """List available pipelines in the Prax project."""
    try:
        # Create Prax configuration using oceanum context
        prax_config_data = {
            "org": obj.domain.split('.')[0] if '.' in obj.domain else obj.domain,
            "stage": stage or "dev"
        }

        # Override project if specified
        if project:
            prax_config_data["project"] = project

        # Use oceanum's token for authentication
        if obj.token and obj.token.access_token:
            prax_config_data["token"] = obj.token.access_token

        prax_config = PraxConfig.from_env(**prax_config_data)

        from ...client import PraxClient
        client = PraxClient(prax_config)

        click.echo("🔍 Listing available pipelines...")
        pipelines = client.list_pipelines()

        if pipelines:
            click.echo(f"✅ Found {len(pipelines)} pipelines:")
            for pipeline in pipelines:
                name = pipeline.get('name', 'unknown')
                desc = pipeline.get('description', 'No description')
                status = pipeline.get('status', 'unknown')
                click.echo(f"   📋 {name}: {desc} (Status: {status})")

            click.echo("\n💡 Usage:")
            click.echo("   oceanum rompy run config.yml swan --pipeline-name <pipeline_name>")
        else:
            click.echo("📭 No pipelines found in this project")
            click.echo("💡 You may need to deploy a pipeline first:")
            click.echo("   oceanum rompy run config.yml swan --pipeline-name my-pipeline --deploy --template <template_file>")

    except Exception as e:
        click.echo(f"❌ Failed to list pipelines: {e}", err=True)
        click.echo("💡 Make sure you're authenticated: oceanum auth login")
