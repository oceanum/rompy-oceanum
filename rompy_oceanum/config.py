"""
Configuration models for rompy-oceanum backend implementations.

This module provides Pydantic configuration models for the various backend
components, following rompy's backend configuration patterns.
"""
import os
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator, root_validator
from pathlib import Path
import logging
import yaml

logger = logging.getLogger(__name__)


class PraxTaskResources(BaseModel):
    """Resource specification for a single Prax pipeline task."""
    
    cpu: str = Field("1", description="CPU requirement (e.g., '1', '2', '500m')")
    memory: str = Field("1G", description="Memory requirement (e.g., '1G', '512M', '2Gi')")

    @validator('cpu')
    def validate_cpu(cls, v):
        """Validate CPU resource format."""
        if not v or not str(v).strip():
            raise ValueError("CPU requirement cannot be empty")
        return str(v).strip()

    @validator('memory')
    def validate_memory(cls, v):
        """Validate memory resource format."""
        if not v or not str(v).strip():
            raise ValueError("Memory requirement cannot be empty")
        # Basic validation for common formats
        v_str = str(v).strip()
        if not any(v_str.endswith(suffix) for suffix in ['G', 'M', 'K', 'Gi', 'Mi', 'Ki']):
            if not v_str.isdigit():
                raise ValueError("Memory must end with G, M, K, Gi, Mi, Ki or be a number (bytes)")
        return v_str


class PraxPipelineResources(BaseModel):
    """Resource overrides for Prax pipeline tasks."""
    
    generate: Optional[PraxTaskResources] = Field(None, description="Resources for generate task")
    run: Optional[PraxTaskResources] = Field(None, description="Resources for run task")
    register_task: Optional[PraxTaskResources] = Field(None, description="Resources for register task")

    def get_resource_dict(self) -> Dict[str, Dict[str, str]]:
        """Convert to dictionary format for hashing and comparison."""
        result = {}
        if self.generate:
            result['generate'] = {'cpu': self.generate.cpu, 'memory': self.generate.memory}
        if self.run:
            result['run'] = {'cpu': self.run.cpu, 'memory': self.run.memory}
        if self.register_task:
            result['register'] = {'cpu': self.register_task.cpu, 'memory': self.register_task.memory}
        return result


class PraxResources(BaseModel):
    """Legacy resource configuration for backward compatibility."""

    requests: Optional['PraxTaskResources'] = Field(None, description="Resource requests")
    limits: Optional['PraxTaskResources'] = Field(None, description="Resource limits")

    def get_cpu(self) -> Optional[str]:
        """Get CPU resource request."""
        return self.requests.cpu if self.requests else None

    def get_memory(self) -> Optional[str]:
        """Get memory resource request."""
        return self.requests.memory if self.requests else None


from rompy.backends.config import BaseBackendConfig
class PraxBackendConfig(BaseBackendConfig):
    """ROMPY-compatible backend config for Prax pipeline execution."""
    base_url: str
    token: Optional[str]
    org: str
    project: str
    stage: str = "dev"
    timeout: int = 3600
    env_vars: Dict[str, str] = Field(default_factory=dict)
    working_dir: Optional[Path] = None
    
    # Pipeline deployment configuration
    pipeline_template: Optional[str] = Field(None, description="Path to pipeline template YAML (auto-detected if None)")
    auto_deploy: bool = Field(True, description="Automatically deploy pipeline if not exists")
    redeploy_on_resource_change: bool = Field(True, description="Redeploy if resource requirements change")
    skip_local_generation: bool = Field(True, description="Skip local generation - let pipeline handle it remotely")
    
    # Resource overrides (triggers redeployment if different from template)
    resources: Optional[PraxPipelineResources] = Field(None, description="Resource overrides for pipeline tasks")
    
    # Legacy resources field for backward compatibility
    legacy_resources: Optional[PraxResources] = Field(None, description="Legacy resource configuration")

    def get_backend_class(self):
        # Delayed import to avoid circular import
        from rompy_oceanum.pipeline import PraxPipelineBackend
        return PraxPipelineBackend

    def resolve_pipeline_template(self, model_type: Optional[str] = None) -> Path:
        """Resolve the pipeline template path based on configuration or model type.
        
        Args:
            model_type: The model type to use for template discovery
            
        Returns:
            Path to the resolved template file
            
        Raises:
            ValueError: If template cannot be resolved
        """
        # If explicitly specified, validate and return
        if self.pipeline_template:
            template_path = Path(self.pipeline_template)
            if template_path.exists():
                return template_path
            raise ValueError(f"Specified pipeline template not found: {self.pipeline_template}")
        
        # Auto-detect based on model type
        if not model_type:
            raise ValueError("Model type must be provided for template auto-detection")
            
        try:
            from rompy_oceanum.pipeline_templates import get_template_path
            template_path = get_template_path(model_type)
            if template_path and template_path.exists():
                return template_path
        except ImportError:
            logger.warning("Pipeline templates module not available")
        
        # Fallback: try to find template in same directory
        fallback_path = Path(__file__).parent / "pipeline_templates" / f"{model_type.lower()}.yaml"
        if fallback_path.exists():
            return fallback_path
            
        raise ValueError(f"No pipeline template found for model type: {model_type}")

    def detect_model_type_from_config(self, model_config: Dict[str, Any]) -> Optional[str]:
        """Detect model type from rompy model configuration.
        
        Args:
            model_config: The rompy model configuration dictionary
            
        Returns:
            Detected model type or None if cannot be determined
        """
        logger.debug(f"detect_model_type_from_config called with keys: {list(model_config.keys())}")
        logger.debug(f"_class_name: {model_config.get('_class_name')}")
        logger.debug(f"Top-level model_type: {model_config.get('model_type')}")
        logger.debug(f"config.model_type: {model_config.get('config', {}).get('model_type')}")
        
        # First check config section for model-specific information (most reliable)
        config_section = model_config.get('config', {})
        logger.debug(f"Config section keys: {list(config_section.keys()) if isinstance(config_section, dict) else 'not a dict'}")
        if isinstance(config_section, dict):
            # Check config.model_type field for SwanConfig, etc.
            config_model_type = config_section.get('model_type', '').lower()
            logger.debug(f"config.model_type: {config_model_type}")
            if 'swan' in config_model_type:
                logger.debug("config.model_type contains 'swan', returning 'swan'")
                return 'swan'
            elif 'schism' in config_model_type:
                logger.debug("config.model_type contains 'schism', returning 'schism'")
                return 'schism'
            elif 'ww3' in config_model_type:
                logger.debug("config.model_type contains 'ww3', returning 'ww3'")
                return 'ww3'
                
            # Check for model-specific sections
            for model_type in ['swan', 'schism', 'ww3']:
                if model_type in config_section or model_type.upper() in config_section:
                    logger.debug(f"Found {model_type} in config section, returning '{model_type}'")
                    return model_type
                    
            # Check for model-specific class names in config
            class_name = config_section.get('class', '').lower()
            if 'swan' in class_name:
                logger.debug("config class name contains 'swan', returning 'swan'")
                return 'swan'
            elif 'schism' in class_name:
                logger.debug("config class name contains 'schism', returning 'schism'")
                return 'schism'
            elif 'ww3' in class_name:
                logger.debug("config class name contains 'ww3', returning 'ww3'")
                return 'ww3'
        
        # Check explicit top-level model_type field, but skip if it's just the class name
        if 'model_type' in model_config:
            model_type_value = model_config['model_type'].lower()
            class_name = model_config.get('_class_name', '').lower()
            # Skip if model_type is just the lowercased class name (e.g., "modelrun")
            if model_type_value != class_name:
                detected = model_type_value
                logger.debug(f"Found meaningful top-level model_type, returning: {detected}")
                return detected
            else:
                logger.debug(f"Skipping top-level model_type '{model_type_value}' as it matches class name")

        # Check class name (less reliable as ModelRun is generic)
        if '_class_name' in model_config:
            class_name = model_config['_class_name'].lower()
            logger.debug(f"Checking class name: {class_name}")
            if 'swan' in class_name:
                logger.debug("Class name contains 'swan', returning 'swan'")
                return 'swan'
            elif 'schism' in class_name:
                logger.debug("Class name contains 'schism', returning 'schism'")
                return 'schism'
            elif 'ww3' in class_name:
                logger.debug("Class name contains 'ww3', returning 'ww3'")
                return 'ww3'
            logger.debug(f"Class name '{class_name}' doesn't contain known model types")
        
        # Check for model type in the main config keys (SwanConfigComponents, etc.)
        config_class = model_config.get('class', '').lower()
        if 'swan' in config_class:
            return 'swan'
        elif 'schism' in config_class:
            return 'schism'
        elif 'ww3' in config_class:
            return 'ww3'
        
        # Check environment variables
        if self.env_vars.get('ROMPY_MODEL'):
            return self.env_vars['ROMPY_MODEL'].lower()
            
        # Default to swan for now
        logger.info("Could not detect model type from config, defaulting to 'swan'")
        logger.debug(f"Model config keys: {list(model_config.keys())}")
        if '_class_name' in model_config:
            logger.debug(f"Model class name: {model_config['_class_name']}")
        return 'swan'

    def generate_pipeline_name(self, model_type: str, template_path: Path) -> str:
        """Generate a unique pipeline name based on template and resources.
        
        Args:
            model_type: The model type (e.g., 'swan', 'schism')
            template_path: Path to the pipeline template
            
        Returns:
            Generated pipeline name in format: {model}-{template_hash}-{resource_hash}
        """
        # Hash the template content
        try:
            with open(template_path, 'r') as f:
                template_content = f.read()
            template_hash = hashlib.md5(template_content.encode()).hexdigest()[:6]
        except Exception as e:
            logger.warning(f"Failed to hash template {template_path}: {e}")
            template_hash = "default"
        
        # Hash the resource configuration
        resource_dict = {}
        if self.resources:
            resource_dict = self.resources.get_resource_dict()
        
        # Include stage and other deployment-specific settings
        deployment_config = {
            'stage': self.stage,
            'resources': resource_dict,
            'env_vars': {k: v for k, v in self.env_vars.items() if k.startswith('ROMPY_')},
        }
        
        resource_content = json.dumps(deployment_config, sort_keys=True)
        resource_hash = hashlib.md5(resource_content.encode()).hexdigest()[:6]
        
        return f"{model_type}-{template_hash}-{resource_hash}"

    def should_redeploy(self, existing_pipeline_name: str, current_pipeline_name: str) -> bool:
        """Determine if pipeline should be redeployed based on name changes.
        
        Args:
            existing_pipeline_name: Name of currently deployed pipeline
            current_pipeline_name: Name that would be generated now
            
        Returns:
            True if redeployment is needed
        """
        if existing_pipeline_name != current_pipeline_name:
            logger.info(f"Pipeline name changed: {existing_pipeline_name} → {current_pipeline_name}")
            return True
        return False

    def get_deployment_hash_info(self) -> Dict[str, str]:
        """Get hash information for deployment tracking.
        
        Returns:
            Dictionary with hash components for logging/debugging
        """
        resource_dict = {}
        if self.resources:
            resource_dict = self.resources.get_resource_dict()
            
        return {
            'stage': self.stage,
            'resource_fingerprint': str(resource_dict),
            'env_fingerprint': str({k: v for k, v in self.env_vars.items() if k.startswith('ROMPY_')}),
        }

    @validator('pipeline_template')
    def validate_pipeline_template(cls, v):
        """Validate pipeline template path if provided."""
        if v is not None:
            template_path = Path(v)
            if not template_path.is_absolute():
                # Try to resolve relative to package directory
                try:
                    from rompy_oceanum import pipeline_templates
                    pkg_path = Path(pipeline_templates.__file__).parent / v
                    if pkg_path.exists():
                        return str(pkg_path)
                except ImportError:
                    pass
                # If not found in package, check current directory
                if not Path(v).exists():
                    raise ValueError(f"Pipeline template not found: {v}")
            elif not template_path.exists():
                raise ValueError(f"Pipeline template not found: {v}")
        return v

# Legacy PraxConfig for direct use (not ROMPY backend)
class PraxConfig(BaseModel):
    """Configuration for Prax pipeline backend."""

    base_url: str = Field(..., description="Prax API base URL")
    token: Optional[str] = Field(None, description="Authentication token")
    org: str = Field(..., description="Organization name")
    project: str = Field(..., description="Project name")
    stage: str = Field(default="dev", description="Deployment stage")
    timeout: int = Field(default=3600, ge=60, le=86400, description="Pipeline timeout in seconds")
    resources: Optional[PraxResources] = Field(None, description="Resource configuration")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables")

    def __init__(self, **data):
        """Initialize PraxConfig and auto-load authentication token if needed."""
        super().__init__(**data)
        # If no token provided or placeholder token, try to load from saved auth
        if not self.token or self.token == "your-prax-token-here":
            saved_token = self._load_saved_token()
            if saved_token:
                self.token = saved_token

    def _load_saved_token(self) -> Optional[str]:
        """Load authentication token from oceanum CLI saved credentials."""
        try:
            # Import TokenResponse from oceanum.cli.models
            from oceanum.cli.models import TokenResponse
            
            # Extract domain from base_url (e.g., "https://prax.oceanum.io" -> "oceanum.io")
            from urllib.parse import urlparse
            parsed_url = urlparse(self.base_url)
            domain_parts = parsed_url.hostname.split('.')
            if len(domain_parts) >= 2:
                # For prax.oceanum.io, we want the auth domain auth.oceanum.io
                domain = f"auth.{'.'.join(domain_parts[-2:])}"
            else:
                domain = parsed_url.hostname
            
            # Try to load saved token
            token_response = TokenResponse.load(domain)
            if token_response and not token_response.is_expired:
                logger.info(f"Using saved authentication token for domain: {domain}")
                return token_response.access_token
            elif token_response and token_response.is_expired:
                logger.warning(f"Saved authentication token for {domain} has expired. Please run 'rompy oceanum-auth login' to refresh.")
            else:
                logger.info(f"No saved authentication token found for domain: {domain}. Please run 'rompy oceanum-auth login' to authenticate.")
                
        except ImportError:
            logger.warning("Could not import oceanum authentication modules")
        except Exception as e:
            logger.warning(f"Could not load saved authentication token: {e}")
        
        return None

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

    @validator('base_url')
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip('/')

    @validator('token')
    def validate_token(cls, v):
        """Validate authentication token if provided."""
        if v is None:
            return v
        if not v.strip():
            raise ValueError("Authentication token cannot be empty if provided")
        return v.strip()

    @validator('org', 'project')
    def validate_identifiers(cls, v):
        """Validate organization and project identifiers."""
        if not v or not v.strip():
            raise ValueError("Organization and project identifiers cannot be empty")
        # Basic validation - alphanumeric and hyphens
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError("Identifiers must be alphanumeric with optional hyphens and underscores")
        return v.strip()

    @validator('stage')
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

    @validator('base_url')
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Base URL must start with http:// or https://")
        return v.rstrip('/')

    @validator('token')
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

    @validator('working_dir')
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

    @validator('pipeline_name')
    def validate_pipeline_name(cls, v):
        """Validate pipeline name."""
        if not v or not v.strip():
            raise ValueError("Pipeline name cannot be empty")
        return v.strip()
