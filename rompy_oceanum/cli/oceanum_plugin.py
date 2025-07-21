"""Direct entry point for oceanum CLI plugin system.

This module provides a direct entry point that oceanum can find and load.
It serves as an adapter between the oceanum CLI system and our rompy_clean implementation.
"""

import click
from .rompy import rompy_group

# Direct alias for oceanum.cli entry point discovery
# oceanum's __main__.py looks for a direct attribute match with the entry point name
rompy = rompy_group

# Make sure rompy is exported
__all__ = ["rompy"]
