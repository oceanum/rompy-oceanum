"""
Configuration models for rompy-oceanum backend implementations.

This module provides Pydantic configuration models for the various backend
components, following rompy's backend configuration patterns.
"""
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PraxTaskResources(BaseModel):
    """Resource requirements for Prax pipeline tasks."""

    cpu: Optional[str] = Field(None, description="CPU resource request (e.g., '1000m', '2')")
    memory: Optional[str] = Field(None, description="Memory resource request (e.g., '2Gi', '4096Mi')")

    @field_validator('cpu')
    @classmethod
    def validate_cpu(cls, v):
        """Validate CPU resource format."""
        if v is None:
            return v
        # Basic validation - should be numeric with optional 'm' suffix
        if not (v.replace('.', '').replace('m', '').isdigit()):
            raise ValueError("CPU must be numeric with optional 'm' suffix (e.g., '1000m', '2')")
        return v

    @field_validator('memory')
    @classmethod
    def validate_memory(cls, v):
        """Validate memory resource format."""
        if v is None:
            return v
        # Basic validation - should end with Gi, Mi, or Ki
        if not any(v.endswith(suffix) for suffix in ['Gi', 'Mi', 'Ki', 'G', 'M', 'K']):
            raise ValueError("Memory must end with Gi, Mi, Ki, G, M, or K (e.g., '2Gi', '4096Mi')")
        return v


class PraxResources(BaseModel):
    """Resource configuration for Prax pipeline execution."""

    requests: Optional[PraxTaskResources] = Field(None, description="Resource requests")
    limits: Optional[PraxTaskResources] = Field(None, description="Resource limits")

    def get_cpu(self) -> Optional[str]:
        """Get CPU resource request."""
        return self.requests.cpu if self.requests else None

    def get_memory(self) -> Optional[str]:
        """Get memory resource request."""
        return self.requests.memory if self.requests else None


class PraxConfig(BaseModel):
    """Configuration for Prax pipeline backend."""

    base_url: str = Field(..., description="Prax API base URL")
    token: str = Field(..., description="Authentication token")
    org: str = Field(..., description="Organization name")
    project: str = Field(..., description="Project name")
    stage: str = Field(default="dev", description="Deployment stage")
    timeout: int = Field(default=3600, ge=60, le=86400, description="Pipeline timeout in seconds")
    resources: Optional[PraxResources] = Field(None, description="Resource configuration")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")

    @classmethod
    def from_env(cls, **overrides) -> 'PraxConfig':
        """Create configuration from environment variables.

        Args:
            **overrides: Additional configuration overrides

        Returns:
            PraxConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        config = {
            "base_url": os.getenv("PRAX_BASE_URL", "https://prax.oceanum.io"),
            "token": os.getenv("PRAX_TOKEN"),
            "org": os.getenv("PRAX_ORG"),
            "project": os.getenv("PRAX_PROJECT"),
            "stage": os.getenv("PRAX_STAGE", "dev"),
            "timeout": int(os.getenv("PRAX_TIMEOUT", "3600")),
        }

        # Remove None values
        config = {k: v for k, v in config.items() if v is not None}

        # Apply overrides
        config.update(overrides)

        # Validate required fields
        required_fields = ["base_url", "token", "org", "project"]
        missing_fields = [field for field in required_fields if field not in config or not config[field]]

        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")

        return cls(**config)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'PraxConfig':
        """Create configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            PraxConfig instance
        """
        return cls(**config_dict)

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip('/')

    @field_validator('token')
    @classmethod
    def validate_token(cls, v):
        """Validate authentication token."""
        if not v or not v.strip():
            raise ValueError("Authentication token cannot be empty")
        return v.strip()

    @field_validator('org', 'project')
    @classmethod
    def validate_identifiers(cls, v):
        """Validate organization and project identifiers."""
        if not v or not v.strip():
            raise ValueError("Organization and project identifiers cannot be empty")
        # Basic validation - alphanumeric and hyphens
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Identifiers must be alphanumeric with optional hyphens and underscores")
        return v.strip()

    @field_validator('stage')
    @classmethod
    def validate_stage(cls, v):
        """Validate deployment stage."""
        valid_stages = ['dev', 'staging', 'prod']
        if v not in valid_stages:
            raise ValueError(f"Stage must be one of: {', '.join(valid_stages)}")
        return v


class DataMeshConfig(BaseModel):
    """Configuration for DataMesh integration."""

    base_url: str = Field(..., description="DataMesh API base URL")
    token: str = Field(..., description="Authentication token")
    dataset_name: Optional[str] = Field(None, description="Dataset name for registration")
    tags: List[str] = Field(default_factory=list, description="Dataset tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def from_env(cls, **overrides) -> 'DataMeshConfig':
        """Create configuration from environment variables.

        Args:
            **overrides: Additional configuration overrides

        Returns:
            DataMeshConfig instance
        """
        config = {
            "base_url": os.getenv("DATAMESH_BASE_URL", "https://datamesh.oceanum.io"),
            "token": os.getenv("DATAMESH_TOKEN"),
            "dataset_name": os.getenv("DATAMESH_DATASET_NAME"),
        }

        # Remove None values
        config = {k: v for k, v in config.items() if v is not None}

        # Apply overrides
        config.update(overrides)

        return cls(**config)

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip('/')

    @field_validator('token')
    @classmethod
    def validate_token(cls, v):
        """Validate authentication token."""
        if not v or not v.strip():
            raise ValueError("Authentication token cannot be empty")
        return v.strip()


class RunConfig(BaseModel):
    """Configuration for model execution within Prax pipelines."""

    command: Optional[str] = Field(None, description="Custom run command")
    working_dir: Optional[str] = Field(None, description="Working directory")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    build_image: bool = Field(default=True, description="Whether to build Docker image")
    image_tag: Optional[str] = Field(None, description="Docker image tag")

    def get_run_command(self) -> str:
        """Get the run command, with fallback to default."""
        if self.command:
            return self.command
        return "python -m rompy run"

    def should_build_image(self) -> bool:
        """Check if image should be built."""
        return self.build_image

    @field_validator('working_dir')
    @classmethod
    def validate_working_dir(cls, v):
        """Validate working directory path."""
        if v is None:
            return v
        path = Path(v)
        if not path.is_absolute():
            raise ValueError("Working directory must be an absolute path")
        return str(path)


class PraxPipelineConfig(BaseModel):
    """Complete configuration for Prax pipeline backend execution."""

    prax: PraxConfig = Field(..., description="Prax configuration")
    datamesh: Optional[DataMeshConfig] = Field(None, description="DataMesh configuration")
    run: RunConfig = Field(default_factory=RunConfig, description="Run configuration")
    pipeline_name: str = Field(..., description="Pipeline name to execute")

    @classmethod
    def from_env(cls, pipeline_name: str, **overrides) -> 'PraxPipelineConfig':
        """Create complete configuration from environment variables.

        Args:
            pipeline_name: Name of the pipeline to execute
            **overrides: Additional configuration overrides

        Returns:
            PraxPipelineConfig instance
        """
        config = {
            "prax": PraxConfig.from_env(),
            "pipeline_name": pipeline_name,
        }

        # Add DataMesh config if available
        try:
            config["datamesh"] = DataMeshConfig.from_env()
        except Exception:
            logger.debug("DataMesh configuration not available from environment")

        # Apply overrides
        config.update(overrides)

        return cls(**config)

    @field_validator('pipeline_name')
    @classmethod
    def validate_pipeline_name(cls, v):
        """Validate pipeline name."""
        if not v or not v.strip():
            raise ValueError("Pipeline name cannot be empty")
        return v.strip()
