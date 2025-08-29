"""Prax pipeline backend for rompy-oceanum.

This module provides the PraxPipelineBackend that implements the rompy pipeline
interface for executing models on Oceanum's Prax platform.
"""

import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from .client import PraxClient
from .config import DataMeshConfig
from .prax_client import PraxClientWrapper

logger = logging.getLogger(__name__)


class PraxPipelineBackend:
    """Prax pipeline backend that executes models on Oceanum's Prax platform.

    This backend submits rompy model configurations to Prax pipelines for remote
    execution, providing monitoring and result retrieval capabilities.
    """

    def __init__(self, base_url: str, token: str, org: str, project: str, stage: str = "dev", user: Optional[str] = None):
        """Initialize the PraxPipelineBackend.

        Args:
            base_url: Base URL for Prax API
            token: Authentication token
            org: Organization name
            project: Project name
            stage: Deployment stage (default: "dev")
            user: User email (optional)
        """
        self.base_url = base_url
        self.token = token
        self.org = org
        self.project = project
        self.stage = stage
        self.user = user

    def submit(self, model_run, pipeline_name: str, **kwargs):
        """Submit a model run to a Prax pipeline.

        This is an alias for the execute method for compatibility with rompy's pipeline interface.

        Args:
            model_run: The ModelRun instance to execute
            pipeline_name: Name of the Prax pipeline to execute
            **kwargs: Additional parameters passed to execute method

        Returns:
            Pipeline execution results
        """
        return self.execute(model_run, pipeline_name, **kwargs)

    def get_status(self, result):
        """Get the status of a pipeline run.

        Args:
            result: PraxResult object

        Returns:
            Status dictionary
        """
        return result.get_status()

    def get_logs(self, result, task_name: Optional[str] = None):
        """Get logs from a pipeline run.

        Args:
            result: PraxResult object
            task_name: Optional task name to get logs for specific task

        Returns:
            List of log lines
        """
        return result.get_logs(task_name)

    def download_outputs(self, result, target_dir: str):
        """Download outputs from a pipeline run.

        Args:
            result: PraxResult object
            target_dir: Directory to download outputs to

        Returns:
            List of downloaded file paths
        """
        return result.download_outputs(target_dir)

    def execute(
        self,
        model_run,
        pipeline_name: str,
        datamesh_config: Optional[Union[Dict[str, Any], DataMeshConfig]] = None,
        template_path: Optional[str] = None,
        deploy_pipeline: bool = True,
        wait_for_completion: bool = False,
        timeout: int = 3600,
        download_outputs: bool = False,
        output_dir: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        ctx=None,
        **kwargs,
    ) -> Dict[str, Any]:

        """Execute the model pipeline on Prax.

        Args:
            model_run: The ModelRun instance to execute
            pipeline_name: Name of the Prax pipeline to execute
            prax_config: Prax configuration (dict or PraxConfig instance)
            datamesh_config: DataMesh configuration (dict or DataMeshConfig instance)
            template_path: Path to pipeline template file
            deploy_pipeline: Whether to deploy pipeline if it doesn't exist
            wait_for_completion: Whether to wait for pipeline completion
            timeout: Maximum time to wait for completion (seconds)
            download_outputs: Whether to download outputs after completion
            output_dir: Directory to download outputs to
            parameters: Additional pipeline parameters
            **kwargs: Additional parameters (unused)

        Returns:
            Pipeline execution results

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate input parameters
        if not model_run:
            raise ValueError("model_run cannot be None")

        if not hasattr(model_run, "run_id"):
            raise ValueError("model_run must have a run_id attribute")

        if not pipeline_name or not pipeline_name.strip():
            raise ValueError("pipeline_name cannot be empty")

        # Initialize DataMesh configuration if provided
        if datamesh_config is not None and isinstance(datamesh_config, dict):
            datamesh_config = DataMeshConfig(**datamesh_config)

        # Initialize parameters
        pipeline_parameters = parameters or {}

        logger.info(f"Starting Prax pipeline execution for run_id: {model_run.run_id}")
        logger.info(
            f"Pipeline: {pipeline_name}, Org: {self.org}, Project: {self.project}"
        )

        pipeline_results = {
            "success": False,
            "backend": "prax",
            "run_id": model_run.run_id,
            "pipeline_name": pipeline_name,
            "prax_run_id": None,
            "stages_completed": [],
        }

        try:
            # Create Prax client
            client = PraxClient(
                base_url=self.base_url,
                token=self.token,
                org=self.org,
                project=self.project,
                stage=self.stage,
                user=self.user
            )

            # Stage 1: Deploy pipeline if needed
            if deploy_pipeline and template_path:
                logger.warning(
                    "Pipeline deployment is not handled by this backend. "
                    "Please use 'oceanum prax create pipeline' command for deployment."
                )
                pipeline_results["stages_completed"].append("deploy")

            # Stage 2: Generate model configuration
            logger.info("Generating model configuration for Prax submission")

            try:
                # Generate the model configuration
                # staging_dir = model_run.generate()
                staging_dir = model_run.staging_dir

                # Prepare parameters for Prax pipeline
                prax_params = pipeline_parameters.copy()

                # Add datamesh configuration if provided
                if datamesh_config:
                    prax_params["datamesh_config"] = datamesh_config

                # Convert model configuration to Prax parameters
                prax_parameters = self._convert_model_to_prax_parameters(
                    model_run, staging_dir, prax_params
                )

                pipeline_results["staging_dir"] = (
                    str(staging_dir) if staging_dir else None
                )
                pipeline_results["stages_completed"].append("generate")

            except Exception as e:
                logger.exception(f"Failed to generate model configuration: {e}")
                return {
                    **pipeline_results,
                    "stage": "generate",
                    "message": f"Model configuration generation failed: {str(e)}",
                    "error": str(e),
                }

            # Stage 3: Submit pipeline
            logger.info(f"Submitting pipeline {pipeline_name} to Prax")

            try:
                result = client.submit_pipeline(
                    pipeline_name,
                    parameters=prax_parameters,
                    ctx=ctx,
                )
                prax_run_id = result.run_id
                prax_run_name = (
                    result.run_name if hasattr(result, "run_name") else prax_run_id
                )
                logger.debug(
                    f"Submitted pipeline, got run ID: {prax_run_id}, run name: {prax_run_name}"
                )
                pipeline_results["prax_run_id"] = prax_run_id
                pipeline_results["prax_run_name"] = prax_run_name
                pipeline_results["stages_completed"].append("submit")

                logger.info(
                    f"Pipeline submitted successfully. Prax run ID: {prax_run_id}"
                )

            except Exception as e:
                logger.exception(f"Failed to submit pipeline: {e}")
                return {
                    **pipeline_results,
                    "stage": "submit",
                    "message": f"Pipeline submission failed: {str(e)}",
                    "error": str(e),
                }

            pipeline_results["result"] = result

            # Stage 4: Wait for completion (optional)
            if wait_for_completion:
                logger.info(f"Waiting for pipeline completion (timeout: {timeout}s)")

                try:
                    final_status = result.wait_for_completion(timeout=timeout)
                    pipeline_results["final_status"] = final_status
                    pipeline_results["stages_completed"].append("wait")

                    if final_status.get("status") != "completed":
                        logger.warning(
                            f"Pipeline did not complete successfully: {final_status}"
                        )
                        return {
                            **pipeline_results,
                            "stage": "wait",
                            "message": f"Pipeline execution failed or timed out: {final_status.get('status', 'unknown')}",
                        }

                except Exception as e:
                    logger.exception(f"Error waiting for pipeline completion: {e}")
                    return {
                        **pipeline_results,
                        "stage": "wait",
                        "message": f"Error waiting for completion: {str(e)}",
                        "error": str(e),
                    }

            # Stage 5: Download outputs (optional)
            if download_outputs:
                if not output_dir:
                    output_dir = (
                        Path(model_run.output_dir) / model_run.run_id / "prax_outputs"
                    )

                logger.info(f"Downloading outputs to: {output_dir}")

                try:
                    # Ensure output_dir is a string
                    output_dir_str = str(output_dir)
                    downloaded_files = result.download_outputs(output_dir_str)
                    pipeline_results["downloaded_files"] = [
                        str(f) for f in downloaded_files
                    ]
                    pipeline_results["stages_completed"].append("download")

                    logger.info(f"Downloaded {len(downloaded_files)} files")

                except Exception as e:
                    logger.exception(f"Error downloading outputs: {e}")
                    return {
                        **pipeline_results,
                        "stage": "download",
                        "message": f"Error downloading outputs: {str(e)}",
                        "error": str(e),
                    }

            # Stage 6: DataMesh registration (optional)
            if datamesh_config:
                logger.info("Registering results with DataMesh")

                try:
                    datamesh_result = self._register_with_datamesh(
                        model_run, result.run_id, datamesh_config, output_dir
                    )
                    pipeline_results["datamesh_result"] = datamesh_result
                    pipeline_results["stages_completed"].append("datamesh")

                except Exception as e:
                    logger.exception(f"Error registering with DataMesh: {e}")
                    # Don't fail the entire pipeline for DataMesh registration errors
                    pipeline_results["datamesh_error"] = str(e)

            # Pipeline completed successfully
            pipeline_results["success"] = True
            pipeline_results["message"] = "Pipeline executed successfully"

            logger.info(
                f"Prax pipeline execution completed successfully for run_id: {model_run.run_id}"
            )
            return pipeline_results

        except Exception as e:
            logger.exception(f"Unexpected error in Prax pipeline execution: {e}")
            return {
                **pipeline_results,
                "stage": "pipeline",
                "message": f"Pipeline error: {str(e)}",
                "error": str(e),
            }

    def _convert_model_to_prax_parameters(
        self, model_run, staging_dir: Path, additional_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert model configuration to Prax pipeline parameters.

        Args:
            model_run: ModelRun instance
            staging_dir: Path to generated staging directory
            additional_params: Additional parameters to include

        Returns:
            Dictionary of Prax pipeline parameters in the format expected by the Prax pipeline
        """

        # Create rompy-config parameter containing the full configuration
        rompy_config = model_run.dump_inputs_dict()

        # Ensure output is somewhere where the prax pipelines expects
        rompy_config["output_dir"] = "/tmp/rompy"
        rompy_config["run_id_subdir"] = False

        # Convert rompy_config to JSON string
        parameters = {"rompy-config": json.dumps(rompy_config)}

        # Add DataMesh token if available
        datamesh_token = additional_params.get("datamesh_token")
        if datamesh_token:
            parameters["datamesh-token"] = datamesh_token
        else:
            # Try to get from environment or configuration
            import os

            datamesh_token = os.getenv("DATAMESH_TOKEN")
            if datamesh_token:
                parameters["datamesh-token"] = datamesh_token
            else:
                raise ValueError(
                    "DataMesh token is required- \nPlease set environment variable DATAMESH_TOKEN"
                )
        return parameters

    def _serialize_config(self, obj):
        """Recursively serialize configuration objects to JSON-compatible format.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable object
        """
        import datetime
        from pathlib import Path

        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return obj.total_seconds()
        elif isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: self._serialize_config(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_config(item) for item in obj]
        elif hasattr(obj, "model_dump"):
            return self._serialize_config(obj.model_dump())
        elif hasattr(obj, "dict"):
            return self._serialize_config(obj.dict())
        else:
            return obj

    def _register_with_datamesh(
        self,
        model_run,
        run_id: str,
        datamesh_config: DataMeshConfig,
        output_dir: Optional[str],
    ) -> Dict[str, Any]:
        """Register pipeline results with DataMesh.

        Args:
            model_run: ModelRun instance
            run_id: Pipeline run identifier
            datamesh_config: DataMesh configuration
            output_dir: Output directory path

        Returns:
            DataMesh registration result
        """
        # This is a placeholder implementation
        # In a real implementation, this would interact with the DataMesh API
        logger.info("DataMesh registration not yet implemented")

        return {
            "status": "not_implemented",
            "message": "DataMesh registration is not yet implemented",
            "config": (
                datamesh_config.model_dump()
                if hasattr(datamesh_config, "model_dump")
                else datamesh_config.dict()
            ),
        }

    def get_default_template_path(self, model_type: str) -> Optional[str]:
        """Get the default template path for a model type.

        Args:
            model_type: Type of model (e.g., 'swan', 'schism')

        Returns:
            Path to default template file, or None if not found
        """
        template_dir = Path(__file__).parent / "pipeline_templates"
        template_file = template_dir / f"{model_type}.yaml"

        if template_file.exists():
            return str(template_file)

        # Try with common variations
        for variation in [f"{model_type}-rompy", f"rompy-{model_type}"]:
            template_file = template_dir / f"{variation}.yaml"
            if template_file.exists():
                return str(template_file)

        return None
