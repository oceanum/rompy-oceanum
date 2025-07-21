#!/usr/bin/env python3
"""
Example demonstrating the new rompy-oceanum Prax backend architecture.

This example shows how to use the PraxPipelineBackend to submit rompy models
to Oceanum's Prax platform using the plugin architecture.
"""

import logging
import os
from pathlib import Path

import yaml
from rompy.model import ModelRun

from rompy_oceanum.client import PraxClient
from rompy_oceanum.config import DataMeshConfig, PraxConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model configuration
try:
    swan_config = yaml.safe_load(open("example_swan.yaml"))
except FileNotFoundError:
    logger.warn("example_swan.yaml not found in current directory")
    swan_config = yaml.safe_load(open("examples/example_swan.yaml"))


def example_basic_prax_execution():
    """
    Example 1: Basic Prax pipeline execution with minimal configuration.

    This shows the simplest way to submit a model to Prax using environment
    variables for configuration.
    """
    logger.info("=== Example 1: Basic Prax Pipeline Execution ===")

    # Create ModelRun instance
    model_run = ModelRun(
        config=swan_config["config"], output_dir="./outputs", run_id="example-basic-run"
    )

    # Execute using Prax backend
    # This assumes environment variables are set:
    # - PRAX_TOKEN
    # - PRAX_ORG
    # - PRAX_PROJECT
    # - PRAX_BASE_URL (optional, defaults to https://prax.oceanum.io)

    try:
        result = model_run.pipeline(
            pipeline_backend="prax",
            pipeline_name="swan-from-rompy",
            deploy_pipeline=True,
            wait_for_completion=False,  # Don't wait, just submit
        )

        if result["success"]:
            logger.info(f"✅ Pipeline submitted successfully!")
            logger.info(f"Prax run ID: {result['prax_run_id']}")
            logger.info(
                f"You can monitor the run using: rompy-oceanum status {result['prax_run_id']}"
            )
        else:
            logger.error(f"❌ Pipeline submission failed: {result.get('message')}")

    except Exception as e:
        logger.error(f"Error executing pipeline: {e}")

    return result


def example_explicit_configuration():
    """
    Example 2: Explicit configuration without environment variables.

    This shows how to provide configuration explicitly rather than relying
    on environment variables.
    """
    logger.info("=== Example 2: Explicit Configuration ===")

    # Create explicit Prax configuration
    prax_config = PraxConfig(
        base_url="https://prax.oceanum.io",
        token="your-prax-token-here",
        org="your-org",
        project="your-project",
        stage="dev",
        timeout=3600,
    )

    # Create DataMesh configuration for output registration
    datamesh_config = DataMeshConfig(
        base_url="https://datamesh.oceanum.io",
        token="your-datamesh-token-here",
        dataset_name="swan-example-outputs",
    )

    # Load model configuration
    swan_config = yaml.safe_load(open("example_swan.yaml"))

    # Create ModelRun instance
    model_run = ModelRun(
        config=swan_config, output_dir="./outputs", run_id="example-explicit-config"
    )

    try:
        result = model_run.pipeline(
            pipeline_backend="prax",
            pipeline_name="swan-from-rompy",
            prax_config=prax_config,
            datamesh_config=datamesh_config,
            deploy_pipeline=True,
            wait_for_completion=True,  # Wait for completion
            timeout=7200,  # 2 hours
            download_outputs=True,
            output_dir="./prax_outputs",
        )

        if result["success"]:
            logger.info(f"✅ Pipeline completed successfully!")
            logger.info(
                f"Final status: {result.get('final_status', {}).get('status', 'unknown')}"
            )

            if result.get("downloaded_files"):
                logger.info(f"Downloaded {len(result['downloaded_files'])} files:")
                for file_path in result["downloaded_files"]:
                    logger.info(f"  - {file_path}")

            if result.get("datamesh_result"):
                logger.info(
                    f"DataMesh registration: {result['datamesh_result'].get('status', 'unknown')}"
                )
        else:
            logger.error(f"❌ Pipeline execution failed: {result.get('message')}")

    except Exception as e:
        logger.error(f"Error executing pipeline: {e}")

    return result


def example_monitoring_and_management():
    """
    Example 3: Pipeline monitoring and management using PraxClient directly.

    This shows how to use the PraxClient for lower-level operations like
    monitoring status, retrieving logs, and downloading outputs.
    """
    logger.info("=== Example 3: Pipeline Monitoring and Management ===")

    # Create Prax configuration
    prax_config = PraxConfig.from_env()

    # Create client
    client = PraxClient(prax_config)

    try:
        # Check if pipeline exists
        pipeline_name = "swan-from-rompy"
        if client.check_pipeline_exists(pipeline_name):
            logger.info(f"✅ Pipeline {pipeline_name} exists")
        else:
            logger.warning(f"⚠️  Pipeline {pipeline_name} does not exist")

            # Deploy pipeline from template
            template_path = Path(__file__).parent / "templates" / "swan.yaml"
            if template_path.exists():
                if client.deploy_pipeline(pipeline_name, str(template_path)):
                    logger.info(f"✅ Pipeline {pipeline_name} deployed successfully")
                else:
                    logger.error(f"❌ Failed to deploy pipeline {pipeline_name}")

        # Submit pipeline run
        result = example_basic_prax_execution()

        # Get pipeline status
        status = client.get_run_status(run_id)
        logger.info(f"Pipeline status: {status.get('status', 'unknown')}")

        # Get logs
        logs = client.get_run_logs(run_id, tail=50)
        logger.info(f"Recent logs ({len(logs)} lines):")
        for log_line in logs[-10:]:  # Show last 10 lines
            logger.info(f"  {log_line}")

        # Download outputs if completed
        if status.get("status") == "completed":
            output_dir = Path("./downloaded_outputs")
            downloaded_files = client.download_run_artifacts(run_id, output_dir)
            logger.info(f"Downloaded {len(downloaded_files)} files to {output_dir}")

        # Create result object for higher-level operations
        result = client.create_result(run_id, pipeline_name)

        # Get human-readable status
        logger.info(f"Status summary: {result.summary_status()}")

    except Exception as e:
        logger.error(f"Error in monitoring operations: {e}")


def example_batch_processing():
    """
    Example 4: Batch processing multiple model runs.

    This shows how to submit multiple model runs to Prax and monitor them.
    """
    logger.info("=== Example 4: Batch Processing ===")

    # Create multiple runs with different time periods
    runs = []
    for i in range(3):
        config = swan_config["config"].copy()
        config["period"] = {
            "start": f"2023-01-{i+1:02d}T00:00:00Z",
            "end": f"2023-01-{i+2:02d}T00:00:00Z",
        }

        model_run = ModelRun(
            config=config, output_dir="./batch_outputs", run_id=f"batch-run-{i+1:02d}"
        )
        runs.append(model_run)

    # Submit all runs
    prax_results = []
    for i, model_run in enumerate(runs):
        try:
            logger.info(f"Submitting run {i+1}/{len(runs)}: {model_run.run_id}")

            result = model_run.pipeline(
                pipeline_backend="prax",
                pipeline_name="swan-from-rompy",
                deploy_pipeline=(i == 0),  # Only deploy on first run
                wait_for_completion=False,  # Don't wait, submit all first
            )

            if result["success"]:
                prax_results.append(result)
                logger.info(
                    f"✅ Submitted {model_run.run_id} -> {result['prax_run_id']}"
                )
            else:
                logger.error(
                    f"❌ Failed to submit {model_run.run_id}: {result.get('message')}"
                )

        except Exception as e:
            logger.error(f"Error submitting {model_run.run_id}: {e}")

    # Monitor all runs
    logger.info(f"Monitoring {len(prax_results)} submitted runs...")

    # Create client for monitoring
    prax_config = PraxConfig.from_env()
    client = PraxClient(prax_config)

    # Check status of all runs
    for result in prax_results:
        try:
            status = client.get_run_status(result["prax_run_id"])
            logger.info(
                f"Run {result['run_id']} ({result['prax_run_id']}): {status.get('status', 'unknown')}"
            )
        except Exception as e:
            logger.error(f"Error checking status for {result['prax_run_id']}: {e}")


def example_custom_pipeline_parameters():
    """
    Example 5: Using custom pipeline parameters.

    This shows how to pass custom parameters to the Prax pipeline.
    """
    logger.info("=== Example 5: Custom Pipeline Parameters ===")

    # Create SWAN configuration
    swan_config = {
        "model_type": "swan",
        "grid": {
            "grid_type": "regular",
            "nx": 150,
            "ny": 120,
            "dx": 0.008,
            "dy": 0.008,
            "x0": 115.0,
            "y0": -32.0,
        },
        "physics": {"wind": True, "gen": True, "wcap": True, "quad": True},
        "period": {"start": "2023-01-01T00:00:00Z", "end": "2023-01-02T00:00:00Z"},
    }

    # Create ModelRun instance
    model_run = ModelRun(
        config=swan_config, output_dir="./outputs", run_id="example-custom-params"
    )

    # Custom parameters to pass to the pipeline
    custom_parameters = {
        "enable_debug": True,
        "output_format": "netcdf",
        "compression": "gzip",
        "custom_postprocessing": "spectral_analysis",
        "notification_email": "user@example.com",
    }

    try:
        result = model_run.pipeline(
            pipeline_backend="prax",
            pipeline_name="swan-from-rompy-advanced",
            parameters=custom_parameters,
            deploy_pipeline=True,
            wait_for_completion=True,
            timeout=5400,  # 1.5 hours
            download_outputs=True,
        )

        if result["success"]:
            logger.info(f"✅ Custom pipeline completed successfully!")
            logger.info(f"Custom parameters were: {list(custom_parameters.keys())}")
        else:
            logger.error(f"❌ Custom pipeline failed: {result.get('message')}")

    except Exception as e:
        logger.error(f"Error executing custom pipeline: {e}")


def main():
    """
    Main function to run all examples.

    Set environment variables before running:
    - PRAX_TOKEN: Your Prax authentication token
    - PRAX_ORG: Your Prax organization
    - PRAX_PROJECT: Your Prax project
    - PRAX_BASE_URL: Prax API base URL (optional)
    - DATAMESH_TOKEN: DataMesh token (optional)
    """
    logger.info("Starting rompy-oceanum Prax backend examples")

    # Check if required environment variables are set
    required_vars = ["PRAX_TOKEN", "PRAX_ORG", "PRAX_PROJECT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        logger.error("Please set these variables before running the examples")
        return

    # Run examples
    try:
        # example_basic_prax_execution()
        # example_explicit_configuration()
        example_monitoring_and_management()
        # example_batch_processing()
        # example_custom_pipeline_parameters()

        logger.info("All examples completed!")

    except Exception as e:
        logger.error(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
