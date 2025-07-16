#!/usr/bin/env python3
"""
Example script demonstrating how to use the new rompy backend infrastructure
with SWAN model execution through the Prax pipeline system.

This example shows how to:
1. Configure a SWAN model using rompy
2. Execute using different backend configurations:
   - Docker backend: For local testing (spawns containers)
   - Local backend: For native execution on host system
   - Prax backend: For execution within Prax pipeline containers
3. Use the DataMesh postprocessor for output registration

Usage:
    python swan_pipeline_example.py

Environment Variables Required:
    PRAX_TOKEN - Authentication token for Prax
    PRAX_ORG - Organization name
    PRAX_PROJECT - Project name
    DATAMESH_TOKEN - DataMesh authentication token (optional)
"""

import os
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import sys

# Example SWAN configuration
SWAN_CONFIG = {
    "model_type": "swan",
    "run_id": f"swan-example-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    "output_dir": "./outputs",
    "
": {
        "start": "2023-01-01T00:00:00",
        "end": "2023-01-02T00:00:00",
        "interval": "1H",
        "include_end": True
    },
    "config": {
        "grid": {
            "x": [0, 1000, 2000, 3000, 4000, 5000],
            "y": [0, 1000, 2000, 3000, 4000, 5000],
            "dx": 1000,
            "dy": 1000
        },
        "physics": {
            "generation": True,
            "breaking": True,
            "friction": "jonswap",
            "whitecapping": True
        },
        "boundaries": {
            "north": "neumann",
            "south": "neumann",
            "east": "neumann",
            "west": "constant"
        },
        "outputs": [
            {
                "type": "grid",
                "parameters": ["hsig", "tps", "dir"],
                "format": "netcdf",
                "filename": "swangrid.nc"
            },
            {
                "type": "spectra",
                "parameters": ["energy"],
                "format": "netcdf",
                "filename": "swanspec.nc"
            }
        ]
    }
}

# Backend configuration for different execution modes
BACKEND_CONFIGS = {
    "local": {
        "type": "local",
        "timeout": 3600,
        "command": "mpirun -n 2 swan.exe",
        "shell": True,
        "capture_output": True,
        "env_vars": {
            "OMP_NUM_THREADS": "2",
            "ROMPY_MODEL": "swan"
        }
    },
    "docker": {
        "type": "docker",
        "image": "us-central1-docker.pkg.dev/oceanum-prod/oceanum-public/swan:latest",
        "timeout": 3600,
        "cpu": 4,
        "memory": "2G",
        "mpiexec": "mpirun -n 2",
        "executable": "/usr/local/bin/swan.exe",
        "user": "root",
        "env_vars": {
            "OMPI_ALLOW_RUN_AS_ROOT": "1",
            "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
            "OMP_NUM_THREADS": "2",
            "ROMPY_MODEL": "swan"
        },
        "remove_container": True
    },
    "prax": {
        "type": "local",  # Prax uses local backend inside container
        "timeout": 3600,
        "command": "mpirun -n 2 /usr/local/bin/swan.exe",
        "shell": True,
        "capture_output": True,
        "working_dir": "/app",
        "env_vars": {
            "OMPI_ALLOW_RUN_AS_ROOT": "1",
            "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1",
            "OMP_NUM_THREADS": "2",
            "ROMPY_MODEL": "swan"
        }
    }
}


def create_config_file(config_data, filename="swan_config.json"):
    """Create a temporary configuration file."""
    config_path = Path(filename)
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2, default=str)
    return config_path


def create_backend_config_file(backend_config, filename="backend_config.json"):
    """Create a backend configuration file."""
    config_path = Path(filename)
    with open(config_path, 'w') as f:
        json.dump(backend_config, f, indent=2)
    return config_path


def run_rompy_command(command, env_vars=None):
    """Run a rompy CLI command with optional environment variables."""
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    try:
        print(f"Running: {command}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            check=True
        )
        print(f"✅ Command succeeded")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        if e.stdout:
            print(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            print(f"STDERR:\n{e.stderr}")
        raise


def example_generate_only():
    """Example: Generate SWAN input files only."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Generate SWAN input files only")
    print("="*60)

    # Create configuration file
    config_path = create_config_file(SWAN_CONFIG, "swan_generate.json")

    try:
        # Run rompy generate command
        command = f"rompy generate {config_path} --output-dir ./outputs -v"
        run_rompy_command(command)

        print(f"\n✅ SWAN input files generated successfully!")
        print(f"Check the outputs directory for generated files.")

    finally:
        # Cleanup
        if config_path.exists():
            config_path.unlink()


def example_full_pipeline_local():
    """Example: Run full pipeline with native local backend."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Full SWAN pipeline with native local backend")
    print("="*60)
    print("This runs SWAN natively on the host system (no containers)")

    # Create configuration files
    config_path = create_config_file(SWAN_CONFIG, "swan_local.json")
    backend_path = create_backend_config_file(BACKEND_CONFIGS["local"], "backend_local.json")

    try:
        # Run full pipeline
        command = f"rompy pipeline {config_path} --run-backend local --processor noop -v"
        env_vars = {
            "ROMPY_BACKEND_CONFIG": str(backend_path)
        }
        run_rompy_command(command, env_vars)

        print(f"\n✅ SWAN pipeline completed successfully!")

    finally:
        # Cleanup
        for path in [config_path, backend_path]:
            if path.exists():
                path.unlink()


def example_full_pipeline_docker():
    """Example: Run full pipeline with Docker backend."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Full SWAN pipeline with Docker backend")
    print("="*60)
    print("This spawns Docker containers for execution (good for local testing)")

    # Create configuration files
    config_path = create_config_file(SWAN_CONFIG, "swan_docker.json")
    backend_path = create_backend_config_file(BACKEND_CONFIGS["docker"], "backend_docker.json")

    try:
        # Run full pipeline
        command = f"rompy pipeline {config_path} --run-backend docker --processor noop -v"
        env_vars = {
            "ROMPY_BACKEND_CONFIG": str(backend_path)
        }
        run_rompy_command(command, env_vars)

        print(f"\n✅ SWAN pipeline with Docker completed successfully!")

    finally:
        # Cleanup
        for path in [config_path, backend_path]:
            if path.exists():
                path.unlink()


def example_prax_backend_simulation():
    """Example: Simulate Prax backend execution (local backend inside container)."""
    print("\n" + "="*60)
    print("EXAMPLE 4: SWAN pipeline with Prax-style backend")
    print("="*60)
    print("This simulates execution within a Prax pipeline container")
    print("(uses local backend with container paths and environment)")

    # Create configuration files
    config_path = create_config_file(SWAN_CONFIG, "swan_prax.json")
    backend_path = create_backend_config_file(BACKEND_CONFIGS["prax"], "backend_prax.json")

    try:
        # Run pipeline with Prax-style configuration
        command = f"rompy pipeline {config_path} --run-backend local --processor noop -v"
        env_vars = {
            "ROMPY_BACKEND_CONFIG": str(backend_path),
            # Simulate container environment
            "OMPI_ALLOW_RUN_AS_ROOT": "1",
            "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1"
        }
        run_rompy_command(command, env_vars)

        print(f"\n✅ SWAN pipeline with Prax-style backend completed successfully!")

    finally:
        # Cleanup
        for path in [config_path, backend_path]:
            if path.exists():
                path.unlink()


def example_pipeline_with_datamesh():
    """Example: Run pipeline with DataMesh postprocessor."""
    print("\n" + "="*60)
    print("EXAMPLE 5: SWAN pipeline with DataMesh postprocessor")
    print("="*60)

    # Check for required environment variables
    required_env = ["DATAMESH_TOKEN"]
    missing_env = [var for var in required_env if not os.getenv(var)]

    if missing_env:
        print(f"⚠️  Skipping DataMesh example - missing environment variables: {', '.join(missing_env)}")
        return

    # Create configuration files
    config_path = create_config_file(SWAN_CONFIG, "swan_datamesh.json")
    backend_path = create_backend_config_file(BACKEND_CONFIGS["docker"], "backend_datamesh.json")

    try:
        # Run pipeline with DataMesh postprocessor
        command = f"rompy pipeline {config_path} --run-backend docker --processor datamesh -v"
        env_vars = {
            "ROMPY_BACKEND_CONFIG": str(backend_path),
            "DATAMESH_OUTPUT_PATTERNS": "*.nc,*.dat,*.csv",
            "DATAMESH_TAGS": "swan,wave-model,example"
        }
        run_rompy_command(command, env_vars)

        print(f"\n✅ SWAN pipeline with DataMesh completed successfully!")

    finally:
        # Cleanup
        for path in [config_path, backend_path]:
            if path.exists():
                path.unlink()


def example_prax_pipeline():
    """Example: Submit to Prax pipeline system."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Submit SWAN model to Prax pipeline")
    print("="*60)

    # Check for required environment variables
    required_env = ["PRAX_TOKEN", "PRAX_ORG", "PRAX_PROJECT"]
    missing_env = [var for var in required_env if not os.getenv(var)]

    if missing_env:
        print(f"⚠️  Skipping Prax example - missing environment variables: {', '.join(missing_env)}")
        print("Required environment variables:")
        for var in required_env:
            print(f"  - {var}")
        return

    try:
        # Import rompy-oceanum for Prax integration
        from rompy.model import ModelRun

        # Create model run configuration
        model_run = ModelRun(**SWAN_CONFIG)

        print(f"Created ModelRun with ID: {model_run.run_id}")

        # Submit to Prax pipeline
        print("Submitting to Prax pipeline...")
        result = model_run.pipeline(
            pipeline_backend="prax",
            pipeline_name="swan-from-rompy",
            stage="dev"
        )

        if result.get("success"):
            print(f"✅ Pipeline submitted successfully!")
            print(f"Run ID: {result.get('run_id')}")
            if result.get("pipeline_url"):
                print(f"Pipeline URL: {result.get('pipeline_url')}")
        else:
            print(f"❌ Pipeline submission failed: {result.get('message')}")

    except ImportError:
        print("⚠️  rompy-oceanum not installed - cannot run Prax example")
    except Exception as e:
        print(f"❌ Error running Prax example: {e}")


def main():
    """Run all examples."""
    print("ROMPY Backend Configuration Examples")
    print("====================================")
    print()
    print("This script demonstrates different ways to execute SWAN models")
    print("using the new rompy backend infrastructure.")
    print()

    examples = [
        ("Generate Only", example_generate_only),
        ("Native Local Backend", example_full_pipeline_local),
        ("Docker Backend", example_full_pipeline_docker),
        ("Prax-style Backend", example_prax_backend_simulation),
        ("DataMesh Integration", example_pipeline_with_datamesh),
        ("Prax Pipeline", example_prax_pipeline),
    ]

    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error in {name} example: {e}")
            print("Continuing with next example...\n")
            continue

    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
    print()
    print("For more information, see:")
    print("- ROMPY documentation: https://rompy.readthedocs.io/")
    print("- Backend configuration guide: docs/backends.rst")
    print("- Pipeline templates: rompy_oceanum/pipeline_templates/")


if __name__ == "__main__":
    main()
