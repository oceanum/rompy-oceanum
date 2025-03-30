#!/usr/bin/env python
"""
Example script for submitting a SWAN model run to Prax with automatic pipeline deployment.
"""

import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Import the required modules from rompy-oceanum
from rompy_oceanum import OceanumModelRun
from rompy_oceanum.model_extension import PraxConfig, PraxResources, PraxTaskResources
from rompy_oceanum.prax import PraxClient

# Path to the pipeline template file
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            "pipeline_templates", "swan.yaml")

# Initialize the client
client = PraxClient()

# Create a Prax configuration
prax_config = PraxConfig(
    pipeline_name="swan-from-rompy",
    user="t.durrant@oceanum.science",
    org="oceanum",
    project="rompy-oceanum",
    stage="dev",
    resources=PraxResources(
        run=PraxTaskResources(cpu=2, memory="1G")
    )
)

# Create an OceanumModelRun instance with the prax configuration
model = OceanumModelRun(run_id="example-swan-run", prax_config=prax_config)

# Submit to Prax - all configuration is now part of the model.prax_config
result = model.submit_to_prax(deploy_template=True)

# No need to deploy separately, we're using deploy_template=True in submit_to_prax
# The template_path is automatically determined from the model's swan_pipeline_template property
print(f"Pipeline '{model.prax_config.pipeline_name}' will be deployed automatically if needed")

# Get status
status = result.get_status()
print("Initial status:")
print(status)
print("\n")

# Get logs
logs = result.get_logs()
print("Intermediate logs:")
print(logs)
print("\n")

# Wait for completion (optional, comment out if you don't want to wait)
print("Waiting for completion...")
try:
    result.wait_for_completion(timeout=300)  # 5 minute timeout
    print("Run completed!")
except TimeoutError:
    print("Run did not complete within the timeout period. Continuing...")

# Get final status
final_status = result.get_status()
print("Final status:")
print(final_status)
print("\n")

# Get final logs
final_logs = result.get_logs()
print("Final logs:")
print(final_logs)
print("\n")

# Download outputs when complete
print("Downloading outputs...")
output_files = result.download_outputs(target_dir="./outputs")
print(f"Downloaded output files: {output_files}")
