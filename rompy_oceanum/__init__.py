"""
rompy-oceanum: Oceanum Prax integration for rompy

This package extends rompy to allow submitting model runs to Oceanum's Prax system.
"""

from .prax import PraxClient, PraxResult
from .extension import extension
from .model_extension import OceanumModelRun

__all__ = ["PraxClient", "PraxResult", "OceanumModelRun", "extension"]

# No need to initialize anymore, OceanumModelRun is ready to use
