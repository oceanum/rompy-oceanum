"""
rompy-oceanum: Oceanum Prax integration for rompy

This package extends rompy with Prax pipeline backend integration using
the rompy plugin architecture.
"""

from .client import PraxClient, PraxResult
from .config import DataMeshConfig
from .pipeline import PraxPipelineBackend
from .postprocess import DataMeshPostprocessor

__all__ = [
    "DataMeshConfig",
    "PraxPipelineBackend",
    "DataMeshPostprocessor",
    "PraxClient",
    "PraxResult",
]

__version__ = "0.1.6"
