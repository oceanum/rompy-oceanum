"""
DataMesh postprocessor for registering model outputs with DataMesh.

This module provides a postprocessor implementation for registering model outputs
with the Oceanum DataMesh service.
"""
import logging
import pathlib
from typing import Dict, List, Optional, Any

from rompy.postprocess import Postprocessor
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DataMeshConfig(BaseModel):
    """Configuration for DataMesh registration."""
    enabled: bool = Field(True, description="Whether to enable DataMesh registration")
    org: str = Field("", description="Organization name for dataset naming")
    tags: List[str] = Field(default_factory=list, description="Additional tags to apply to datasets")
    labels: Dict[str, str] = Field(default_factory=dict, description="Labels to apply to datasets")


class DataMeshPostprocessor(Postprocessor):
    """Register model outputs with DataMesh.
    
    This postprocessor finds model output files and registers them with
    the Oceanum DataMesh service using the appropriate dataset naming conventions.
    """
    
    def process(self, 
               model_run, 
               config: Optional[DataMeshConfig] = None,
               **kwargs) -> Dict[str, Any]:
        """Register model outputs with DataMesh.
        
        Args:
            model_run: The ModelRun instance whose outputs to register
            config: DataMesh configuration
            **kwargs: Additional parameters
            
        Returns:
            Dictionary mapping data types to registered dataset names
        """
        # Get or create configuration
        if config is None:
            # Try to get config from model_run if it has one
            if hasattr(model_run, "datamesh_config"):
                config = model_run.datamesh_config
            else:
                # Create default config
                config = DataMeshConfig()
        # Convert dict to DataMeshConfig if needed
        elif isinstance(config, dict):
            config = DataMeshConfig(**config)
                
        # Skip if not enabled
        if not config.enabled:
            logger.warning("DataMesh registration is not enabled. Skipping registration.")
            return {"success": False, "message": "DataMesh registration not enabled"}
            
        # Check required fields
        if not config.org:
            logger.warning("Organisation name is required for DataMesh registration.")
            return {"success": False, "message": "Organisation name not set"}
        
        # Import DataMesh writer (here to avoid circular imports)
        from rompy_oceanum.datamesh import DatameshWriter
        
        registered = {}
        run_id = model_run.run_id
        run_dir = model_run.output_dir / run_id
        
        # Process all available output types
        output_types = self._find_output_types(run_dir)
        
        for data_type, file_path in output_types.items():
            try:
                # Generate dataset name in the format <organisation>-<run_id>-<data_type>
                dataset_name = f"{config.org}-{run_id}-{data_type}"
                
                # Create DataMesh writer
                writer = DatameshWriter(
                    datasource_id=dataset_name,
                    name=f"{config.org} Model {data_type}",
                    description=f"ROMPY generated {data_type} dataset for run {run_id}",
                    tags=["rompy", f"{data_type}", f"{config.org}"] + config.tags
                )
                
                # Register with DataMesh
                logger.info(f"Registering {data_type} data with DataMesh as '{dataset_name}'")
                
                # Call the appropriate DataMesh registration method based on data type
                if data_type == "spectra":
                    writer.write_spectra(str(file_path))
                elif data_type == "grid":
                    writer.write_grid(str(file_path))
                
                registered[data_type] = dataset_name
                logger.info(f"Successfully registered {data_type} data with DataMesh as '{dataset_name}'")
            except Exception as e:
                logger.warning(f"Failed to register {data_type} data: {e}")
        
        return {
            "success": len(registered) > 0,
            "registered": registered,
            "message": f"Registered {len(registered)} datasets" if registered else "No datasets registered"
        }
    
    def _find_output_types(self, run_dir: pathlib.Path) -> Dict[str, pathlib.Path]:
        """Find output files in the run directory.
        
        This method looks for known output file patterns and maps them
        to data types for registration.
        
        Args:
            run_dir: Path to the model run directory
            
        Returns:
            Dictionary mapping data types to file paths
        """
        output_types = {}
        
        # Check for known output files - SWAN outputs
        grid_file = run_dir / "swangrid.nc"
        if grid_file.exists():
            output_types["grid"] = grid_file
            
        spectra_file = run_dir / "swanspec.nc"
        if spectra_file.exists():
            output_types["spectra"] = spectra_file
        
        # Add more file type patterns here as needed
        # ...
        
        return output_types
