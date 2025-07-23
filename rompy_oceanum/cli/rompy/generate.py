"""Generate command for creating backend configuration files."""

import yaml
from pathlib import Path
from typing import Optional

import click
from oceanum.cli.common.models import ContextObject


@click.command()
@click.argument("model", type=click.Choice(["swan", "schism", "ww3"]))
@click.option(
    "--backend-type",
    type=click.Choice(["local", "docker", "prax"]),
    default="docker",
    help="Backend type"
)
@click.option(
    "--output",
    "-o",
    help="Output file path (default: backend_config_{model}_{type}.yaml)"
)
@click.option(
    "--cpu",
    default=4,
    help="CPU cores for Docker backend"
)
@click.option(
    "--memory",
    default="2G",
    help="Memory limit for Docker backend"
)
@click.option(
    "--timeout",
    default=3600,
    help="Execution timeout in seconds"
)
@click.option(
    "--mpi-procs",
    default=2,
    help="Number of MPI processes"
)
@click.pass_obj
def generate_backend_config(
    obj: ContextObject,
    model: str,
    backend_type: str,
    output: Optional[str],
    cpu: int,
    memory: str,
    timeout: int,
    mpi_procs: int
):
    """Generate backend configuration file for a specific model.

    Backend types:
    - docker: For local testing - spawns Docker containers
    - local: For native local execution on host system
    - prax: For use within Prax pipeline containers (local backend inside container)

    Example:
        oceanum rompy generate-backend-config swan --backend-type prax
        oceanum rompy generate-backend-config schism --cpu 8 --memory 4G
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
                    "ROMPY_MODEL": "swan"
                }
            },
            "local": {
                "command": f"mpirun -n {mpi_procs} swan.exe",
                "env_vars": {
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "swan"
                }
            },
            "prax": {
                "command": f"mpirun -n {mpi_procs} /usr/local/bin/swan.exe",
                "working_dir": "/tmp/rompy",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "swan"
                }
            }
        },
        "schism": {
            "docker": {
                "image": "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/schism:latest",
                "executable": "/usr/local/bin/pschism",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "schism"
                }
            },
            "local": {
                "command": f"mpirun -n {mpi_procs} pschism",
                "env_vars": {
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "schism"
                }
            },
            "prax": {
                "command": f"mpirun -n {mpi_procs} /usr/local/bin/pschism",
                "working_dir": "/tmp/rompy",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "schism"
                }
            }
        },
        "ww3": {
            "docker": {
                "image": "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/ww3:latest",
                "executable": "/usr/local/bin/ww3_shel",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "ww3"
                }
            },
            "local": {
                "command": f"mpirun -n {mpi_procs} ww3_shel",
                "env_vars": {
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "ww3"
                }
            },
            "prax": {
                "command": f"mpirun -n {mpi_procs} /usr/local/bin/ww3_shel",
                "working_dir": "/tmp/rompy",
                "env_vars": {
                    "OMPI_ALLOW_RUN_AS_ROOT": "1",
                    "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
                    "OMP_NUM_THREADS": str(min(cpu, 4)),
                    "ROMPY_MODEL": "ww3"
                }
            }
        }
    }

    # Create backend configuration
    if backend_type == "prax":
        config = {"type": "local", "timeout": timeout}  # Prax uses local backend inside container
    else:
        config = {"type": backend_type, "timeout": timeout}

    if backend_type == "docker":
        model_config = model_configs[model]["docker"]
        config.update({
            "image": model_config["image"],
            "cpu": cpu,
            "memory": memory,
            "mpiexec": f"mpirun -n {mpi_procs}",
            "executable": model_config["executable"],
            "user": "root",
            "env_vars": model_config["env_vars"],
            "volumes": [],
            "remove_container": True
        })
    elif backend_type == "prax":
        model_config = model_configs[model]["prax"]
        config.update({
            "command": model_config["command"],
            "shell": True,
            "capture_output": True,
            "working_dir": model_config["working_dir"],
            "env_vars": model_config["env_vars"]
        })
    else:  # local
        model_config = model_configs[model]["local"]
        config.update({
            "command": model_config["command"],
            "shell": True,
            "capture_output": True,
            "env_vars": model_config["env_vars"]
        })

    # Add postprocessor configuration with environment-specific tags
    env_tags = {
        "docker": [model, "oceanum", "rompy-generated", "local-testing"],
        "local": [model, "oceanum", "rompy-generated", "native-local"],
        "prax": [model, "oceanum", "rompy-generated", "prax-pipeline"]
    }

    env_metadata = {
        "docker": {"execution_environment": "local", "purpose": "development"},
        "local": {"execution_environment": "native", "purpose": "local-development"},
        "prax": {"execution_environment": "prax", "purpose": "pipeline"}
    }

    # full_config = {
    #     "backend": config,
    #     "postprocess": {
    #         "processor": "datamesh",
    #         "config": {
    #             "output_patterns": ["*.nc", "*.dat", "*.csv", "*.log"],
    #             "tags": env_tags[backend_type],
    #             "metadata": {
    #                 "model_type": model,
    #                 "backend_type": "local" if backend_type == "prax" else backend_type,
    #                 "generated_by": "rompy-oceanum",
    #                 "framework": "rompy",
    #                 **env_metadata[backend_type]
    #             }
    #         }
    #     }
    # }
    full_config = config

    # Determine output file path
    if not output:
        output = f"backend_config_{model}_{backend_type}.yaml"

    # Write configuration file
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        yaml.dump(full_config, f, default_flow_style=False, indent=2)

    click.echo(f"✅ Backend configuration generated: {output_path}")
    click.echo(f"Model: {model}, Backend: {backend_type}")

    if backend_type == "prax":
        click.echo(f"Usage: rompy pipeline config.yaml --run-backend local --processor datamesh")
        click.echo(f"Note: Prax backend uses local execution within container")
    else:
        click.echo(f"Usage: rompy pipeline config.yaml --run-backend {backend_type} --processor datamesh")

    if backend_type == "docker":
        click.echo(f"Docker image: {model_configs[model]['docker']['image']}")
        click.echo(f"Resources: {cpu} CPU, {memory} memory")
    elif backend_type == "prax":
        click.echo(f"Working directory: {model_configs[model]['prax']['working_dir']}")
        click.echo(f"Command: {model_configs[model]['prax']['command']}")
    else:
        click.echo(f"Command: {model_configs[model]['local']['command']}")
