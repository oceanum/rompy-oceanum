# Basic Usage

This guide shows how to use the `rompy-oceanum` package to submit rompy model runs to Oceanum's Prax system.

## Submitting a Model Run to Prax

The `rompy-oceanum` package adds a `submit_to_prax` method to the rompy `ModelRun` class that allows you to submit your model configuration to a Prax pipeline:

```python
import rompy
import rompy_oceanum  # Just import to activate the extension

# Create a rompy model configuration as usual
model_run = rompy.ModelRun(
    run_id="my_run",
    output_dir="./outputs",
    period={
        "start": "20230101T000000",
        "duration": "1d",
        "interval": "1h"
    },
    config={
        "model_type": "swanconfig",
        # ... rest of your SWAN configuration ...
    }
)

# Submit to Prax pipeline
result = model_run.submit_to_prax(
    pipeline_name="swan-from-rompy",
    user="your_username",     # Optional if PRAX_USER env var is set
    org="your_organization",  # Optional if PRAX_ORG env var is set
    project="your_project",   # Optional if PRAX_PROJECT env var is set
    stage="dev"               # Default: "dev"
)

# The result object has information about the submitted run
print(f"Run ID: {result.run_id}")
print(f"Status: {result.status}")
```

## Monitoring Pipeline Status

You can check the status of your pipeline run:

```python
# Get current status
status = result.get_status()
print(f"Current status: {status['status']}")

# Wait for completion
final_status = result.wait_for_completion(timeout=1800, check_interval=30)
print(f"Final status: {final_status['status']}")
```

## Getting Pipeline Logs

You can retrieve logs from the pipeline run:

```python
# Get all logs
logs = result.get_logs()
print(logs)

# Get logs for a specific task
task_logs = result.get_logs(task_name="run")
print(task_logs)
```

## Downloading Output Files

Once the pipeline run is complete, you can download the output files:

```python
# Download all output artifacts to a directory
downloaded_files = result.download_outputs(target_dir="./outputs")
print(f"Downloaded files: {downloaded_files}")
```

## Using the PraxClient Directly

If you need more control, you can use the `PraxClient` class directly:

```python
from rompy_oceanum.prax import PraxClient

# Create a client
client = PraxClient(token="your_token")  # Optional if PRAX_TOKEN env var is set

# Submit a pipeline
result = client.submit_pipeline(
    pipeline_name="swan-from-rompy",
    user="your_username",
    org="your_organization",
    project="your_project",
    stage="dev",
    parameters={"rompy-config": "...your config in YAML format..."}
)
```
