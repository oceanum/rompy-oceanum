"""Main entry point module for rompy run command."""

from .run import run
from .init import init
from .status import status
from .logs import logs
from .sync import sync
from .create import create_resource
from .list import list_resources
from .describe import describe_resource
from .delete import delete_resource

# Export the command for entry point discovery
__all__ = [
    "run", 
    "init", 
    "status", 
    "logs", 
    "sync",
    "create_resource",
    "list_resources",
    "describe_resource",
    "delete_resource",
]
