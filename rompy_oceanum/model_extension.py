"""
Model extension for rompy-oceanum.

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
from pydantic import BaseModel, ConfigDict, Field, validator

from .prax import PraxClient, PraxResult

# Set up logging
logger = logging.getLogger(__name__)

# Forward reference for type hints
if TYPE_CHECKING:
    from rompy.model import ModelRun

# Import ModelRun for inheritance
from rompy.model import ModelRun


# Define Prax configuration models
class PraxTaskResources(BaseModel):
    """Resources configuration for a Prax task."""

    cpu: int = 2
    memory: str = "1G"


class PraxResources(BaseModel):
    """Resources configuration for Prax pipeline tasks."""

    run: PraxTaskResources = Field(default_factory=PraxTaskResources)

    def get_cpu(self, task_name: str) -> int:
        """Get CPU setting for a specific task."""
        if task_name == "run" and hasattr(self, "run"):
            return self.run.cpu
        return 2  # Default CPU

    def get_memory(self, task_name: str) -> str:
        """Get memory setting for a specific task."""
        if task_name == "run" and hasattr(self, "run"):
            return self.run.memory
        return "1G"  # Default memory


class PraxConfig(BaseModel):
    """Prax pipeline configuration."""

    pipeline_name: str = "swan-from-rompy"
    user: str = ""
    org: str = ""
    datamesh_token: str = os.environ.get("DATAMESH_TOKEN", None)
    project: str = ""
    stage: str = "dev"
    url: str = "https://prax.oceanum.io"
    resources: PraxResources = Field(default_factory=PraxResources)

    # raise if datamesh is None
    @validator("datamesh_token")
    def datamesh_token_is_not_none(cls, v):
        if v is None:
            raise ValueError(
                "datamesh_token not set. Please set in config, or set DATAMESH_TOKEN environment variable"
            )
        return v

    @classmethod
    def from_env(cls, **overrides) -> "PraxConfig":
        """Create a PraxConfig with values from environment variables."""
        return cls(
            user=os.environ.get("PRAX_USER", ""),
            org=os.environ.get("PRAX_ORG", ""),
            project=os.environ.get("PRAX_PROJECT", ""),
            **overrides,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PraxConfig":
        """Create a PraxConfig from a dictionary."""
        if not data:
            return cls.from_env()

        # Convert old-style resources dict to new model format
        if "resources" in data and isinstance(data["resources"], dict):
            resources_dict = data.pop("resources")
            resources = PraxResources()

            if "run" in resources_dict and isinstance(resources_dict["run"], dict):
                run_dict = resources_dict["run"]
                resources.run = PraxTaskResources(**run_dict)

            data["resources"] = resources

        return cls(**data)


# Default Prax configuration for backward compatibility
DEFAULT_PRAX_CONFIG = PraxConfig().dict()

# Path to the pipeline templates directory
PIPELINE_TEMPLATES_DIR = pathlib.Path(__file__).parent / "pipeline_templates"


class DataMeshConfig(BaseModel):
    """Configuration for DataMesh registration."""

    enabled: bool = False
    org: str = ""
    tags: list[str] = []
    labels: list[str] = {}

    @classmethod
    def from_env(cls, **overrides) -> "DataMeshConfig":
        """Create a DataMeshConfig with values from environment variables."""
        return cls(org=os.environ.get("DATAMESH_ORGANISATION", ""), **overrides)


class OceanumModelRun(ModelRun):
    """
    Extended version of rompy ModelRun with Oceanum-specific functionality.

    This class adds Prax submission capabilities and DataMesh registration to the base ModelRun class.

    Args:
        prax_config: Configuration for Prax pipeline submission
                    (dict or PraxConfig instance, optional)
        datamesh_config: Configuration for DataMesh registration
                    (dict or DataMeshConfig instance, optional)
    """

    model_config = ConfigDict(
        protected_namespaces=(), extra="allow"
    )  # Temporary fix to allow datamesh fields until spec is updated

    # Prax configuration with default from environment variables
    prax_config: PraxConfig = Field(default_factory=PraxConfig.from_env)

    # DataMesh configuration with default from environment variables
    datamesh_config: DataMeshConfig = Field(default_factory=DataMeshConfig.from_env)

    # Swan pipeline template as a class variable
    _swan_pipeline_template: ClassVar[Optional[Dict[str, Any]]] = None

    # Validator to convert dictionary to PraxConfig
    @validator("prax_config", pre=True)
    def validate_prax_config(cls, value):
        """Convert dict to PraxConfig if needed"""
        if isinstance(value, dict):
            return PraxConfig.from_dict(value)
        return value

    # Validator to convert dictionary to DataMeshConfig
    @validator("datamesh_config", pre=True)
    def validate_datamesh_config(cls, value):
        """Convert dict to DataMeshConfig if needed"""
        if isinstance(value, dict):
            return DataMeshConfig(**value)
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
        # With Pydantic, we can just pass the entire spec including prax
        # The validator will handle converting the prax dict to a PraxConfig object
        return cls(**spec)

    @property
    def swan_pipeline_template(self) -> Dict[str, Any]:
        """
        Get the Swan pipeline template with customized fields based on the current model configuration.

        Returns:
            Customized Swan pipeline template as a dictionary
        """
        # Load the template if it hasn't been loaded yet
        if OceanumModelRun._swan_pipeline_template is None:
            template_path = PIPELINE_TEMPLATES_DIR / "swan.yaml"
            if not template_path.exists():
                raise FileNotFoundError(
                    f"Swan pipeline template not found at {template_path}"
                )

            with open(template_path, "r") as f:
                OceanumModelRun._swan_pipeline_template = yaml.safe_load(f)

        # Create a deep copy to avoid modifying the original template
        template = deepcopy(OceanumModelRun._swan_pipeline_template)

        # Get configuration values
        run_id = self.run_id
        cpu = self.prax_config.resources.run.cpu
        memory = self.prax_config.resources.run.memory

        # Find the run task and update its resources
        for task in template.get("resources", {}).get("tasks", []):
            if task.get("name") == "run":
                task["resources"] = {"cpu": cpu, "memory": memory}

        # Update the pipeline parameters to use the model's run_id
        for pipeline in template.get("resources", {}).get("pipelines", []):
            if pipeline.get("name") == "swan-from-rompy":
                for param in pipeline.get("arguments", {}).get("parameters", []):
                    if param.get("name") == "rompy-config" and "value" in param:
                        # Parse the YAML string value if it's a string
                        config_dict = {}
                        if isinstance(param["value"], str):
                            config_dict = yaml.safe_load(param["value"])
                        else:
                            config_dict = param["value"]
                            
                        # Update the run_id
                        config_dict["run_id"] = run_id
                        
                        # Add the model config if it's not already there
                        if not config_dict.get("config") and hasattr(self, "config"):
                            config_dict["config"] = self.config.model_dump()
                            
                        # Convert back to YAML string
                        param["value"] = yaml.dump(
                            config_dict, default_flow_style=False
                        )

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
        # Use stored config values as defaults
        pipeline_name = pipeline_name or self.prax_config.pipeline_name
        user = user or self.prax_config.user
        org = org or self.prax_config.org
        project = project or self.prax_config.project
        stage = stage or self.prax_config.stage
        prax_url = prax_url or self.prax_config.url

        # Check required parameters
        if not user:
            raise ValueError(
                "User is required. Provide as parameter, set in prax_config, or set PRAX_USER env var."
            )
        if not org:
            raise ValueError(
                "Organization is required. Provide as parameter, set in prax_config, or set PRAX_ORG env var."
            )
        if not project:
            raise ValueError(
                "Project is required. Provide as parameter, set in prax_config, or set PRAX_PROJECT env var."
            )

        # Create Prax client
        client = PraxClient(base_url=prax_url, token=token)

        # Convert model run to Prax parameters
        parameters = self.to_prax_parameters()

        # If we need to deploy the pipeline template first
        if deploy_template and pipeline_name == "swan-from-rompy":
            # Create a temporary file with the customized template
            template_path = pathlib.Path.cwd() / "swan_template_custom.yaml"
            with open(template_path, "w") as f:
                yaml.dump(self.swan_pipeline_template, f)

            logger.info(
                f"Deploying customized Swan pipeline template from {template_path}"
            )
            client.deploy_pipeline(
                template_path=str(template_path),
                user=user,
                org=org,
                project=project,
                stage=stage,
            )
            # Clean up the temporary file
            template_path.unlink()

        # Submit pipeline
        logger.info(f"Submitting {pipeline_name} pipeline to Prax")
        result = client.submit_pipeline(
            pipeline_name=pipeline_name,
            user=user,
            org=org,
            project=project,
            stage=stage,
            parameters=parameters,
        )

        logger.info(f"Pipeline submitted successfully with run ID: {result.run_id}")
        return result

    def to_prax_parameters(self) -> Dict[str, Any]:
        """
        Convert this model run configuration to Prax pipeline parameters.

        Returns:
            Dictionary with Prax pipeline parameters
        """
        # Get the base model attributes first
        # We need to create a copy of the model without the prax_config
        # to avoid JSON serialization issues with Pydantic models
        base_model_dict = {}
        for key, value in self.dump_inputs_dict().items():
            if key != "prax_config":
                base_model_dict[key] = value

        # Serialize the base model attributes to JSON
        try:
            config_json = json.dumps(base_model_dict)
        except TypeError as e:
            # Handle any other serialization errors
            logger.warning(f"Error serializing model config: {e}")
            # Fallback to a minimal config
            config_json = json.dumps({"run_id": self.run_id})

        # Create pipeline parameters
        parameters = {
            "rompy-config": config_json,
            "datamesh-token": self.prax_config.datamesh_token,
        }

        return parameters

    def get_spec(self) -> Dict[str, Any]:
        """
        Get the specification dictionary with Prax-related parameters added.
        Extends the base ModelRun.get_spec() method.

        Returns:
            Dictionary with model specification including Prax fields
        """
        # Get the base specification from parent class
        spec = super().get_spec()

        # Add Prax-specific fields
        spec.update({"prax": self.prax_config.dict()})

        # Add DataMesh-specific fields
        spec.update({"datamesh": self.datamesh_config.dict()})

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
        # Get Prax configuration values
        pipeline_name = self.prax_config.pipeline_name
        user = self.prax_config.user
        org = self.prax_config.org
        project = self.prax_config.project
        stage = self.prax_config.stage
        prax_url = self.prax_config.url
        token = os.environ.get("PRAX_TOKEN")

        # If we're using the built-in Swan template
        if template_path is None:
            # Deploy the template and submit
            return self.submit_to_prax(
                pipeline_name=pipeline_name,
                user=user,
                org=org,
                project=project,
                stage=stage,
                prax_url=prax_url,
                token=token,
                deploy_template=True,
            )
        else:
            # Create Prax client
            client = PraxClient(base_url=prax_url, token=token)

            # Deploy the provided template
            client.deploy_pipeline(
                template_path=template_path,
                user=user,
                org=org,
                project=project,
                stage=stage,
            )

            # Submit the pipeline
            return self.submit_to_prax(
                pipeline_name=pipeline_name,
                user=user,
                org=org,
                project=project,
                stage=stage,
                prax_url=prax_url,
                token=token,
            )

    def dump_spec(self, filename: str) -> None:
        """
        Dump the model specification to a JSON file.

        Args:
            filename: Path to the output JSON file
        """
        spec = self.get_spec()
        with open(filename, "w") as f:
            json.dump(spec, f, indent=2)
        logger.info(f"Model specification saved to {filename}")

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
            ValueError: If org is not set
        """
        if data_type not in ["spectra", "grid"]:
            raise ValueError(
                f"Data type must be 'spectra' or 'grid', got '{data_type}'"
            )

        if not self.datamesh_config.enabled:
            raise ValueError("DataMesh registration is not enabled")

        if not self.datamesh_config.org:
            # raise ValueError("Organisation must be set for DataMesh registration")
            self.datamesh_config.org = "oceanum"  # This is a bug, hardcoded for now

        # Generate dataset name in the format <org>-<run_id>-<data_type>
        dataset_name = f"{self.datamesh_config.org}-rompy-{self.run_id}-{data_type}"

        # Import here to avoid circular imports
        from rompy_oceanum.datamesh import DatameshWriter

        # Create DataMesh writer
        writer = DatameshWriter(
            datasource_id=dataset_name,
            name=f"{self.datamesh_config.org} {self.run_id} {data_type}",
            description=f"ROMPY generated {data_type} dataset for run {self.run_id}",
            tags=self.datamesh_config.tags + ["waves", data_type],
            labels=self.datamesh_config.labels,
        )

        filenamedict = {"grid": "swangrid", "spectra": "swanspec"}

        # Path to the output data (this is a simplified version, you may need to adjust)
        data_file = self.output_dir / self.run_id / f"{filenamedict[data_type]}.nc"

        if not data_file.exists():
            raise FileNotFoundError(f"Data file not found: {data_file}")

        # Register with DataMesh
        logger.info(f"Registering {data_type} data with DataMesh as '{dataset_name}'")

        # Call the appropriate DataMesh registration method based on data type
        if data_type == "spectra":
            writer.write_spectra(str(data_file))
        else:  # grid
            writer.write_grid(str(data_file))

        logger.info(
            f"Successfully registered {data_type} data with DataMesh as '{dataset_name}'"
        )
        return dataset_name


# Note about legacy monkey patching
"""
Legacy Note: Previously, this module supported a monkey patching approach
that extended the rompy ModelRun class directly. That approach has been removed
in favor of the cleaner inheritance model. If you have code that relied on
the monkey patching approach, update it to use OceanumModelRun directly.

Example migration:
```python
# Old approach (no longer supported):
# from rompy.model import ModelRun
# from rompy_oceanum.model_extension import add_prax_methods_to_model_run
# add_prax_methods_to_model_run()
# model = ModelRun(...)
# model.submit_to_prax(...)

# New approach:
from rompy_oceanum.model_extension import OceanumModelRun
model = OceanumModelRun(...)
model.submit_to_prax(...)
```
"""


# Legacy standalone functions are removed in favor of class methods
