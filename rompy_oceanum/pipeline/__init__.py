"""
Pipeline backends for the Oceanum implementation of rompy.

This module provides pipeline backends specific to Oceanum, including
the PraxPipelineBackend for executing models on the Prax platform.
"""
import logging
from typing import Dict, Any, Optional

from rompy.pipeline import PipelineBackend

logger = logging.getLogger(__name__)


class PraxPipelineBackend(PipelineBackend):
    """Pipeline backend for Prax execution.
    
    This backend submits the entire model pipeline to Prax for execution.
    """
    
    def execute(self, model_run, **kwargs) -> Dict[str, Any]:
        """Submit the model pipeline to Prax.
        
        Args:
            model_run: The ModelRun instance to execute
            **kwargs: Additional Prax-specific parameters
            
        Returns:
            Dictionary with results from the Prax submission
        """
        # Ensure we have Prax configuration
        if not hasattr(model_run, "prax_config"):
            logger.error("Model run does not have Prax configuration")
            return {"success": False, "message": "Missing Prax configuration"}
            
        logger.info(f"Submitting {model_run.run_id} to Prax")
        
        # Generate input files (if requested)
        if kwargs.get("generate_first", False):
            logger.info("Generating input files before Prax submission")
            model_run.generate()
            
        # Get execution parameters
        parameters = kwargs.get("parameters", {})
        
        # Check if we have both run and postprocess configuration
        run_config = kwargs.get("run_config", {})
        postprocess_config = kwargs.get("postprocess_config", {})
        
        # Prepare the pipeline in Prax-compatible format
        pipeline = self._prepare_pipeline(model_run, run_config, postprocess_config)
        
        # Submit to Prax
        try:
            # In a real implementation, this would use the Prax API client
            # to submit the pipeline to the Prax platform
            logger.info(f"Pipeline would be submitted to Prax: {pipeline}")
            
            # Simulate a successful Prax submission
            prax_job_id = f"prax-{model_run.run_id}"
            
            return {
                "success": True, 
                "job_id": prax_job_id,
                "message": f"Pipeline submitted to Prax with job ID {prax_job_id}",
                "pipeline": pipeline
            }
            
        except Exception as e:
            logger.exception(f"Failed to submit pipeline to Prax: {e}")
            return {"success": False, "message": f"Failed to submit to Prax: {str(e)}"}
    
    def _prepare_pipeline(self, model_run, run_config, postprocess_config) -> Dict:
        """Prepare a pipeline configuration for Prax.
        
        Args:
            model_run: The ModelRun instance
            run_config: Configuration for the run stage
            postprocess_config: Configuration for the postprocess stage
            
        Returns:
            Prax pipeline configuration
        """
        # Real implementation would transform the model configuration
        # into a format suitable for Prax
        return {
            "id": model_run.run_id,
            "stages": [
                {
                    "name": "run",
                    "config": run_config,
                    "resources": {
                        "cpu": model_run.prax_config.resources.get_cpu("run"),
                        "memory": model_run.prax_config.resources.get_memory("run"),
                    }
                },
                {
                    "name": "postprocess",
                    "config": postprocess_config,
                    "resources": {
                        "cpu": model_run.prax_config.resources.get_cpu("postprocess"),
                        "memory": model_run.prax_config.resources.get_memory("postprocess"),
                    }
                }
            ]
        }
