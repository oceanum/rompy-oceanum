"""
rompy-oceanum: Oceanum Prax integration for rompy

This package extends rompy to allow submitting model runs to Oceanum's Prax system.
"""

from .prax import PraxClient
from .extension import extension
from .model_extension import add_prax_methods_to_model_run

__all__ = ["PraxClient", "extension"]

# Initialize the extension on import
add_prax_methods_to_model_run()
