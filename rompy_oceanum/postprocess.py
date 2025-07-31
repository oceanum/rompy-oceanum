"""
DataMesh postprocessor for rompy-oceanum.

This module provides the DataMeshPostprocessor that implements the rompy postprocess
interface for registering model outputs with Oceanum's DataMesh system.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import DataMeshConfig
from .datamesh import DatameshWriter

logger = logging.getLogger(__name__)


class DataMeshPostprocessor:
    """DataMesh postprocessor for registering model outputs with DataMesh.

    This postprocessor registers model outputs and metadata with Oceanum's
    DataMesh data catalog system for discovery and access.
    """

    def __init__(self, config: Optional[Union[Dict[str, Any], DataMeshConfig]] = None):
        """Initialize the DataMeshPostprocessor.

        Args:
            config: DataMesh configuration (dict or DataMeshConfig instance)
        """
        self.config = config

    def process(
        self,
        model_run,
        datamesh_config: Optional[Union[Dict[str, Any], DataMeshConfig]] = None,
        dataset_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Process model outputs and register with DataMesh.

        Args:
            model_run: The ModelRun instance that was executed
            datamesh_config: DataMesh configuration (dict or DataMeshConfig instance)
            dataset_name: Name for the dataset (defaults to rompy-{model_run.run_id})
            tags: Tags to apply to the dataset
            metadata: Additional metadata to include
            **kwargs: Additional parameters

        Returns:
            Processing results dictionary

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate input parameters
        if not model_run:
            raise ValueError("model_run cannot be None")

        if not hasattr(model_run, "run_id"):
            raise ValueError("model_run must have a run_id attribute")

        # Initialize configuration
        if datamesh_config is None:
            try:
                datamesh_config = DataMeshConfig.from_env()
            except Exception as e:
                raise ValueError(
                    f"Failed to load DataMesh configuration from environment: {e}"
                )
        elif isinstance(datamesh_config, dict):
            datamesh_config = DataMeshConfig.from_dict(datamesh_config)

        # Set defaults
        dataset_name = dataset_name or f"rompy-{model_run.run_id}"
        tags = tags or []
        metadata = metadata or {}

        logger.info(f"Starting DataMesh registration for run_id: {model_run.run_id}")
        logger.info(f"Dataset name: {dataset_name}")

        process_results = {
            "success": False,
            "processor": "datamesh",
            "run_id": model_run.run_id,
            "dataset_name": dataset_name,
            "stages_completed": [],
        }

        try:
            # Get output directory - handle both local and Prax pipeline contexts
            if hasattr(model_run, "output_dir"):
                base_output_dir = Path(model_run.output_dir)
                
                # Check if we're in a Prax pipeline context
                config_dict = getattr(model_run, "config", {})
                if hasattr(config_dict, "dict"):
                    config_dict = config_dict.dict()
                elif hasattr(config_dict, "model_dump"):
                    config_dict = config_dict.model_dump()

                run_id_subdir = config_dict.get("run_id_subdir", False)

                if str(base_output_dir) == "/tmp/rompy" and not run_id_subdir:
                    # Prax pipeline context - files are directly in /tmp/rompy
                    output_dir = base_output_dir
                    logger.info(
                        f"Prax pipeline context detected - looking for files in: {output_dir}"
                    )
                else:
                    # Local context - files are in output_dir/run_id
                    output_dir = base_output_dir / model_run.run_id
            else:
                output_dir = Path.cwd() / "outputs" / model_run.run_id

            logger.info(f"Looking for output files in: {output_dir}")

            if not output_dir.exists():
                error_msg = f"Output directory does not exist: {output_dir}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

            # Look for standard output files
            grid_file = output_dir / "swangrid.nc"
            spectra_file = output_dir / "swanspec.nc"

            # Create DataMesh writer
            writer = DatameshWriter(
                datasource_id=dataset_name,
                name=f"ROMPY Data - {model_run.run_id}",
                description=f"ROMPY model outputs for run {model_run.run_id}",
                tags=tags
            )

            # Register grid data if it exists
            if grid_file.exists():
                logger.info(f"Registering grid data with DataMesh: {grid_file}")
                writer.write_grid(grid_file)
                process_results["stages_completed"].append("register_grid")
                logger.info("Grid data registered successfully")

            # Register spectra data if it exists
            if spectra_file.exists():
                logger.info(f"Registering spectra data with DataMesh: {spectra_file}")
                writer.write_spectra(spectra_file)
                process_results["stages_completed"].append("register_spectra")
                logger.info("Spectra data registered successfully")

            # Processing completed successfully
            process_results["success"] = True
            process_results["message"] = "DataMesh registration completed successfully"

            logger.info(
                f"DataMesh registration completed successfully for run_id: {model_run.run_id}"
            )
            return process_results

        except Exception as e:
            logger.exception(f"Error in DataMesh processing: {e}")
            return {
                **process_results,
                "stage": "processing",
                "message": f"DataMesh processing error: {str(e)}",
                "error": str(e),
            }