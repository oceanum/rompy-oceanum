# API Reference

This page documents the API for the `rompy-oceanum` package.

## PraxClient

```python
from rompy_oceanum.client import PraxClient
```

The `PraxClient` class provides methods for interacting with the Oceanum Prax API.

### Constructor

```python
client = PraxClient(base_url="https://prax.oceanum.io", token=None)
```

- `base_url`: Base URL for the Prax API
- `token`: Prax API token (if None, looks for PRAX_TOKEN environment variable)

### Methods

#### submit_pipeline

```python
result = client.submit_pipeline(
    pipeline_name,
    parameters=None,
    org=None,
    project=None,
    stage=None
)
```

Submits a pipeline to Prax.

- `pipeline_name`: Name of the pipeline to run
- `parameters`: Pipeline parameters dictionary
- `org`: Organization name
- `project`: Project name
- `stage`: Stage name (e.g., "dev", "prod")

Returns a `PraxResult` object with information about the submitted run.

#### get_run_status

```python
status = client.get_run_status(
    run_id,
    pipeline_name,
    org=None,
    project=None,
    stage=None
)
```

Gets the status of a pipeline run.

- `run_id`: ID of the run to check
- `pipeline_name`: Name of the pipeline
- `org`: Organization name
- `project`: Project name
- `stage`: Stage name

Returns a dictionary with run status information.

#### get_run_logs

```python
logs = client.get_run_logs(
    run_id,
    pipeline_name,
    org=None,
    project=None,
    stage=None
)
```

Gets logs from a pipeline run.

- `run_id`: ID of the run
- `pipeline_name`: Name of the pipeline
- `org`: Organization name
- `project`: Project name
- `stage`: Stage name

Returns a list of log lines.

## PraxResult

```python
from rompy_oceanum.client import PraxResult
```

The `PraxResult` class represents the result of a Prax pipeline submission.

### Attributes

- `run_id`: ID of the pipeline run
- `pipeline_name`: Name of the pipeline
- `org`: Organization name
- `project`: Project name
- `stage`: Stage name
- `status`: Current status of the run

### Methods

#### get_status

```python
status = result.get_status()
```

Gets the current status of the pipeline run.

Returns a dictionary with run status information.

#### get_logs

```python
logs = result.get_logs()
```

Gets logs from the pipeline run.

Returns a list of log lines.

#### wait_for_completion

```python
final_status = result.wait_for_completion(
    timeout=3600,
    check_interval=30
)
```

Waits for the pipeline run to complete.

- `timeout`: Maximum time to wait in seconds (default: 1 hour)
- `check_interval`: Time between status checks in seconds (default: 30s)

Returns the final status of the run. Raises a `TimeoutError` if the run does not complete within the timeout period.

#### download_outputs

```python
files = result.download_outputs(target_dir="./outputs")
```

Downloads output artifacts from the completed pipeline run.

- `target_dir`: Directory to save the downloaded files

Returns a list of paths to downloaded files.

## ModelRun Extensions

The package extends the rompy `ModelRun` class with the following methods:

### submit_to_prax

```python
result = model_run.submit_to_prax(
    pipeline_name="swan-from-rompy",
    org=None,
    project=None,
    stage="dev",
    prax_url="https://prax.oceanum.io",
    token=None
)
```

Submits the model run to an Oceanum Prax pipeline.

- `pipeline_name`: Name of the pipeline to run (default: swan-from-rompy)
- `org`: Organization name (default: from env var PRAX_ORG)
- `project`: Project name (default: from env var PRAX_PROJECT)
- `stage`: Stage name (default: dev)
- `prax_url`: Prax API base URL (default: https://prax.oceanum.io)
- `token`: Prax API token (default: from env var PRAX_TOKEN)

Returns a `PraxResult` object with information about the submitted run.

### to_prax_parameters

```python
parameters = model_run.to_prax_parameters()
```

Converts the model run configuration to Prax pipeline parameters.

Returns a dictionary with Prax pipeline parameters.
