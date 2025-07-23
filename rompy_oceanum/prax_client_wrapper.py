"""
Wrapper for native oceanum-prax client for rompy-oceanum integration.
"""
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from .config import PraxConfig
import logging

# Import the native oceanum-prax client
import sys
import importlib.util
import logging

# Dynamically import PRAXClient from the local source tree
try:
    spec = importlib.util.spec_from_file_location(
        "oceanum.cli.prax.client",
        "/home/tdurrant/source/rompy/rompy-oceanum/relevant_packages/oceanum-prax-cli/src/oceanum/cli/prax/client.py"
    )
    if spec and spec.loader:
        oceanum_prax_client = importlib.util.module_from_spec(spec)
        sys.modules["oceanum.cli.prax.client"] = oceanum_prax_client
        spec.loader.exec_module(oceanum_prax_client)
        PRAXClient = getattr(oceanum_prax_client, "PRAXClient", None)
    else:
        PRAXClient = None
        logging.warning("Could not import PRAXClient from oceanum-prax-cli. Wrapper will not function.")
except Exception as e:
    PRAXClient = None
    logging.warning(f"Could not import PRAXClient from oceanum-prax-cli: {e}. Wrapper will not function.")

except ImportError:
    PRAXClient = None  # For stubbing/testing
    logging.warning("Could not import PRAXClient from oceanum-prax-cli. Wrapper will not function.")

logger = logging.getLogger(__name__)

class PraxClientWrapper:
    """
    Wrapper for the native oceanum-prax client, providing a consistent interface for rompy-oceanum.
    """
    def __init__(self, config: PraxConfig):
        self.config = config
        if PRAXClient is None:
            raise ImportError("PRAXClient not available. Ensure oceanum-prax-cli is installed and importable.")
        # Compose service URL
        service_url = config.base_url.rstrip('/') + '/api'
        self.client = PRAXClient(token=config.token, service=service_url)
        self.org = config.org
        self.project = config.project
        self.stage = config.stage

    def check_pipeline_exists(self, pipeline_name: str) -> bool:
        resp = self.client.get_pipeline(pipeline_name, org=self.org, project=self.project, stage=self.stage)
        return hasattr(resp, 'name') and resp.name == pipeline_name

    def submit_pipeline(self, pipeline_name: str, parameters: Dict[str, Any], wait_for_completion: bool = False, timeout: int = 3600) -> Dict[str, Any]:
        resp = self.client.submit_pipeline(pipeline_name, parameters, org=self.org, project=self.project, stage=self.stage)
        # Convert response to dict
        if hasattr(resp, 'model_dump'):
            result = resp.model_dump(exclude_none=True)
        elif isinstance(resp, dict):
            result = resp
        else:
            result = {"id": getattr(resp, 'id', None), "name": getattr(resp, 'name', None)}
        return result

    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        resp = self.client.get_pipeline_run(run_id, org=self.org, project=self.project, stage=self.stage)
        if hasattr(resp, 'model_dump'):
            return resp.model_dump(exclude_none=True)
        elif isinstance(resp, dict):
            return resp
        else:
            return {"id": getattr(resp, 'id', None), "status": getattr(resp, 'status', None)}

    def get_run_logs(self, run_id: str, task_name: Optional[str] = None) -> List[str]:
        # Only pipeline logs for now
        lines = []
        try:
            for line in self.client.get_pipeline_run_logs(run_id, lines=100, follow=False, org=self.org, project=self.project, stage=self.stage):
                if isinstance(line, bytes):
                    line = line.decode('utf-8')
                lines.append(str(line))
        except Exception as e:
            logger.error(f"Failed to get logs for run {run_id}: {e}")
        return lines

    def download_artifacts(self, run_id: str, target_dir: Union[str, Path], file_patterns: Optional[List[str]] = None) -> List[Path]:
        # Not implemented in oceanum-prax; stub for now
        logger.warning("download_artifacts is not implemented in oceanum-prax. Returning empty list.")
        return []

    def list_pipelines(self) -> List[Dict[str, Any]]:
        resp = self.client.list_pipelines(org=self.org, project=self.project, stage=self.stage)
        if isinstance(resp, list):
            return [r.model_dump(exclude_none=True) if hasattr(r, 'model_dump') else dict(r) for r in resp]
        return []

# Optionally, stub PraxResult for compatibility
class PraxResult:
    pass
