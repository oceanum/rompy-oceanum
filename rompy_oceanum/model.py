"""
Model module for rompy-oceanum.

This module provides an extended version of the rompy ModelRun class with
additional methods for submitting to Prax using an inheritance approach.
"""

import json
import logging
import os
import pathlib
from copy import deepcopy
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Dict, List,
                    Optional, Union)

import yaml
from pydantic import BaseModel, Field, validator

from .prax import PraxClient, PraxResult

# Set up logging
logger = logging.getLogger(__name__)


class PraxTaskResources(BaseModel):
    """Resources configuration for a Prax task."""
    cpu: int = Field(2, description="Number of CPU cores")
    memory: str = Field("1G", description="Memory allocation (e.g., '1G')")


class PraxResources(BaseModel):
    """Resources configuration for Prax pipeline tasks."""
    run: PraxTaskResources = Field(default_factory=PraxTaskResources, description="Resources for run task")
    postprocess: PraxTaskResources = Field(default_factory=PraxTaskResources, description="Resources for postprocess task")
    
    def get_cpu(self, task_name: str) -> int:
        """Get CPU setting for a specific task."""
        if hasattr(self, task_name):
            return getattr(self, task_name).cpu
        return 1  # Default is 1 CPU
        
    def get_memory(self, task_name: str) -> str:
        """Get memory setting for a specific task."""
        if hasattr(self, task_name):
            return getattr(self, task_name).memory
        return "512M"  # Default is 512MB


class PraxConfig(BaseModel):
    """Prax pipeline configuration."""
    pipeline_name: str = Field("swan-from-rompy", description="Name of the Prax pipeline")
    user: str = Field("", description="Prax username")
    org: str = Field("", description="Prax organization")
    project: str = Field("", description="Prax project")
    stage: str = Field("dev", description="Deployment stage")
    url: str = Field("https://prax.oceanum.io", description="Prax API URL")
    resources: PraxResources = Field(default_factory=PraxResources, description="Resource configuration")
    
    @classmethod
    def from_env(cls, **overrides) -> "PraxConfig":
        """Create a PraxConfig with values from environment variables."""
        return cls(
            pipeline_name=overrides.get("pipeline_name", os.environ.get("PRAX_PIPELINE", "swan-from-rompy")),
            user=overrides.get("user", os.environ.get("PRAX_USER", "")),
            org=overrides.get("org", os.environ.get("PRAX_ORG", "")),
            project=overrides.get("project", os.environ.get("PRAX_PROJECT", "")),
            stage=overrides.get("stage", os.environ.get("PRAX_STAGE", "dev")),
            url=overrides.get("url", os.environ.get("PRAX_URL", "https://prax.oceanum.io")),
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PraxConfig":
        """Create a PraxConfig from a dictionary."""
        # Make a copy to avoid modifying the input
        data_copy = deepcopy(data)
        
        # Handle resources if present
        if "resources" in data_copy and isinstance(data_copy["resources"], dict):
            resources_data = data_copy["resources"]
            
            # Convert task resources if present
            for task in ["run", "postprocess"]:
                if task in resources_data and isinstance(resources_data[task], dict):
                    resources_data[task] = PraxTaskResources(**resources_data[task])
            
            data_copy["resources"] = PraxResources(**resources_data)
            
        return cls(**data_copy)


# Default Prax configuration for backward compatibility
DEFAULT_PRAX_CONFIG = PraxConfig().dict()


class DataMeshConfig(BaseModel):
    """Configuration for DataMesh registration."""
    enabled: bool = Field(False, description="Whether to enable DataMesh registration")
    org: str = Field("", description="Organization name for dataset naming")
    tags: List[str] = Field(default_factory=list, description="Additional tags to apply to datasets")
    labels: Dict[str, str] = Field(default_factory=dict, description="Labels to apply to datasets")
    
    @classmethod
    def from_env(cls, **overrides) -> "DataMeshConfig":
        """Create a DataMeshConfig with values from environment variables."""
        return cls(
            enabled=overrides.get("enabled", os.environ.get("DATAMESH_ENABLED", "").lower() == "true"),
            org=overrides.get("org", os.environ.get("DATAMESH_ORG", "")),
        )


class RunConfig(BaseModel):
    """Configuration for model execution."""
    executable: str = Field("/usr/local/bin/swan.exe", description="Path to the model executable")
    mpiexec: str = Field("mpirun", description="MPI command for parallel execution")
    image: Optional[str] = Field(None, description="Docker image to use")
    dockerfile: Optional[str] = Field(None, description="Dockerfile to build")
    build_args: Dict[str, str] = Field(default_factory=dict, description="Arguments for Docker builds")
    
    def get_run_command(self, cpu: int) -> str:
        """Create the run command with the specified CPU count."""
        if self.mpiexec:
            return f"{self.mpiexec} -n {cpu} {self.executable}"
        return self.executable
    
    def should_build_image(self) -> bool:
        """Check if a docker image needs to be built."""
        return self.dockerfile is not None and self.image is None


class OceanumModelRun(BaseModel):
    """Extended version of rompy ModelRun with Oceanum-specific functionality.

    This class adds Prax submission capabilities and DataMesh registration to the base ModelRun class.

    Args:
        prax_config: Configuration for Prax pipeline submission
                    (dict or PraxConfig instance, optional)
        datamesh_config: Configuration for DataMesh registration
                    (dict or DataMeshConfig instance, optional)
        run_config: Configuration for model execution
                    (dict or RunConfig instance, optional)
    """
    prax_config: PraxConfig = Field(default_factory=PraxConfig.from_env, description="Prax configuration")
    datamesh_config: DataMeshConfig = Field(default_factory=DataMeshConfig.from_env, description="DataMesh configuration")
    run_config: RunConfig = Field(default_factory=RunConfig, description="Run configuration")
    
    # Class variable to cache the Swan pipeline template
    _swan_pipeline_template: ClassVar[Optional[Dict[str, Any]]] = None
    
    @validator("prax_config", pre=True)
    def validate_prax_config(cls, value):
        """Convert dict to PraxConfig if needed"""
        if isinstance(value, dict):
            return PraxConfig.from_dict(value)
        return value
    
    @validator("datamesh_config", pre=True)
    def validate_datamesh_config(cls, value):
        """Convert dict to DataMeshConfig if needed"""
        if isinstance(value, dict):
            return DataMeshConfig(**value)
        return value
        
    @validator("run_config", pre=True)
    def validate_run_config(cls, value):
        """Convert dict to RunConfig if needed"""
        if isinstance(value, dict):
            return RunConfig(**value)
        return value
    
    @classmethod
    def from_spec(cls, spec: Dict[str, Any]) -> "OceanumModelRun":
        """
        Create a new OceanumModelRun instance from a specification dictionary.
        
        Args:
            spec: Dictionary with model specification including Prax fields
            
        Returns:
            New OceanumModelRun instance
        """
        from rompy import ModelRun  # Import here to avoid circular imports
        
        # Make a copy to avoid modifying the input
        spec_copy = deepcopy(spec)
        
        # Extract Oceanum-specific fields if present
        prax_config = spec_copy.pop("prax_config", {})
        datamesh_config = spec_copy.pop("datamesh_config", {})
        run_config = spec_copy.pop("run_config", {})
        
        # Create base ModelRun instance
        model_run = ModelRun.from_spec(spec_copy)
        
        # Add OceanumModelRun fields
        for key, value in model_run.__dict__.items():
            setattr(cls, key, value)
            
        # Create OceanumModelRun instance
        return cls(**spec)
    
    @property
    def swan_pipeline_template(self) -> Dict[str, Any]:
        """
        Get the Swan pipeline template with customized fields based on the current model configuration.
        
        Returns:
            Customized Swan pipeline template as a dictionary
        """
        if self._swan_pipeline_template is None:
            # Load the template from the package
            template_path = pathlib.Path(__file__).parent / "templates" / "swan_pipeline.json"
            with open(template_path, "r") as f:
                cls._swan_pipeline_template = json.load(f)
                
        # Make a copy to avoid modifying the class variable
        template = deepcopy(self._swan_pipeline_template)
        
        # Customize the template based on the current model run
        # TODO: Implement customization
        
        return template
    
    def submit_to_prax(
            self,
            pipeline_name: str = None,
            user: str = None,
            org: str = None,
            project: str = None,
            stage: str = None,
            prax_url: str = None,
            token: Optional[str] = None,
            deploy_template: bool = False,
        ) -> PraxResult:
        """
        Submit this model run to an Oceanum Prax pipeline.
        
        Args:
            pipeline_name: Name of the pipeline to run (default: from prax_config or "swan-from-rompy")
            user: Username (default: from prax_config or env var PRAX_USER)
            org: Organization name (default: from prax_config or env var PRAX_ORG)
            project: Project name (default: from prax_config or env var PRAX_PROJECT)
            stage: Stage name (default: from prax_config or "dev")
            prax_url: Prax API base URL (default: from prax_config or "https://prax.oceanum.io")
            token: Prax API token (default: from env var PRAX_TOKEN)
            deploy_template: Whether to deploy the pipeline template first (default: False)
            
        Returns:
            PraxResult object with information about the submitted run
        """
        return submit_to_prax(
            self,
            pipeline_name=pipeline_name,
            user=user,
            org=org,
            project=project,
            stage=stage,
            prax_url=prax_url,
            token=token,
            deploy_template=deploy_template,
        )
    
    def to_prax_parameters(self) -> Dict[str, Any]:
        """
        Convert this model run configuration to Prax pipeline parameters.
        
        Returns:
            Dictionary with Prax pipeline parameters
        """
        return to_prax_parameters(self)
    
    def get_spec(self) -> Dict[str, Any]:
        """
        Get the specification dictionary with Prax-related parameters added.
        Extends the base ModelRun.get_spec() method.
        
        Returns:
            Dictionary with model specification including Prax fields
        """
        # Start with the base spec
        from rompy import ModelRun  # Import here to avoid circular imports
        
        # Get base fields spec
        base_spec = {}
        for field_name in ModelRun.__annotations__:
            if hasattr(self, field_name):
                base_spec[field_name] = getattr(self, field_name)
        
        # Add Prax and DataMesh fields
        spec = {
            **base_spec,
            "prax_config": self.prax_config.dict() if self.prax_config else {},
            "datamesh_config": self.datamesh_config.dict() if self.datamesh_config else {},
            "run_config": self.run_config.dict() if self.run_config else {},
        }
        
        return spec
    
    def submit_pipeline_with_template(
            self, template_path: Optional[str] = None
        ) -> PraxResult:
        """
        Submit a pipeline to Prax using a template file, with customized fields.
        
        This method combines deploying a pipeline template with running it in one step.
        If no template path is provided, uses the built-in Swan pipeline template.
        
        Args:
            template_path: Optional path to a custom pipeline template file
                          If None, uses the built-in Swan template
                          
        Returns:
            PraxResult object with information about the submitted run
        """
        # Create a Prax client
        client = PraxClient(
            user=self.prax_config.user,
            org=self.prax_config.org,
            url=self.prax_config.url,
        )
        
        # Load the template
        if template_path:
            with open(template_path, "r") as f:
                if template_path.endswith(".json"):
                    template = json.load(f)
                elif template_path.endswith((".yaml", ".yml")):
                    template = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported template file format: {template_path}")
        else:
            # Use the built-in Swan template
            template = self.swan_pipeline_template
            
        # Customize the template
        # TODO: Implement customization
            
        # Deploy the template
        logger.info(f"Deploying pipeline template: {self.prax_config.pipeline_name}")
        deploy_result = client.deploy_pipeline(
            name=self.prax_config.pipeline_name,
            spec=template,
            project=self.prax_config.project,
            stage=self.prax_config.stage,
        )
        
        if not deploy_result.success:
            logger.error(f"Failed to deploy pipeline template: {deploy_result.message}")
            return deploy_result
            
        # Run the pipeline
        logger.info(f"Running pipeline: {self.prax_config.pipeline_name}")
        parameters = self.to_prax_parameters()
        
        return client.run_pipeline(
            name=self.prax_config.pipeline_name,
            parameters=parameters,
            project=self.prax_config.project,
            stage=self.prax_config.stage,
        )
    
    def dump_spec(self, filename: str):
        """
        Dump the model specification to a JSON file.
        
        Args:
            filename: Path to the output JSON file
        """
        spec = self.get_spec()
        with open(filename, "w") as f:
            json.dump(spec, f, indent=2)
            
    def register_with_datamesh(self, data_type: str) -> str:
        """
        Register output data with DataMesh.
        
        Args:
            data_type: Type of data ('spectra' or 'grid')
            
        Returns:
            The registered dataset name
            
        Raises:
            ValueError: If data_type is not 'spectra' or 'grid'
            ValueError: If datamesh_config is not enabled
            ValueError: If organisation is not set
        """
        if data_type not in ["spectra", "grid"]:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        if not self.datamesh_config.enabled:
            raise ValueError("DataMesh registration is not enabled")
            
        if not self.datamesh_config.org:
            raise ValueError("DataMesh organisation name is not set")
        
        # Import here to avoid circular imports
        from rompy_oceanum.datamesh import register_with_datamesh
        
        # Set up the dataset name pattern: <organisation>-<run_id>-<data_type>
        dataset_name = f"{self.datamesh_config.org}-{self.run_id}-{data_type}"
        
        # Get the output file path based on data type
        if data_type == "spectra":
            file_path = self.output_dir / self.run_id / "swanspec.nc"
        else:  # grid
            file_path = self.output_dir / self.run_id / "swangrid.nc"
            
        if not file_path.exists():
            raise FileNotFoundError(f"Output file not found: {file_path}")
            
        # Register with DataMesh
        logger.info(f"Registering {data_type} data with DataMesh as '{dataset_name}'")
        
        register_with_datamesh(
            file_path=file_path,
            data_type=data_type,
            dataset_name=dataset_name,
            tags=self.datamesh_config.tags,
            labels=self.datamesh_config.labels,
        )
        
        logger.info(f"Successfully registered {data_type} data with DataMesh as '{dataset_name}'")
        return dataset_name

    # Use the base ModelRun.run() method with appropriate backend
    # For Docker execution: model.run(backend="docker", image="oceanum/swan:latest")
            
    # Use the base ModelRun.postprocess() method with the DataMesh processor
    # For DataMesh registration: model.postprocess(processor="datamesh", config={"enabled": True, "org": "oceanum"})


# Note about legacy monkey patching
"""
Legacy Note: Previously, this module supported a monkey patching approach
to extend the ModelRun class. This approach is still supported for backwards
compatibility but is deprecated in favor of the inheritance-based approach
provided by OceanumModelRun.
"""

# Monkey patching of ModelRun class for backward compatibility
def add_prax_methods_to_model_run(model_run_class):
    """Add Prax-related methods to the ModelRun class."""
    old_get_spec = model_run_class.get_spec
    
    def patched_get_spec(self):
        """Get model specification with Prax fields."""
        spec = old_get_spec(self)
        if hasattr(self, "prax_config"):
            spec["prax_config"] = self.prax_config
        return spec
    
    model_run_class.get_spec = patched_get_spec
    model_run_class.submit_to_prax = submit_to_prax
    model_run_class.to_prax_parameters = to_prax_parameters
    
    return model_run_class


# For backward compatibility: monkey patch ModelRun on import
# This is deprecated in favor of using OceanumModelRun directly
try:
    from rompy.model import ModelRun
    add_prax_methods_to_model_run(ModelRun)
except ImportError:
    pass


# Helper functions for Prax submission
def to_prax_parameters(model_run) -> Dict[str, Any]:
    """Convert a model run to Prax parameters."""
    # Basic parameters
    params = {
        "run_id": model_run.run_id,
        "start_time": model_run.period.start.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": model_run.period.end.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # Add any additional parameters specific to the model type
    if hasattr(model_run.config, "to_prax_parameters"):
        params.update(model_run.config.to_prax_parameters())
        
    return params


def submit_to_prax(
        model_run,
        pipeline_name: str = None,
        user: str = None,
        org: str = None,
        project: str = None,
        stage: str = None,
        prax_url: str = None,
        token: Optional[str] = None,
        deploy_template: bool = False,
    ) -> PraxResult:
    """Submit a model run to Prax."""
    # Get configuration from the model or use defaults
    if hasattr(model_run, "prax_config"):
        prax_config = model_run.prax_config
    else:
        # Use default configuration
        prax_config = PraxConfig.from_env()
    
    # Override configuration with explicit parameters
    if pipeline_name:
        prax_config.pipeline_name = pipeline_name
    if user:
        prax_config.user = user
    if org:
        prax_config.org = org
    if project:
        prax_config.project = project
    if stage:
        prax_config.stage = stage
    if prax_url:
        prax_config.url = prax_url
        
    # Create Prax client
    client = PraxClient(
        user=prax_config.user,
        org=prax_config.org,
        url=prax_config.url,
        token=token,
    )
    
    # Deploy template if requested
    if deploy_template:
        try:
            from rompy_oceanum.model import OceanumModelRun
            if isinstance(model_run, OceanumModelRun):
                logger.info(f"Deploying pipeline template: {prax_config.pipeline_name}")
                template = model_run.swan_pipeline_template
                deploy_result = client.deploy_pipeline(
                    name=prax_config.pipeline_name,
                    spec=template,
                    project=prax_config.project,
                    stage=prax_config.stage,
                )
                
                if not deploy_result.success:
                    logger.error(f"Failed to deploy pipeline template: {deploy_result.message}")
                    return deploy_result
            else:
                logger.warning("Model run is not an OceanumModelRun, skipping template deployment")
        except ImportError:
            logger.warning("Could not import OceanumModelRun, skipping template deployment")
    
    # Convert model to parameters
    parameters = to_prax_parameters(model_run)
    
    # Submit the run
    logger.info(f"Submitting pipeline: {prax_config.pipeline_name}")
    return client.run_pipeline(
        name=prax_config.pipeline_name,
        parameters=parameters,
        project=prax_config.project,
        stage=prax_config.stage,
    )
