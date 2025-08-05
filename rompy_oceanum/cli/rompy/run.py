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
from ...prax_client import PraxClientWrapper

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
@click.option(
    "--follow",
    is_flag=True,
    help="Follow logs after submission",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude log lines containing these patterns (can be used multiple times with --follow)",
    default=['[wait]'],
)
@click.option(
    "--watch",
    is_flag=True,
    help="Watch and print task statuses after submission (mutually exclusive with --follow)",
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
            ctx=click.get_current_context(),  # Pass the click context
        )

        if result["success"]:
            click.echo("✅ Pipeline submitted successfully!")

            # Check if prax_run_id is available
            if result.get("prax_run_id"):
                click.echo(f"🆔 Prax run ID: {result['prax_run_id']}")
                # Use run name for logs and status if available
                run_identifier = result.get("prax_run_name", result["prax_run_id"])
                click.echo(
                    f"💡 Monitor with: oceanum prax logs pipeline-runs {run_identifier} NOT YET IMPLEMENTED"
                )
                click.echo(
                    f"💡 Check status with: oceanum prax describe pipeline-runs {run_identifier} NOT YET IMPLEMENTED"
                )

            # Follow logs if requested (must be outside the if result.get("prax_run_id") block)
            # Mutually exclusive: --follow and --watch
            if follow and watch:
                click.echo("❌ --follow and --watch cannot be used together.", err=True)
                return

            if follow and result.get("prax_run_id"):
                click.echo(
                    f"\n📋 Following logs for latest run of pipeline {pipeline_name}:"
                )
                try:
                    # Create PraxClientWrapper for log following
                    prax_client_wrapper = PraxClientWrapper(prax_config)
                    logger.info(
                        "Created PraxClientWrapper for log following (pipeline mode)"
                    )
                    click.echo("\n📋 Pipeline logs (streaming):")
                    import time

                    for nn in range(3):
                        logger.info(f"Logs for task {nn + 1}")
                        log_stream = prax_client_wrapper.get_run_logs(
                            run_name=result["prax_run_id"],
                            tail=100,
                            follow=True,
                        )

                        last_log_time = time.time()
                        log_received = False
                        progress_interval = 10  # seconds
                        last_progress = time.time()
                        run_id = result["prax_run_id"]
                        prax_client_wrapper = PraxClientWrapper(prax_config)
                        try:
                            for line in log_stream:
                                try:
                                    # Handle bytes, and also string representations of bytes (e.g. "b'...'")
                                    import ast

                                    if isinstance(line, bytes):
                                        line = line.decode("utf-8", errors="replace")
                                    elif (
                                        isinstance(line, str)
                                        and line.startswith("b'")
                                        and line.endswith("'")
                                    ):
                                        try:
                                            # Safely evaluate as bytes literal, then decode
                                            line = ast.literal_eval(line).decode(
                                                "utf-8", errors="replace"
                                            )
                                        except Exception:
                                            # Fallback: leave as-is if parsing fails
                                            pass
                                    elif not isinstance(line, str):
                                        line = str(line)
                                    # Filter out empty lines and container init noise
                                    if not line.strip():
                                        continue
                                    if (
                                        "container" in line
                                        and "waiting to start" in line
                                        and "PodInitializing" in line
                                    ) or (
                                        "No related containers found in namespace" in line
                                    ):
                                        continue
                                    
                                    # Filter out excluded patterns if specified
                                    if exclude:
                                        should_exclude = False
                                        for pattern in exclude:
                                            if pattern in line:
                                                should_exclude = True
                                                break
                                        if should_exclude:
                                            continue
                                    
                                    click.echo(line)
                                    log_received = True
                                    last_log_time = time.time()
                                except Exception as e:
                                    click.echo(
                                        f"\n⚠️  Error decoding log line: {e}\n[DEBUG] raw line: {repr(line)}\n"
                                    )
                                # Show progress if no logs for a while
                                if (
                                    not log_received
                                    and (time.time() - last_progress) > progress_interval
                                ):
                                    click.echo(
                                        "⏳ Waiting for containers to start... (no logs yet, try --watch for task status)"
                                    )
                                    last_progress = time.time()
                            # After log stream ends, check if any logs were received
                            if not log_received:
                                # Poll run status one last time
                                status = prax_client_wrapper.get_run_status(run_id)
                                overall_status = status.get("status", "").lower()
                                terminal_states = (
                                    "succeeded",
                                    "failed",
                                    "error",
                                    "cancelled",
                                    "completed",
                                    "success",
                                    "finished",
                                )
                                if overall_status in terminal_states:
                                    click.echo(
                                        "⚠️  No logs were received, but the run has completed. Try --watch for task status."
                                    )
                                else:
                                    click.echo(
                                        "⚠️  No logs were received. The job may still be starting. Try --watch for task status."
                                    )
                        except KeyboardInterrupt:
                            click.echo("\n🛑 Log following interrupted by user.\n")
                        except Exception as e:
                            logger.exception(f"Failed to follow logs: {e}")
                            click.echo(f"\n⚠️  Failed to follow logs: {e}\n")

                except Exception as e:
                    logger.exception(f"Failed to follow logs: {e}")
                    click.echo(f"\n⚠️  Failed to follow logs: {e}\n")

            elif watch and result.get("prax_run_id"):
                import time

                from rich.console import Console
                from rich.live import Live
                from rich.table import Table

                click.echo(
                    f"\n👀 Watching tasks for latest run of pipeline {pipeline_name} (matches official client):"
                )
                prax_client_wrapper = PraxClientWrapper(prax_config)
                run_id = result["prax_run_id"]
                console = Console()
                poll_interval = 5  # seconds

                def render_status_table(status_dict):
                    table = Table(title=f"Pipeline Run: {run_id}", show_lines=True)
                    table.add_column("Task", style="cyan", no_wrap=True)
                    table.add_column("Status", style="magenta")
                    table.add_column("Message", style="green")
                    details = status_dict.get("details", {})
                    logical_tasks = []
                    if isinstance(details, dict):
                        for info in details.values():
                            # Only include actual execution steps (Pods)
                            if info.get("type") == "Pod":
                                # Prefer templateName, fallback to cleaned displayName
                                task_name = info.get("templateName") or info.get(
                                    "displayName", ""
                                )
                                # Remove numeric suffixes like (0)
                                if isinstance(task_name, str):
                                    task_name = task_name.replace("(0)", "").strip()
                                status = info.get(
                                    "phase", info.get("status", "unknown")
                                )
                                msg = info.get("message", "")
                                logical_tasks.append((task_name, status, msg))
                    # Sort tasks by name for stable display
                    for task_name, status, msg in sorted(logical_tasks):
                        table.add_row(str(task_name), str(status), str(msg))
                    return table

                with Live(console=console, refresh_per_second=2) as live:
                    while True:
                        status = prax_client_wrapper.get_run_status(run_id)
                        live.update(render_status_table(status))
                        overall_status = status.get("status", "").lower()
                        # Consider run finished if all logical tasks are in a terminal state
                        terminal_states = (
                            "succeeded",
                            "failed",
                            "error",
                            "cancelled",
                            "completed",
                            "success",
                            "finished",
                        )
                        logical_task_phases = [
                            info.get("phase", "").lower()
                            for info in status.get("details", {}).values()
                            if info.get("type") == "Pod"
                        ]
                        if overall_status in terminal_states or (
                            logical_task_phases
                            and all(
                                phase in terminal_states
                                for phase in logical_task_phases
                            )
                        ):
                            break
                        time.sleep(poll_interval)
                click.echo("\n✅ Pipeline run completed. Final task statuses above.")
                click.echo("\n✅ Pipeline run completed. Final task statuses above.")

            elif follow:
                click.echo("⚠️  No Prax run ID returned")

            click.echo(f"📋 Completed stages: {', '.join(result['stages_completed'])}")
            click.echo(f"📋 Grid data be available at: https://ui.datamesh.oceanum.io/datasource/rompy-{model_run.run_id}-grid")
            click.echo(f"📋 Spectra be available at:   https://ui.datamesh.oceanum.io/datasource/rompy-{model_run.run_id}-grid")

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
