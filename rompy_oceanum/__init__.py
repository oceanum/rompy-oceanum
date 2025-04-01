"""
rompy-oceanum: Oceanum Prax integration for rompy

This package extends rompy to allow submitting model runs to Oceanum's Prax system.
"""

from .extension import extension
from .model_extension import OceanumModelRun
from .prax import PraxClient, PraxResult

__all__ = ["PraxClient", "PraxResult", "OceanumModelRun", "extension"]

__version__ = "pre-alpha"
