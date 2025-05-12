#!/usr/bin/env python

import json
import logging

import rompy
import yaml

from rompy_oceanum import OceanumModelRun
from rompy_oceanum.model_extension import (PraxConfig, PraxResources,
                                           PraxTaskResources)

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

# Load model configuration
model_config = yaml.safe_load(open("example_swan.yaml"))

# Define Prax configuration
prax_config = PraxConfig(
    pipeline_name="swan-from-rompy",
    user="t.durrant@oceanum.science",
    org="oceanum",
    project="rompy-oceanum",
    stage="dev",
    resources=PraxResources(run=PraxTaskResources(cpu=2, memory="2G")),
)

# Create an OceanumModelRun with the prax_config
model_run = OceanumModelRun(**model_config, prax_config=prax_config)


# Alternatively, you could use a dictionary for prax_config:
# model_run = OceanumModelRun(
#     **model_config,
#     prax_config={
#         "pipeline_name": "swan-from-rompy",
#         "user": "t.durrant@oceanum.science",
#         "org": "oceanum",
#         "project": "rompy-oceanum",
#         "stage": "dev",
#         "resources": {
#             "run": {"cpu": 2, "memory": "2G"}
#         }
#     }
# )

# # Write the model configuration to a file if needed
# with open("model_config.json", "w") as f:
#     json.dump(model_run.get_spec(), f, indent=2)
# exit()

# Submit to Prax pipeline
# All the configuration is now part of the model_run.prax_config
result = model_run.submit_to_prax()

# Monitor status
status = result.get_status()

# Display a well-formatted summary of the status
print("\nInitial Pipeline Status:")
result.summary_status(status)

# Get logs with streaming enabled
print("Streaming logs (press Ctrl+C to stop)...")
logs = result.get_logs(follow=True, stream_to_stdout=True)

# Get updated status after some time
status = result.get_status()
print("\nUpdated Pipeline Status:")
result.summary_status(status)

# Stream logs again if needed
print("Streaming more logs (press Ctrl+C to stop)...")
logs = result.get_logs(follow=True, stream_to_stdout=True)

# Get updated status after some time
status = result.get_status()
print("\nUpdated Pipeline Status:")
result.summary_status(status)

# Stream logs again if needed
print("Streaming more logs (press Ctrl+C to stop)...")
logs = result.get_logs(follow=True, stream_to_stdout=True)

# Wait for completion
print("Waiting for completion...")
result.wait_for_completion()

# Get final status
final_status = result.get_status()
print("\nFinal Pipeline Status:")
result.summary_status(final_status)

logger.info("Pipeline completed")
logger.info("Output datasets available in datamesh:")
logger.info(
    f"\t paramaters: https://ui.datamesh.oceanum.io/datasource/oceanum-rompy-{model_run.run_id}-grid"
)
logger.info(
    f"\t spectra:    https://ui.datamesh.oceanum.io/datasource/oceanum-rompy-{model_run.run_id}-spectra"
)

# # Download outputs when complete (not yet implemented in Prax)
# print("Downloading outputs...")
# result.download_outputs(target_dir="./outputs")
