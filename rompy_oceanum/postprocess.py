"""
DataMesh postprocessor for rompy-oceanum.

This module provides the DataMeshPostprocessor that implements the rompy postprocess
interface for registering model outputs with Oceanum's DataMesh system.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import requests
from datetime import datetime

from .config import DataMeshConfig

logger = logging.getLogger(__name__)


class DataMeshPostprocessor:
    """DataMesh postprocessor for registering model outputs with DataMesh.

    This postprocessor registers model outputs and metadata with Oceanum's
    DataMesh data catalog system for discovery and access.
    """

    def process(self, model_run,
                datamesh_config: Optional[Union[Dict[str, Any], DataMeshConfig]] = None,
                dataset_name: Optional[str] = None,
                tags: Optional[List[str]] = None,
                metadata: Optional[Dict[str, Any]] = None,
                output_patterns: Optional[List[str]] = None,
                **kwargs) -> Dict[str, Any]:
        """Process model outputs and register with DataMesh.

        Args:
            model_run: The ModelRun instance that was executed
            datamesh_config: DataMesh configuration (dict or DataMeshConfig instance)
            dataset_name: Name for the dataset (defaults to run_id)
            tags: Tags to apply to the dataset
            metadata: Additional metadata to include
            output_patterns: File patterns to include (e.g., ['*.nc', '*.csv'])
            **kwargs: Additional parameters

        Returns:
            Processing results dictionary

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Validate input parameters
        if not model_run:
            raise ValueError("model_run cannot be None")

        if not hasattr(model_run, 'run_id'):
            raise ValueError("model_run must have a run_id attribute")

        # Initialize configuration
        if datamesh_config is None:
            try:
                datamesh_config = DataMeshConfig.from_env()
            except Exception as e:
                raise ValueError(f"Failed to load DataMesh configuration from environment: {e}")
        elif isinstance(datamesh_config, dict):
            datamesh_config = DataMeshConfig.from_dict(datamesh_config)

        # Set defaults
        dataset_name = dataset_name or f"rompy-{model_run.run_id}"
        tags = tags or []
        metadata = metadata or {}
        output_patterns = output_patterns or ["*.nc", "*.csv", "*.json"]

        logger.info(f"Starting DataMesh registration for run_id: {model_run.run_id}")
        logger.info(f"Dataset name: {dataset_name}")

        process_results = {
            "success": False,
            "processor": "datamesh",
            "run_id": model_run.run_id,
            "dataset_name": dataset_name,
            "stages_completed": []
        }

        try:
            # Stage 1: Discover output files
            logger.info("Discovering output files")

            output_files = self._discover_output_files(model_run, output_patterns)
            process_results["output_files"] = [str(f) for f in output_files]
            process_results["stages_completed"].append("discover")

            # Note: _discover_output_files now raises exceptions for missing files
            # so we don't need to handle empty results here

            logger.info(f"Found {len(output_files)} output files")

            # Stage 2: Extract metadata
            logger.info("Extracting metadata from outputs")

            extracted_metadata = self._extract_metadata(model_run, output_files)
            combined_metadata = {**extracted_metadata, **metadata}
            process_results["metadata"] = combined_metadata
            process_results["stages_completed"].append("extract_metadata")

            # Stage 3: Register with DataMesh
            logger.info("Registering dataset with DataMesh")

            registration_result = self._register_dataset(
                datamesh_config, dataset_name, output_files,
                combined_metadata, tags
            )
            process_results["registration_result"] = registration_result
            process_results["stages_completed"].append("register")

            # Stage 4: Upload files (if configured)
            if registration_result.get("upload_urls"):
                logger.info("Uploading files to DataMesh")

                upload_results = self._upload_files(
                    output_files, registration_result["upload_urls"]
                )
                process_results["upload_results"] = upload_results
                process_results["stages_completed"].append("upload")

            # Processing completed successfully
            process_results["success"] = True
            process_results["message"] = "DataMesh registration completed successfully"
            process_results["dataset_url"] = registration_result.get("dataset_url")

            logger.info(f"DataMesh registration completed successfully for run_id: {model_run.run_id}")
            return process_results

        except Exception as e:
            logger.exception(f"Error in DataMesh processing: {e}")
            return {
                **process_results,
                "stage": "processing",
                "message": f"DataMesh processing error: {str(e)}",
                "error": str(e)
            }

    def _discover_output_files(self, model_run, patterns: List[str]) -> List[Path]:
        """Discover output files matching the specified patterns.

        Args:
            model_run: ModelRun instance
            patterns: List of file patterns to match

        Returns:
            List of discovered file paths
        """
        output_files = []

        # Get output directory - handle both local and Prax pipeline contexts
        if hasattr(model_run, 'output_dir'):
            base_output_dir = Path(model_run.output_dir)

            # Check if we're in a Prax pipeline context (output_dir is /app)
            # and run_id_subdir is False
            config_dict = getattr(model_run, 'config', {})
            if hasattr(config_dict, 'dict'):
                config_dict = config_dict.dict()
            elif hasattr(config_dict, 'model_dump'):
                config_dict = config_dict.model_dump()

            run_id_subdir = config_dict.get('run_id_subdir', True)

            if str(base_output_dir) == '/app' and not run_id_subdir:
                # Prax pipeline context - files are directly in /app
                output_dir = base_output_dir
                logger.info(f"Prax pipeline context detected - looking for files in: {output_dir}")
            else:
                # Local context - files are in output_dir/run_id
                output_dir = base_output_dir / model_run.run_id
        else:
            output_dir = Path.cwd() / "outputs" / model_run.run_id

        logger.info(f"Searching for output files in: {output_dir}")

        if not output_dir.exists():
            error_msg = f"Output directory does not exist: {output_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Search for files matching patterns
        for pattern in patterns:
            try:
                matching_files = list(output_dir.glob(f"**/{pattern}"))
                output_files.extend(matching_files)
                logger.info(f"Pattern '{pattern}' matched {len(matching_files)} files")
                for f in matching_files:
                    logger.info(f"  Found: {f}")
            except Exception as e:
                error_msg = f"Error searching for pattern '{pattern}': {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

        # Remove duplicates and sort
        output_files = sorted(list(set(output_files)))

        if not output_files:
            error_msg = f"No output files found matching patterns {patterns} in {output_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.info(f"Found {len(output_files)} total output files")
        return output_files

    def _extract_metadata(self, model_run, output_files: List[Path]) -> Dict[str, Any]:
        """Extract metadata from model run and output files.

        Args:
            model_run: ModelRun instance
            output_files: List of output file paths

        Returns:
            Dictionary of extracted metadata
        """
        metadata = {
            "run_id": model_run.run_id,
            "processing_time": datetime.utcnow().isoformat(),
            "processor": "rompy-oceanum",
            "file_count": len(output_files),
            "total_size_bytes": sum(f.stat().st_size for f in output_files if f.exists())
        }

        # Add model-specific metadata
        if hasattr(model_run, 'config'):
            metadata["model_type"] = getattr(model_run.config, 'model_type', 'unknown')

        if hasattr(model_run, 'period'):
            metadata["start_time"] = str(model_run.period.start)
            metadata["end_time"] = str(model_run.period.end)
            metadata["duration"] = str(model_run.period.end - model_run.period.start)

        # Add file-specific metadata
        file_metadata = []
        for output_file in output_files:
            if output_file.exists():
                file_info = {
                    "name": output_file.name,
                    "path": str(output_file.relative_to(output_file.parent.parent)),
                    "size_bytes": output_file.stat().st_size,
                    "modified": datetime.fromtimestamp(output_file.stat().st_mtime).isoformat(),
                    "extension": output_file.suffix
                }

                # Add format-specific metadata
                if output_file.suffix.lower() == '.nc':
                    file_info["format"] = "netcdf"
                    file_info["type"] = "gridded_data"
                elif output_file.suffix.lower() == '.csv':
                    file_info["format"] = "csv"
                    file_info["type"] = "tabular_data"
                elif output_file.suffix.lower() == '.json':
                    file_info["format"] = "json"
                    file_info["type"] = "structured_data"

                file_metadata.append(file_info)

        metadata["files"] = file_metadata

        return metadata

    def _register_dataset(self, config: DataMeshConfig, dataset_name: str,
                         output_files: List[Path], metadata: Dict[str, Any],
                         tags: List[str]) -> Dict[str, Any]:
        """Register dataset with DataMesh.

        Args:
            config: DataMesh configuration
            dataset_name: Name for the dataset
            output_files: List of output file paths
            metadata: Dataset metadata
            tags: Dataset tags

        Returns:
            Registration result dictionary
        """
        # Prepare registration payload
        payload = {
            "name": dataset_name,
            "description": f"ROMPY model outputs for run {metadata.get('run_id', 'unknown')}",
            "tags": tags,
            "metadata": metadata,
            "files": [
                {
                    "name": f.name,
                    "size": f.stat().st_size if f.exists() else 0,
                    "type": self._get_file_type(f)
                }
                for f in output_files
            ]
        }

        # Make registration request
        url = f"{config.base_url}/api/v1/datasets"
        headers = {
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Dataset registered successfully: {result.get('dataset_id')}")
                return result
            else:
                error_msg = f"Failed to register dataset. Status: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                raise requests.exceptions.RequestException(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error registering dataset: {e}")
            raise

    def _upload_files(self, output_files: List[Path], upload_urls: Dict[str, str]) -> Dict[str, Any]:
        """Upload files to DataMesh storage.

        Args:
            output_files: List of output file paths
            upload_urls: Dictionary mapping file names to upload URLs

        Returns:
            Upload results dictionary
        """
        upload_results = {
            "uploaded": [],
            "failed": [],
            "total": len(output_files)
        }

        for output_file in output_files:
            file_name = output_file.name
            upload_url = upload_urls.get(file_name)

            if not upload_url:
                logger.warning(f"No upload URL provided for file: {file_name}")
                upload_results["failed"].append({
                    "file": file_name,
                    "error": "No upload URL provided"
                })
                continue

            try:
                # Upload file
                with open(output_file, 'rb') as f:
                    response = requests.put(upload_url, data=f, timeout=300)

                if response.status_code in [200, 201]:
                    upload_results["uploaded"].append(file_name)
                    logger.info(f"Successfully uploaded: {file_name}")
                else:
                    error_msg = f"Upload failed with status {response.status_code}"
                    upload_results["failed"].append({
                        "file": file_name,
                        "error": error_msg
                    })
                    logger.error(f"Failed to upload {file_name}: {error_msg}")

            except Exception as e:
                upload_results["failed"].append({
                    "file": file_name,
                    "error": str(e)
                })
                logger.error(f"Error uploading {file_name}: {e}")

        return upload_results

    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type from extension.

        Args:
            file_path: Path to the file

        Returns:
            File type string
        """
        extension = file_path.suffix.lower()

        type_map = {
            '.nc': 'netcdf',
            '.csv': 'csv',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.txt': 'text',
            '.log': 'log'
        }

        return type_map.get(extension, 'unknown')
