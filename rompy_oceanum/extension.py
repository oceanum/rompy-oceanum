"""
Extension module for rompy-oceanum.

This module provides the entry point for the rompy extension mechanism.
"""

from .model_extension import OceanumModelRun

def extension():
    """
    Entry point for the rompy extension mechanism.
    
    This function is called when rompy loads extensions through entrypoints.
    It registers the OceanumModelRun class for use in rompy.
    """
    # No need to modify classes anymore, just return the extension info
    return {
        "name": "oceanum",
        "description": "Oceanum Prax pipeline integration for rompy",
        "version": "0.1.0",
        "model_classes": {
            "OceanumModelRun": OceanumModelRun
        }
    }
