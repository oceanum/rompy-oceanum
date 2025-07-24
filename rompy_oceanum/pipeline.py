"""
Prax pipeline backend for rompy-oceanum.

This module provides the PraxPipelineBackend that implements the rompy pipeline
interface for executing models on Oceanum's Prax platform.
"""

import json
import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import yaml

from .client import PraxClient, PraxResult
from .config import DataMeshConfig, PraxConfig, PraxPipelineConfig

if TYPE_CHECKING:
    from .config import PraxPipelineResources

logger = logging.getLogger(__name__)


class PraxPipelineBackend:
    def run(self, model, config, workspace_dir):
        """
        Run the Prax pipeline backend via the standard ROMPY interface.
        """
        # Get model configuration dictionary for template detection
        model_config = {}

        # Try different ways to get model configuration
        if hasattr(model, "model_dump"):
            model_config = model.model_dump()
        elif hasattr(model, "dict"):
            model_config = model.dict()
        elif hasattr(model, "__dict__"):
            model_config = model.__dict__.copy()

        # Also check if model has a config attribute
        if hasattr(model, "config") and model.config:
            if hasattr(model.config, "model_dump"):
                model_config["config"] = model.config.model_dump()
            elif hasattr(model.config, "dict"):
                model_config["config"] = model.config.dict()
            elif hasattr(model.config, "__dict__"):
                model_config["config"] = model.config.__dict__

        # Add class information for type detection
        model_config["_class_name"] = model.__class__.__name__
        model_config["_class_module"] = model.__class__.__module__

        logger.debug(f"Extracted model config: {list(model_config.keys())}")

        # Use new smart deployment approach
        return self.execute_with_smart_deployment(
            model_run=model,
            backend_config=config,
            model_config=model_config,
            workspace_dir=workspace_dir,
        )

    def execute_with_smart_deployment(
        self,
        model_run,
        backend_config,
        model_config: Dict[str, Any],
        workspace_dir: Optional[str] = None,
        wait_for_completion: bool = True,
        download_outputs: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute model with smart pipeline deployment logic.

        This method implements the new deployment strategy:
        1. Detect model type
        2. Resolve template path
        3. Generate pipeline name based on hash
        4. Check if pipeline exists, deploy/redeploy as needed
        5. Execute pipeline

        Args:
            model_run: The ModelRun instance to execute
            backend_config: PraxBackendConfig instance
            model_config: Model configuration dictionary
            workspace_dir: Workspace directory path
            wait_for_completion: Whether to wait for completion
            download_outputs: Whether to download outputs
            **kwargs: Additional parameters

        Returns:
            Pipeline execution results
        """
        logger.info(
            f"Starting smart Prax pipeline execution for run_id: {model_run.run_id}"
        )

        # Initialize results tracking
        pipeline_results = {
            "success": False,
            "backend": "prax",
            "run_id": model_run.run_id,
            "stages_completed": [],
            "deployment_info": {},
        }

        try:
            # Stage 1: Model type detection and template resolution
            logger.info("Detecting model type and resolving pipeline template")

            model_type = backend_config.detect_model_type_from_config(model_config)
            template_path = backend_config.resolve_pipeline_template(model_type)

            logger.info(f"Detected model type: {model_type}")
            logger.info(f"Using template: {template_path}")

            pipeline_results["deployment_info"].update(
                {
                    "model_type": model_type,
                    "template_path": str(template_path),
                }
            )

            # Stage 2: Pipeline name generation and deployment check
            logger.info("Generating pipeline name and checking deployment status")

            # Try to get pipeline name from template first
            template_pipeline_name = self._get_pipeline_name_from_template(template_path)
            if template_pipeline_name:
                logger.info(f"Using pipeline name from template: {template_pipeline_name}")
                pipeline_name = template_pipeline_name
            else:
                # Fallback to generated name
                pipeline_name = backend_config.generate_pipeline_name(
                    model_type, template_path
                )
                logger.info(f"Generated pipeline name: {pipeline_name}")
            
            hash_info = backend_config.get_deployment_hash_info()

            logger.info(f"Generated pipeline name: {pipeline_name}")
            logger.debug(f"Deployment hash info: {hash_info}")

            pipeline_results["deployment_info"].update(
                {
                    "pipeline_name": pipeline_name,
                    "hash_info": hash_info,
                }
            )

            # Create Prax client
            prax_config = self._create_prax_config(backend_config)
            client = PraxClient(prax_config)

            # Stage 3: Smart deployment logic
            deployment_needed = False

            if backend_config.auto_deploy:
                logger.info("Checking if pipeline deployment is needed")

                # Check if pipeline already exists
                if client.check_pipeline_exists(pipeline_name):
                    logger.info(f"Pipeline {pipeline_name} already exists")
                    pipeline_results["deployment_info"]["deployment_status"] = "exists"
                else:
                    logger.info(f"Pipeline {pipeline_name} does not exist, will deploy")
                    deployment_needed = True
                    pipeline_results["deployment_info"]["deployment_status"] = "needed"

                # Deploy if needed
                if deployment_needed:
                    logger.info(f"Deploying pipeline from template: {template_path}")

                    # Apply resource overrides to template if specified
                    modified_template = self._apply_resource_overrides(
                        template_path, backend_config.resources
                    )

                    if not client.deploy_pipeline(pipeline_name, modified_template):
                        return {
                            **pipeline_results,
                            "stage": "deploy",
                            "message": f"Failed to deploy pipeline {pipeline_name}",
                        }

                    logger.info(f"Successfully deployed pipeline: {pipeline_name}")
                    pipeline_results["stages_completed"].append("deploy")
                    pipeline_results["deployment_info"][
                        "deployment_status"
                    ] = "deployed"
            else:
                logger.info("Auto-deployment disabled, assuming pipeline exists")
                pipeline_results["deployment_info"]["deployment_status"] = "skipped"

            # Stage 4: Execute the existing pipeline logic
            logger.info(f"Executing pipeline: {pipeline_name}")

            execution_result = self.execute(
                model_run=model_run,
                pipeline_name=pipeline_name,
                prax_config=prax_config,
                deploy_pipeline=False,  # Already handled above
                wait_for_completion=wait_for_completion,
                download_outputs=download_outputs,
                output_dir=workspace_dir,
                **kwargs,
            )

            # Merge results
            pipeline_results.update(execution_result)
            pipeline_results["deployment_info"] = {
                **pipeline_results.get("deployment_info", {}),
                **execution_result.get("deployment_info", {}),
            }

            return pipeline_results

        except Exception as e:
            logger.exception(f"Error in smart pipeline deployment: {e}")
            return {
                **pipeline_results,
                "stage": "smart_deployment",
                "message": f"Smart deployment error: {str(e)}",
                "error": str(e),
            }

    def _create_prax_config(self, backend_config) -> PraxConfig:
        """Create PraxConfig from backend configuration.

        Args:
            backend_config: PraxBackendConfig instance

        Returns:
            PraxConfig instance
        """
        return PraxConfig(
            base_url=backend_config.base_url,
            token=backend_config.token,
            org=backend_config.org,
            project=backend_config.project,
            stage=backend_config.stage,
            timeout=backend_config.timeout,
            environment=backend_config.env_vars,
        )

    def _apply_resource_overrides(
        self, template_path: Path, resource_overrides: Optional["PraxPipelineResources"]
    ) -> str:
        """Apply resource overrides to pipeline template.

        Args:
            template_path: Path to the original template
            resource_overrides: Resource override configuration

        Returns:
            Path to modified template (or original if no overrides)
        """
        if not resource_overrides:
            return str(template_path)

        logger.info("Applying resource overrides to template")

        try:
            # Load template
            with open(template_path, "r") as f:
                template_data = yaml.safe_load(f)

            # Apply resource overrides
            resource_dict = resource_overrides.get_resource_dict()

            if "resources" in template_data and "tasks" in template_data["resources"]:
                for task in template_data["resources"]["tasks"]:
                    task_name = task.get("name")
                    if task_name in resource_dict:
                        task_resources = resource_dict[task_name]
                        if "resources" not in task:
                            task["resources"] = {}
                        task["resources"].update(task_resources)
                        logger.info(
                            f"Applied resource overrides to task '{task_name}': {task_resources}"
                        )

            # Write modified template to temporary file
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f:
                yaml.dump(template_data, f, default_flow_style=False)
                return f.name

        except Exception as e:
            logger.warning(f"Failed to apply resource overrides: {e}")
            return str(template_path)

    """Prax pipeline backend that executes models on Oceanum's Prax platform.

    This backend submits rompy model configurations to Prax pipelines for remote
    execution, providing monitoring and result retrieval capabilities.
    """

    def execute(
        self,
        model_run,
        pipeline_name: str,
        prax_config: Optional[Union[Dict[str, Any], PraxConfig]] = None,
        datamesh_config: Optional[Union[Dict[str, Any], DataMeshConfig]] = None,
        template_path: Optional[str] = None,
        deploy_pipeline: bool = True,
        wait_for_completion: bool = False,
        timeout: int = 3600,
        download_outputs: bool = False,
        output_dir: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
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

        # --- Authentication enforcement ---
        # Check for Prax token (from env or plugin)
        prax_token = None
        import os

        prax_token = os.getenv("PRAX_TOKEN")
        if not prax_token:
            # Try to load from PraxAuthBackend (if available)
            try:
                from rompy_oceanum.auth import PraxToken

                # This assumes PraxToken has a static method to load the token
                prax_token_obj = (
                    PraxToken.load() if hasattr(PraxToken, "load") else None
                )
                if prax_token_obj and hasattr(prax_token_obj, "access_token"):
                    prax_token = prax_token_obj.access_token
            except Exception:
                pass
        if not prax_token:
            raise ValueError(
                "No Prax authentication token found. Please run 'rompy prax-auth login' to authenticate."
            )
        # --- End authentication enforcement ---

        # Initialize configuration
        if prax_config is None:
            try:
                prax_config = PraxConfig.from_env(token=prax_token)
            except Exception as e:
                raise ValueError(
                    f"Failed to load Prax configuration from environment: {e}"
                )
        elif isinstance(prax_config, dict):
            prax_config = PraxConfig.from_dict({**prax_config, "token": prax_token})

        # Initialize DataMesh configuration if provided
        if datamesh_config is not None and isinstance(datamesh_config, dict):
            datamesh_config = DataMeshConfig.from_dict(datamesh_config)

        # Initialize parameters
        pipeline_parameters = parameters or {}

        logger.info(f"Starting Prax pipeline execution for run_id: {model_run.run_id}")
        logger.info(
            f"Pipeline: {pipeline_name}, Org: {prax_config.org}, Project: {prax_config.project}"
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
            client = PraxClient(prax_config)

            # Stage 1: Deploy pipeline if needed
            if deploy_pipeline and template_path:
                logger.info(
                    f"Deploying pipeline {pipeline_name} from template: {template_path}"
                )

                template_file = Path(template_path)
                if not template_file.exists():
                    # Try to find template in package
                    package_template = (
                        Path(__file__).parent
                        / "pipeline_templates"
                        / f"{pipeline_name}.yaml"
                    )
                    if package_template.exists():
                        template_path = str(package_template)
                    else:
                        return {
                            **pipeline_results,
                            "stage": "deploy",
                            "message": f"Template file not found: {template_path}",
                        }

                if not client.deploy_pipeline(pipeline_name, template_path):
                    return {
                        **pipeline_results,
                        "stage": "deploy",
                        "message": f"Failed to deploy pipeline {pipeline_name}",
                    }

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
                prax_run_id = client.submit_pipeline(pipeline_name, prax_parameters)
                pipeline_results["prax_run_id"] = prax_run_id
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

            # Create result object for tracking
            result = client.create_result(prax_run_id, pipeline_name)
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
                    downloaded_files = result.download_outputs(output_dir)
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
                        model_run, result, datamesh_config, output_dir
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
        rompy_config["output_dir"] = "/app"
        rompy_config["run_id_subdir"] = False

        # except Exception as e:
        #     logger.warning(f"Failed to serialize model config: {e}")
        #     rompy_config["config"] = {}

        # Note: datamesh_config is handled separately as a pipeline parameter,
        # not embedded in the ModelRun configuration to avoid validation errors

        # Convert rompy_config to JSON string
        import json

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
        result: PraxResult,
        datamesh_config: DataMeshConfig,
        output_dir: Optional[str],
    ) -> Dict[str, Any]:
        """Register pipeline results with DataMesh.

        Args:
            model_run: ModelRun instance
            result: PraxResult instance
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

    def _get_pipeline_name_from_template(self, template_path: str) -> Optional[str]:
        """Extract the actual pipeline name from the template file.
        
        Args:
            template_path: Path to the pipeline template
            
        Returns:
            Pipeline name from template, or None if not found
        """
        try:
            import yaml
            with open(template_path, 'r') as f:
                template_data = yaml.safe_load(f)
            
            # Look for pipelines section and extract first pipeline name
            if 'resources' in template_data and 'pipelines' in template_data['resources']:
                pipelines = template_data['resources']['pipelines']
                if pipelines and len(pipelines) > 0:
                    return pipelines[0].get('name')
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract pipeline name from template {template_path}: {e}")
            return None
