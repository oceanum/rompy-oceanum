"""Main entry point module for rompy run command."""

from .run import run
from .init import init
from .status import status
from .logs import logs
from .sync import sync
from .pipelines import pipelines
from .pipeline_crud import pipeline_crud

# Export the command for entry point discovery
__all__ = ["run", "init", "status", "logs", "sync", "pipelines", "pipeline_crud"]
