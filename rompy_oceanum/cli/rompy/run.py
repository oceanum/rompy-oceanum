"""Run command for submitting rompy configurations to Oceanum Prax."""

import json
import logging
import sys
import time
from pathlib import Path

import click
import rompy.model
import yaml
from oceanum.cli.models import ContextObject
from oceanum.cli.prax.client import PRAXClient

from ...config import DataMeshConfig

# Only generic ModelRun is available
# Specific model classes (SwanModelRun, SchismModelRun, etc.) are not present


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
@click.option(
    "--org", envvar="PRAX_ORG", help="Prax organization (overrides oceanum context)"
)
@click.option(
    "--user", envvar="PRAX_USER", help="Prax user email (overrides oceanum context)"
)
@click.option("--stage", default="dev", envvar="PRAX_STAGE", help="Deployment stage")
@click.option("--wait/--no-wait", default=False, help="Wait for completion")
@click.option("--timeout", default=3600, help="Timeout in seconds")
@click.option(
    "--local",
    is_flag=True,
    help="Run the model locally using Docker instead of submitting to Prax",
)
@click.option(
    "--follow",
    is_flag=True,
    help="Follow logs after submission",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude log lines containing these patterns (can be used multiple times with --follow)",
    default=["[wait]"],
)
@click.option(
    "--watch",
    is_flag=True,
    help="Watch and print task statuses after submission (mutually exclusive with --follow)",
)
@click.pass_context
def run(
    ctx: click.Context,
    config,
    model,
    pipeline_name,
    project,
    org,
    user,
    stage,
    wait,
    timeout,
    local,
    follow,
    exclude,
    watch,
):
    """Submit rompy configuration to Prax for execution or run locally with Docker.

    Args:
        config: Path to rompy configuration file (YAML or JSON)
        model: Model type (swan, schism, ww3)
        pipeline_name: Name of the Prax pipeline to execute (required unless --local is specified)
        local: If True, run the model locally using Docker instead of submitting to Prax
        follow: If True, follow logs after submission

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
    click.echo("🔄   Setting output to predictable place for prax")
    config_data["output_dir"] = "/tmp/rompy"
    config_data["run_id_subdir"] = False

    try:
        run_id = config_data.get("run_id", f"{model}_run_{int(time.time())}")
        model_run = rompy.model.ModelRun.model_validate(config_data)
        click.echo(f"✅ ModelRun created successfully: {model_run.run_id}")

    except Exception as e:
        click.echo(f"⚠️  Configuration validation failed: {e}")
        sys.exit(1)
        # #click.echo("🔄 Creating compatible configuration for Prax submission...")
        #
        # # Create a simplified ModelRun-like object for Prax submission
        # run_id = config_data.get("run_id", f"{model}_run_{int(time.time())}")
        #
        # class PraxCompatibleRun:
        #     def __init__(self, run_id, config_data, model_type):
        #         self.run_id = run_id
        #         self.config_data = config_data
        #         self.model_type = model_type
        #         self.output_dir = "./tmp/rompy"
        #
        #     def dump_inputs_dict(self):
        #         """Return configuration suitable for Prax submission."""
        #         # Clean up config for Prax submission
        #         clean_config = dict(config_data)
        #         # Remove metadata that might cause issues
        #         clean_config.pop("_metadata", None)
        #         # Ensure basic structure
        #         if "config" not in clean_config:
        #             clean_config["config"] = {"model_type": self.model_type}
        #         elif "model_type" not in clean_config["config"]:
        #             clean_config["config"]["model_type"] = self.model_type
        #         clean_config["datamesh-token"] = DataMeshConfig.from_env().token
        #         return clean_config
        #
        # model_run = PraxCompatibleRun(run_id, config_data, model)
        # click.echo(f"✅ Created Prax-compatible run: {model_run.run_id}")

    # If running locally, execute the model directly
    if local:
        click.echo("🔄 Running model locally with Docker...")
        _run_local(model_run, model)
        return

    # Submit pipeline using official PRAXClient (auth/config handled by client)
    click.echo(f"🚀 Submitting to pipeline: {pipeline_name}")
    click.echo(f"📊 Model: {model}, Run ID: {model_run.run_id}")

    try:
        client = PRAXClient(ctx)
        parameters = {
            "rompy-config": model_run.dump_inputs_dict(),
            "datamesh-token": DataMeshConfig.from_env().token,
        }
        result = client.submit_pipeline(
            pipeline_name,
            parameters=parameters,
            org=org,
            user=user,
            project=project,
            stage=stage,
        )

        # Success: result should have last_run.id and last_run.name
        last_run = getattr(result, "last_run", None)
        if last_run is not None and hasattr(last_run, "id"):
            run_id = getattr(last_run, "id", None)
            run_name = getattr(last_run, "name", run_id)
            click.echo("✅ Pipeline submitted successfully!")
            click.echo(f"🆔 Prax run ID: {run_id}")
            click.echo(
                f"💡 Monitor with: oceanum prax logs pipeline {pipeline_name} - Note you can only see logs from the last run, this is WIP"
            )
            # Mutually exclusive: --follow and --watch
            if follow and watch:
                click.echo("❌ --follow and --watch cannot be used together.", err=True)
                return
            if follow:
                click.echo(
                    f"\n📋 Following logs for latest run of pipeline {pipeline_name}:"
                )
                try:
                    last_status = None
                    while True:
                        lines = 1000
                        for line in client.get_pipeline_run_logs(
                            run_name,
                            lines,
                            True,
                            org=org,
                            user=user,
                            project=project,
                            stage=stage,
                        ):
                            # Exclude lines containing any pattern in exclude
                            if any(pat in str(line) for pat in exclude):
                                continue
                            # ErrorResponse handling
                            if hasattr(line, "detail") or (
                                isinstance(line, dict) and "detail" in line
                            ):
                                click.echo(
                                    f"❌ Error fetching logs: {getattr(line, 'detail', line)}",
                                    err=True,
                                )
                                break
                            # Unicode handling
                            if isinstance(line, bytes):
                                line = line.decode("utf-8", errors="replace")
                            click.echo(str(line))
                        run_status = client.get_pipeline_run(
                            run_name,
                            org=org,
                            user=user,
                            project=project,
                            stage=stage,
                        )
                        status = getattr(run_status, "status", None)
                        if status:
                            if status != last_status:
                                click.echo(f"Status: {status}")
                                last_status = status
                            if status.lower() in [
                                "completed",
                                "succeeded",
                                "failed",
                                "error",
                            ]:
                                click.echo(f"Final status: {status}")
                                break
                        else:
                            continue

                except Exception as e:
                    click.echo(f"❌ Error streaming logs: {e}", err=True)
                    logger.exception("Log streaming failed")
            if watch:
                click.echo(
                    f"\n👀 Watching status for latest run of pipeline {pipeline_name}:"
                )
                try:
                    poll_interval = 10
                    last_status = None
                    while True:
                        run_status = client.get_pipeline_run(
                            run_name, org=org, user=user, project=project, stage=stage
                        )
                        status = getattr(run_status, "status", None)
                        if status:
                            if status != last_status:
                                click.echo(f"Status: {status}")
                                last_status = status
                            if status.lower() in [
                                "completed",
                                "succeeded",
                                "failed",
                                "error",
                            ]:
                                click.echo(f"Final status: {status}")
                                break
                        else:
                            detail = getattr(run_status, "detail", None)
                            if detail:
                                click.echo(
                                    f"❌ Error fetching status: {detail}", err=True
                                )
                            else:
                                click.echo(
                                    f"❌ Error fetching status: Unknown error", err=True
                                )
                            break
                        time.sleep(poll_interval)
                except Exception as e:
                    click.echo(f"❌ Error watching status: {e}", err=True)
                    logger.exception("Status watching failed")

            click.echo(
                f"📋 Grid data be available at: https://ui.datamesh.oceanum.io/datasource/rompy-{model_run.run_id}-grid"
            )
            click.echo(
                f"📋 Spectra be available at:   https://ui.datamesh.oceanum.io/datasource/rompy-{model_run.run_id}-grid"
            )

        else:
            # Handle error responses gracefully
            error_detail = getattr(result, "detail", None)
            if error_detail:
                click.echo(
                    f"❌ Pipeline submission failed: {error_detail}",
                    err=True,
                )
            else:
                click.echo(
                    "❌ Pipeline submission failed: No run information returned (missing last_run).",
                    err=True,
                )
            error_message = getattr(result, "message", None)
            if error_message:
                click.echo(f"❌ Error message: {error_message}", err=True)
            return
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
            timeout=3600,
            dockerfile=None,
            mpiexec="",
            build_args={},
            build_context=None,
            remove_container=True,
            user="root",
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
