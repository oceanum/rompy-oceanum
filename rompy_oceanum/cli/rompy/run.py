"""Run command for submitting rompy configurations to Oceanum Prax."""

import json
import logging
import time
from pathlib import Path

import click
import rompy.model
import yaml
from oceanum.cli.models import ContextObject

from ...config import DataMeshConfig, PraxConfig
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
@click.argument(
    "model", type=click.Choice(["swan", "schism", "ww3"]), envvar="ROMPY_MODEL"
)
@click.option(
    "--pipeline-name",
    required=False,
    help="Name of the Prax pipeline (required unless --local is specified)",
)
@click.option(
    "--project", envvar="PRAX_PROJECT", help="Prax project (overrides oceanum context)"
)
@click.option("--stage", default="dev", envvar="PRAX_STAGE", help="Deployment stage")
@click.option("--wait/--no-wait", default=False, help="Wait for completion")
@click.option("--timeout", default=3600, help="Timeout in seconds")
@click.option(
    "--local",
    is_flag=True,
    help="Run the model locally using Docker instead of submitting to Prax",
)
@click.pass_obj
def run(
    obj: ContextObject,
    config,
    model,
    pipeline_name,
    project,
    stage,
    wait,
    timeout,
    local,
):
    """Submit rompy configuration to Prax for execution or run locally with Docker.

    Args:
        config: Path to rompy configuration file (YAML or JSON)
        model: Model type (swan, schism, ww3)
        pipeline_name: Name of the Prax pipeline to execute (required unless --local is specified)
        local: If True, run the model locally using Docker instead of submitting to Prax

    Usage:
        oceanum rompy run config.yml swan --pipeline-name my-swan-pipeline
        oceanum rompy run config.yml swan --local

    For deployment and monitoring of runs, use the 'oceanum prax' commands:
        oceanum prax list pipelines
        oceanum prax submit pipeline <pipeline_name>
        oceanum prax logs pipeline-runs <run_id>
        oceanum prax describe pipeline-runs <run_id>
    """
    # Validate required parameters
    if not local and not pipeline_name:
        click.echo(
            "❌ Error: --pipeline-name is required unless --local is specified",
            err=True,
        )
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
        if model.lower() == "swan" and SwanModelRun is not None:
            model_run = SwanModelRun.model_validate(config_data)
        elif model.lower() == "schism" and SchismModelRun is not None:
            model_run = SchismModelRun.model_validate(config_data)
        elif model.lower() == "ww3" and Ww3ModelRun is not None:
            model_run = Ww3ModelRun.model_validate(config_data)
        else:
            # Fallback to generic ModelRun
            model_run = rompy.model.ModelRun.model_validate(config_data)

        click.echo(f"✅ ModelRun created successfully: {model_run.run_id}")

    except Exception as e:
        click.echo(f"⚠️  Configuration validation failed: {e}")
        click.echo("🔄 Creating compatible configuration for Prax submission...")

        # Create a simplified ModelRun-like object for Prax submission
        run_id = config_data.get("run_id", f"{model}_run_{int(time.time())}")

        class PraxCompatibleRun:
            def __init__(self, run_id, config_data, model_type):
                self.run_id = run_id
                self.config_data = config_data
                self.model_type = model_type
                self.output_dir = "./tmp/rompy"
                self.staging_dir = None

            def dump_inputs_dict(self):
                """Return configuration suitable for Prax submission."""
                # Clean up config for Prax submission
                clean_config = dict(config_data)
                # Remove metadata that might cause issues
                clean_config.pop("_metadata", None)
                # Ensure basic structure
                if "config" not in clean_config:
                    clean_config["config"] = {"model_type": self.model_type}
                elif "model_type" not in clean_config["config"]:
                    clean_config["config"]["model_type"] = self.model_type

                return clean_config

        model_run = PraxCompatibleRun(run_id, config_data, model)
        click.echo(f"✅ Created Prax-compatible run: {model_run.run_id}")

    # If running locally, execute the model directly
    if local:
        click.echo("🔄 Running model locally with Docker...")
        _run_local(model_run, model)
        return

    # Create Prax configuration using oceanum context
    # Use oceanum's authenticated context instead of manual token management
    prax_config_data = {
        "org": obj.domain.split(".")[0] if "." in obj.domain else obj.domain,
        "stage": stage,
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

    # Submit pipeline
    click.echo(f"🚀 Submitting to pipeline: {pipeline_name}")
    click.echo(f"📊 Model: {model}, Run ID: {model_run.run_id}")
    click.echo(
        f"🏢 Org: {prax_config.org}, Project: {prax_config.project}, Stage: {prax_config.stage}"
    )

    if obj.domain != "oceanum.io":
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
            deploy_pipeline=False,  # Deployment should be done with oceanum prax commands
            wait_for_completion=wait,
            timeout=timeout,
            download_outputs=False,  # Downloading should be done with oceanum prax commands
        )

        if result["success"]:
            click.echo("✅ Pipeline submitted successfully!")

            # Check if prax_run_id is available
            if result.get("prax_run_id"):
                click.echo(f"🆔 Prax run ID: {result['prax_run_id']}")
                click.echo(
                    f"💡 Monitor with: oceanum prax logs pipeline-runs {result['prax_run_id']}"
                )
                click.echo(
                    f"💡 Check status with: oceanum prax describe pipeline-runs {result['prax_run_id']}"
                )
            else:
                click.echo("⚠️  No Prax run ID returned")

            click.echo(f"📋 Completed stages: {', '.join(result['stages_completed'])}")
        else:
            click.echo(
                f"❌ Pipeline submission failed: {result.get('message', 'Unknown error')}",
                err=True,
            )
            if result.get("error"):
                click.echo(f"🔍 Error details: {result['error']}", err=True)
            if result.get("stage"):
                click.echo(f"💥 Failed at stage: {result['stage']}", err=True)

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg and "pipelines" in error_msg:
            click.echo(f"❌ Pipeline '{pipeline_name}' not found", err=True)
            click.echo("💡 Try one of these options:")
            click.echo("   1. List available pipelines: oceanum prax list pipelines")
            click.echo("   2. Deploy pipeline: oceanum prax create pipeline --help")
        else:
            click.echo(f"❌ Submission error: {e}", err=True)
        logger.exception("Pipeline submission failed")


def _run_local(model_run, model_type: str):
    """Run the model locally using Docker.

    Args:
        model_run: The ModelRun instance to execute
        model_type: Type of model (swan, schism, ww3)
    """
    try:
        # Import required modules
        from pathlib import Path

        import yaml
        from rompy.backends import DockerConfig

        # Get the pipeline template to extract the Docker image
        template_path = (
            Path(__file__).parent.parent.parent
            / "pipeline_templates"
            / f"{model_type}.yaml"
        )

        if not template_path.exists():
            click.echo(f"❌ Pipeline template not found at {template_path}", err=True)
            return

        # Load the pipeline template
        with open(template_path, "r") as f:
            template_data = yaml.safe_load(f)

        # Extract the run task image from the template
        run_image = None
        for task in template_data.get("resources", {}).get("tasks", []):
            if task.get("name") == "run":
                run_image = task.get("image")
                break

        if not run_image:
            click.echo("❌ Could not find run image in pipeline template", err=True)
            return

        click.echo(f"🐳 Using Docker image: {run_image}")

        # Generate the model configuration
        click.echo("🔄 Generating model configuration...")
        staging_dir = model_run.generate()
        click.echo(f"📁 Staging directory: {staging_dir}")

        # Create Docker configuration
        docker_config = DockerConfig(
            image=run_image,
            cpu=4,  # Default from template
            memory="2G",  # Default from template
            executable="mpirun -n 2 swan.exe",  # Default executable
            working_dir=staging_dir,
            volumes=[f"{staging_dir}:/tmp/rompy"],  # Mount staging directory
            env_vars={
                "OMPI_ALLOW_RUN_AS_ROOT": "1",
                "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
            },
        )

        # Run the model
        click.echo("🚀 Running model locally with Docker...")
        success = model_run.run(backend=docker_config, workspace_dir=str(staging_dir))

        if success:
            click.echo("✅ Model run completed successfully!")
            click.echo(f"📁 Results are in: {staging_dir}")
        else:
            click.echo("❌ Model run failed", err=True)

    except Exception as e:
        click.echo(f"❌ Error running model locally: {e}", err=True)
        logger.exception("Local model run failed")
