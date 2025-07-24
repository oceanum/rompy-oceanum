"""
Pipeline templates for Prax deployment.

This module contains YAML templates for different model types that can be deployed
to the Prax platform for executing ROMPY models.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import logging

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent

# Supported model types and their default templates
MODEL_TEMPLATES = {
    'swan': 'swan.yaml',
    'schism': 'schism.yaml',  # Placeholder for future
    'ww3': 'ww3.yaml',        # Placeholder for future
}


def get_template_path(model_type: str) -> Optional[Path]:
    """Get the path to the template for a given model type.
    
    Args:
        model_type: The model type (e.g., 'swan', 'schism')
        
    Returns:
        Path to the template file, or None if not found
    """
    template_name = MODEL_TEMPLATES.get(model_type.lower())
    if not template_name:
        logger.warning(f"No template found for model type: {model_type}")
        return None
        
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        logger.warning(f"Template file not found: {template_path}")
        return None
        
    return template_path


def load_template(model_type: str) -> Optional[Dict[str, Any]]:
    """Load and parse a pipeline template.
    
    Args:
        model_type: The model type (e.g., 'swan', 'schism')
        
    Returns:
        Parsed template dictionary, or None if not found
    """
    template_path = get_template_path(model_type)
    if not template_path:
        return None
        
    try:
        with open(template_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load template {template_path}: {e}")
        return None


def list_available_templates() -> Dict[str, str]:
    """List all available templates.
    
    Returns:
        Dictionary mapping model types to template file names
    """
    available = {}
    for model_type, template_name in MODEL_TEMPLATES.items():
        template_path = TEMPLATE_DIR / template_name
        if template_path.exists():
            available[model_type] = template_name
        else:
            logger.debug(f"Template {template_name} not found for {model_type}")
    return available