# Configuration Options

This page documents the configuration options available when using the `rompy-oceanum` package.

## Environment Variables

The following environment variables can be used to configure the package:

| Variable | Description | Required |
|----------|-------------|----------|
| `PRAX_TOKEN` | Your Prax API token for authentication | Yes |
| `PRAX_USER` | Your Prax username | No (if specified in code) |
| `PRAX_ORG` | Your Prax organization | No (if specified in code) |
| `PRAX_PROJECT` | Your Prax project | No (if specified in code) |

## PraxClient Options

When creating a `PraxClient` instance, you can configure the following options:

```python
from rompy_oceanum.prax import PraxClient

client = PraxClient(
    base_url="https://prax.oceanum.io",  # The base URL for the Prax API
    token="your_token_here"             # Your Prax API token
)
```

## submit_to_prax Method Parameters

When calling the `submit_to_prax` method on a `ModelRun` instance, you can use the following parameters:

```python
result = model_run.submit_to_prax(
    pipeline_name="swan-from-rompy",    # Name of the pipeline to run
    user="your_username",               # Your Prax username
    org="your_organization",            # Your Prax organization
    project="your_project",             # Your Prax project
    stage="dev",                        # Stage to run in (e.g., "dev", "prod")
    prax_url="https://prax.oceanum.io", # Base URL for the Prax API
    token="your_token_here"             # Your Prax API token
)
```

## PraxResult Methods

The `PraxResult` object returned by `submit_to_prax` provides several methods for interacting with the pipeline run:

### get_status

```python
status = result.get_status()
```

Returns the current status of the pipeline run.

### get_logs

```python
logs = result.get_logs(task_name=None)
```

Gets logs from the pipeline run. If `task_name` is provided, only returns logs for that specific task.

### wait_for_completion

```python
final_status = result.wait_for_completion(
    timeout=3600,         # Maximum time to wait in seconds (default: 1 hour)
    check_interval=30     # Time between status checks in seconds (default: 30s)
)
```

Waits for the pipeline run to complete and returns the final status. Raises a `TimeoutError` if the run does not complete within the specified timeout.

### download_outputs

```python
downloaded_files = result.download_outputs(
    target_dir="./outputs"  # Directory to save downloaded files
)
```

Downloads output artifacts from the completed pipeline run and returns a list of paths to the downloaded files.
