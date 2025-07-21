"""
rompy-oceanum: Oceanum Prax integration for rompy

This package extends rompy with Prax pipeline backend integration using
the rompy plugin architecture.
"""

from .client import PraxClient, PraxResult
from .config import PraxConfig, DataMeshConfig, PraxPipelineConfig
from .pipeline import PraxPipelineBackend
from .postprocess import DataMeshPostprocessor

__all__ = [
    "PraxClient", "PraxResult", "PraxConfig", "DataMeshConfig",
    "PraxPipelineConfig", "PraxPipelineBackend", "DataMeshPostprocessor"
]

__version__ = "0.1.0"
