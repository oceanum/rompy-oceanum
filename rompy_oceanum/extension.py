"""
Extension module for rompy-oceanum.

This module provides the entry point for the rompy extension mechanism.
"""

from .model_extension import add_prax_methods_to_model_run

def extension():
    """
    Entry point for the rompy extension mechanism.
    
    This function is called when rompy loads extensions through entrypoints.
    It adds Prax-related methods to the rompy ModelRun class.
    """
    add_prax_methods_to_model_run()
    return {
        "name": "oceanum",
        "description": "Oceanum Prax pipeline integration for rompy",
        "version": "0.1.0",
    }
