"""
Model extension for rompy-oceanum.

This module extends the rompy ModelRun class with methods for submitting to Prax.
"""

import os
import logging
import yaml
from typing import Dict, Any, Optional, Union, TYPE_CHECKING

from .prax import PraxClient, PraxResult

# Set up logging
logger = logging.getLogger(__name__)

# This is to avoid importing rompy which might not be installed yet
# during setup/installation of this package
if TYPE_CHECKING:
    from rompy.model import ModelRun
else:
    ModelRun = None

def add_prax_methods_to_model_run():
    """Add Prax-related methods to the rompy ModelRun class."""
    try:
        # Import here to avoid circular imports
        from rompy.model import ModelRun as _ModelRun
        global ModelRun
        ModelRun = _ModelRun
        
        # Only add methods if they don't already exist
        if not hasattr(ModelRun, "submit_to_prax"):
            # Add the methods
            ModelRun.submit_to_prax = submit_to_prax
            ModelRun.to_prax_parameters = to_prax_parameters
            
            logger.info("Added Prax methods to rompy ModelRun class")
        else:
            logger.info("Prax methods already added to rompy ModelRun class")
            
    except ImportError:
        logger.warning("Could not import rompy. Make sure it's installed.")
        pass

def submit_to_prax(self: "ModelRun", 
                 pipeline_name: str = "swan-from-rompy", 
                 user: str = None,
                 org: str = None,
                 project: str = None,
                 stage: str = "dev",
                 prax_url: str = "https://prax.oceanum.io",
                 token: Optional[str] = None) -> PraxResult:
    """
    Submit this model run to an Oceanum Prax pipeline.
    
    Args:
        pipeline_name: Name of the pipeline to run (default: swan-from-rompy)
        user: Username (default: from env var PRAX_USER)
        org: Organization name (default: from env var PRAX_ORG)
        project: Project name (default: from env var PRAX_PROJECT)
        stage: Stage name (default: dev)
        prax_url: Prax API base URL (default: https://prax.oceanum.io)
        token: Prax API token (default: from env var PRAX_TOKEN)
        
    Returns:
        PraxResult object with information about the submitted run
    """
    # Get values from environment variables if not provided
    user = user or os.environ.get("PRAX_USER")
    org = org or os.environ.get("PRAX_ORG")
    project = project or os.environ.get("PRAX_PROJECT")
    
    # Check required parameters
    if not user:
        raise ValueError("User is required. Provide as parameter or set PRAX_USER env var.")
    if not org:
        raise ValueError("Organization is required. Provide as parameter or set PRAX_ORG env var.")
    if not project:
        raise ValueError("Project is required. Provide as parameter or set PRAX_PROJECT env var.")
    
    # Create Prax client
    client = PraxClient(base_url=prax_url, token=token)
    
    # Convert model run to Prax parameters
    parameters = self.to_prax_parameters()
    
    # Submit pipeline
    logger.info(f"Submitting {pipeline_name} pipeline to Prax")
    result = client.submit_pipeline(
        pipeline_name=pipeline_name,
        user=user,
        org=org,
        project=project,
        stage=stage,
        parameters=parameters
    )
    
    logger.info(f"Pipeline submitted successfully with run ID: {result.run_id}")
    return result

def to_prax_parameters(self: "ModelRun") -> Dict[str, Any]:
    """
    Convert this model run configuration to Prax pipeline parameters.
    
    Returns:
        Dictionary with Prax pipeline parameters
    """
    # Convert model config to YAML
    config_dict = self.model_dump()
    yaml_content = yaml.dump(config_dict, default_flow_style=False)
    
    # Create pipeline parameters
    parameters = {
        "rompy-config": yaml_content
    }
    
    return parameters
