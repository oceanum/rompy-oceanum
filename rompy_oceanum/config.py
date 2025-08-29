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

# All legacy Prax config classes have been removed. Use oceanum.auth for authentication and configuration.

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
