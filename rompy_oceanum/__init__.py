"""
rompy-oceanum: Oceanum Prax integration for rompy

This package extends rompy with Prax pipeline backend integration using
the rompy plugin architecture.
"""

from .client import PraxClient, PraxResult
from .config import PraxConfig, DataMeshConfig, PraxPipelineConfig
from .pipeline import PraxPipelineBackend
from .postprocess import DataMeshPostprocessor

# Legacy imports for backward compatibility
try:
    from .model_extension import OceanumModelRun
    from .extension import extension
    __all__ = [
        "PraxClient", "PraxResult", "PraxConfig", "DataMeshConfig",
        "PraxPipelineConfig", "PraxPipelineBackend", "DataMeshPostprocessor",
        "OceanumModelRun", "extension"  # Legacy
    ]
except ImportError:
    # If legacy components are not available, only export new components
    __all__ = [
        "PraxClient", "PraxResult", "PraxConfig", "DataMeshConfig",
        "PraxPipelineConfig", "PraxPipelineBackend", "DataMeshPostprocessor"
    ]

__version__ = "0.1.0"
