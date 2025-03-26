#!/usr/bin/env python
"""
Example script for submitting a SWAN model run to Prax with automatic pipeline deployment.
"""

import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Import the required modules from rompy-oceanum
from rompy.model import ModelRun
from rompy_oceanum.prax import PraxClient

# Path to the pipeline template file
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            "pipeline_templates", "swan.yaml")

# Initialize the client
client = PraxClient()

# Create a ModelRun instance
model = ModelRun()

# Submit the swan-from-rompy pipeline to Prax
result = model.submit_to_prax(
    pipeline_name="swan-from-rompy",
    user="t.durrant@oceanum.science",
    org="oceanum",
    project="rompy-oceanum",
    stage="dev",
)

# Deploy the pipeline if it doesn't already exist
# This ensures the pipeline is available before attempting to use it
deployed = result.deploy_if_needed(template_path=TEMPLATE_PATH)
if deployed:
    print(f"Pipeline 'swan-from-rompy' was deployed from {TEMPLATE_PATH}")
else:
    print(f"Pipeline 'swan-from-rompy' already exists, no deployment needed")

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
