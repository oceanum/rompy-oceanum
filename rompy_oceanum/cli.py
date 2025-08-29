# -*- coding: utf-8 -*-

import json
import logging
import os
from importlib.metadata import entry_points
from pathlib import Path

import click
import rompy
import yaml

from .config import DataMeshConfig, PraxConfig

logging.basicConfig(level=logging.INFO)

installed = entry_points(group="rompy.config").names


@click.group()
def cli():
    """rompy-oceanum CLI for Prax pipeline integration."""
    pass


@cli.command()
@click.argument("model", type=click.Choice(installed), envvar="ROMPY_MODEL")
@click.argument("config", envvar="ROMPY_CONFIG")
@click.option("--pipeline-name", required=True, help="Name of the Prax pipeline")
@click.option("--org", envvar="PRAX_ORG", help="Prax organization")
@click.option("--project", envvar="PRAX_PROJECT", help="Prax project")
@click.option("--stage", default="dev", envvar="PRAX_STAGE", help="Deployment stage")
@click.option("--template", help="Path to pipeline template file")
@click.option("--deploy/--no-deploy", default=True, help="Deploy pipeline if needed")
@click.option("--wait/--no-wait", default=False, help="Wait for completion")
@click.option("--timeout", default=3600, help="Timeout in seconds")
@click.option("--download/--no-download", default=False, help="Download outputs")
@click.option("--output-dir", help="Output directory for downloads")
@click.option("--zip/--no-zip", default=False, help="Create zip archive")
def run(
    model,
    config,
    pipeline_name,
    org,
    project,
    stage,
    template,
    deploy,
    wait,
    timeout,
    download,
    output_dir,
    zip,
):
    """Run model using Prax pipeline backend.

    Usage: rompy-oceanum run <model> config.yml --pipeline-name my-pipeline

    Args:
        model(str): model type
        config(str): yaml or json config file
        pipeline_name(str): name of the Prax pipeline
    """
    # Load configuration
    try:
        # First try to open it as a file
        with open(config, "r") as f:
            content = f.read()
    except (FileNotFoundError, IsADirectoryError, OSError):
        # If not a file, treat it as raw content
        content = config

    try:
        # Try to parse as yaml
        config_data = yaml.load(content, Loader=yaml.Loader)
        model_run = rompy.model.ModelRun(**config_data)
    except TypeError:
        model_run = rompy.model.ModelRun.model_validate_json(json.loads(content))

    # Create Prax configuration
    prax_config_data = {}
    if org:
        prax_config_data["org"] = org
    if project:
        prax_config_data["project"] = project
    if stage:
        prax_config_data["stage"] = stage

    try:
        prax_config = PraxConfig.from_env(**prax_config_data)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    # Create DataMesh configuration if available
    datamesh_config = None
    try:
        datamesh_config = DataMeshConfig.from_env()
    except Exception:
        pass  # DataMesh is optional

    # Execute pipeline
    click.echo(f"Executing pipeline: {pipeline_name}")
    click.echo(f"Model: {model}, Run ID: {model_run.run_id}")
    click.echo(
        f"Org: {prax_config.org}, Project: {prax_config.project}, Stage: {prax_config.stage}"
    )

    result = model_run.pipeline(
        pipeline_backend="prax",
        pipeline_name=pipeline_name,
        prax_config=prax_config,
        datamesh_config=datamesh_config,
        template_path=template,
        deploy_pipeline=deploy,
        wait_for_completion=wait,
        timeout=timeout,
        download_outputs=download,
        output_dir=output_dir,
    )

    if result["success"]:
        click.echo(f"✅ Pipeline executed successfully!")

        # Check if prax_run_id is available
        if result.get("prax_run_id"):
            click.echo(f"Prax run ID: {result['prax_run_id']}")
        else:
            click.echo("⚠️  No Prax run ID returned (pipeline may be running locally)")

        click.echo(f"Completed stages: {', '.join(result['stages_completed'])}")

        if download and result.get("downloaded_files"):
            click.echo(f"Downloaded {len(result['downloaded_files'])} files")

        if zip:
            # Create zip archive of outputs
            import zipfile

            zip_path = (
                Path(output_dir or f"outputs/{model_run.run_id}")
                / f"{model_run.run_id}.zip"
            )
            zip_path.parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "w") as zf:
                if result.get("downloaded_files"):
                    for file_path in result["downloaded_files"]:
                        zf.write(file_path, Path(file_path).name)

            click.echo(f"Created zip archive: {zip_path}")
    else:
        click.echo(
            f"❌ Pipeline execution failed: {result.get('message', 'Unknown error')}",
            err=True,
        )
        if result.get("error"):
            click.echo(f"Error details: {result['error']}", err=True)
        if result.get("stage"):
            click.echo(f"Failed at stage: {result['stage']}", err=True)


@cli.command()
@click.argument("run_id", required=True)
@click.option("--org", envvar="PRAX_ORG", help="Prax organization")
@click.option("--project", envvar="PRAX_PROJECT", help="Prax project")
@click.option("--tail", default=100, help="Number of log lines to retrieve")
def logs(run_id, org, project, tail):
    """Get logs for a Prax pipeline run."""
    try:
        prax_config = PraxConfig.from_env(org=org, project=project)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    from .client import PraxClient

    client = PraxClient(prax_config)

    try:
        logs_list = client.get_run_logs(run_id, tail=tail)
        click.echo(f"Logs for run {run_id} (last {tail} lines):")
        click.echo("=" * 50)
        for log_line in logs_list:
            click.echo(log_line)
    except Exception as e:
        click.echo(f"Error retrieving logs: {e}", err=True)


@cli.command()
@click.argument("run_id", required=True)
@click.option("--org", envvar="PRAX_ORG", help="Prax organization")
@click.option("--project", envvar="PRAX_PROJECT", help="Prax project")
def status(run_id, org, project):
    """Get status for a Prax pipeline run."""
    try:
        prax_config = PraxConfig.from_env(org=org, project=project)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    from .client import PraxClient

    client = PraxClient(prax_config)

    try:
        status_info = client.get_run_status(run_id)
        click.echo(f"Status for run {run_id}:")
        click.echo("=" * 30)
        click.echo(json.dumps(status_info, indent=2))
    except Exception as e:
        click.echo(f"Error retrieving status: {e}", err=True)


@cli.command()
@click.argument("run_id", required=True)
@click.argument("output_dir", required=True)
@click.option("--org", envvar="PRAX_ORG", help="Prax organization")
@click.option("--project", envvar="PRAX_PROJECT", help="Prax project")
@click.option("--pattern", default="*", help="File pattern to download")
def download(run_id, output_dir, org, project, pattern):
    """Download outputs for a Prax pipeline run."""
    try:
        prax_config = PraxConfig.from_env(org=org, project=project)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    from .client import PraxClient

    client = PraxClient(prax_config)

    try:
        downloaded_files = client.download_run_artifacts(
            run_id, Path(output_dir), pattern
        )
        click.echo(f"Downloaded {len(downloaded_files)} files to {output_dir}:")
        for file_path in downloaded_files:
            click.echo(f"  - {file_path}")
    except Exception as e:
        click.echo(f"Error downloading files: {e}", err=True)


@cli.command()
@click.argument("model", type=click.Choice(["swan", "schism", "ww3"]))
@click.option(
    "--backend-type",
    type=click.Choice(["local", "docker", "prax"]),
    default="docker",
    help="Backend type",
)
@click.option(
    "--output",
    "-o",
    help="Output file path (default: backend_config_{model}_{type}.yaml)",
)
@click.option("--cpu", default=4, help="CPU cores for Docker backend")
@click.option("--memory", default="2G", help="Memory limit for Docker backend")
@click.option("--timeout", default=3600, help="Execution timeout in seconds")
@click.option("--mpi-procs", default=2, help="Number of MPI processes")
def generate_backend_config(
    model, backend_type, output, cpu, memory, timeout, mpi_procs
):
    """Generate backend configuration file for a specific model.

    Backend types:
    - docker: For local testing - spawns Docker containers
    - local: For native local execution on host system
    - prax: For use within Prax pipeline containers (local backend inside container)
    """

    # Define model-specific configurations
    model_configs = {
        "swan": {
            "docker": {
                "image": "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/swan:latest",
                "executable": "/usr/local/bin/swan.exe",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "swan",
                },
            },
            "local": {
                "command": f"mpirun -n {mpi_procs} swan.exe",
                "env_vars": {
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "swan",
                },
            },
            "prax": {
                "command": f"mpirun -n {mpi_procs} /usr/local/bin/swan.exe",
                "working_dir": "/app",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "swan",
                },
            },
        },
        "schism": {
            "docker": {
                "image": "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/schism:latest",
                "executable": "/usr/local/bin/pschism",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "schism",
                },
            },
            "local": {
                "command": f"mpirun -n {mpi_procs} pschism",
                "env_vars": {
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "schism",
                },
            },
            "prax": {
                "command": f"mpirun -n {mpi_procs} /usr/local/bin/pschism",
                "working_dir": "/app",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "schism",
                },
            },
        },
        "ww3": {
            "docker": {
                "image": "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/ww3:latest",
                "executable": "/usr/local/bin/ww3_shel",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "ww3",
                },
            },
            "local": {
                "command": f"mpirun -n {mpi_procs} ww3_shel",
                "env_vars": {"OMP_NUM_THREADS": str(min(cpu, 4)), "ROMPY_MODEL": "ww3"},
            },
            "prax": {
                "command": f"mpirun -n {mpi_procs} /usr/local/bin/ww3_shel",
                "working_dir": "/app",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "ww3",
                },
            },
        },
    }

    # Create backend configuration
    if backend_type == "prax":
        config = {
            "type": "local",
            "timeout": timeout,
        }  # Prax uses local backend inside container
    else:
        config = {"type": backend_type, "timeout": timeout}

    if backend_type == "docker":
        model_config = model_configs[model]["docker"]
        config.update(
            {
                "image": model_config["image"],
                "cpu": cpu,
                "memory": memory,
                "mpiexec": f"mpirun -n {mpi_procs}",
                "executable": model_config["executable"],
                "user": "root",
                "env_vars": model_config["env_vars"],
                "volumes": [],
                "remove_container": True,
            }
        )
    elif backend_type == "prax":
        model_config = model_configs[model]["prax"]
        config.update(
            {
                "command": model_config["command"],
                "shell": True,
                "capture_output": True,
                "working_dir": model_config["working_dir"],
                "env_vars": model_config["env_vars"],
            }
        )
    else:  # local
        model_config = model_configs[model]["local"]
        config.update(
            {
                "command": model_config["command"],
                "shell": True,
                "capture_output": True,
                "env_vars": model_config["env_vars"],
            }
        )

    # Add postprocessor configuration with environment-specific tags
    env_tags = {
        "docker": [model, "oceanum", "rompy-generated", "local-testing"],
        "local": [model, "oceanum", "rompy-generated", "native-local"],
        "prax": [model, "oceanum", "rompy-generated", "prax-pipeline"],
    }

    env_metadata = {
        "docker": {"execution_environment": "local", "purpose": "development"},
        "local": {"execution_environment": "native", "purpose": "local-development"},
        "prax": {"execution_environment": "prax", "purpose": "pipeline"},
    }

    full_config = {
        "backend": config,
        "postprocess": {
            "processor": "datamesh",
            "config": {
                "output_patterns": ["*.nc", "*.dat", "*.csv", "*.log"],
                "tags": env_tags[backend_type],
                "metadata": {
                    "model_type": model,
                    "backend_type": "local" if backend_type == "prax" else backend_type,
                    "generated_by": "rompy-oceanum",
                    "framework": "rompy",
                    **env_metadata[backend_type],
                },
            },
        },
    }

    # Determine output file path
    if not output:
        output = f"backend_config_{model}_{backend_type}.yaml"

    # Write configuration file
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        yaml.dump(full_config, f, default_flow_style=False, indent=2)

    click.echo(f"✅ Backend configuration generated: {output_path}")
    click.echo(f"Model: {model}, Backend: {backend_type}")

    if backend_type == "prax":
        click.echo(
            f"Usage: rompy pipeline config.yaml --run-backend local --processor datamesh"
        )
        click.echo(f"Note: Prax backend uses local execution within container")
    else:
        click.echo(
            f"Usage: rompy pipeline config.yaml --run-backend {backend_type} --processor datamesh"
        )

    if backend_type == "docker":
        click.echo(f"Docker image: {model_configs[model]['docker']['image']}")
        click.echo(f"Resources: {cpu} CPU, {memory} memory")
    elif backend_type == "prax":
        click.echo(f"Working directory: {model_configs[model]['prax']['working_dir']}")
        click.echo(f"Command: {model_configs[model]['prax']['command']}")
    else:
        click.echo(f"Command: {model_configs[model]['local']['command']}")


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
