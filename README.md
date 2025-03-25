# rompy-oceanum

A rompy extension for interacting with the Oceanum Prax pipeline deployment and management system.

## Installation

```bash
pip install rompy-oceanum
```

## Features

- Submit rompy model configurations to Oceanum Prax pipelines
- Monitor pipeline status and logs
- Download output files from completed pipelines

## Usage

```python
import rompy
import rompy_oceanum

# Create a rompy model configuration as usual
model_run = rompy.ModelRun(...)

# Submit to Prax pipeline
result = model_run.submit_to_prax(
    pipeline_name="swan-from-rompy",
    user="username",
    org="orgname",
    project="project-name",
    stage="dev"
)

# Monitor status
status = result.get_status()

# Get logs
logs = result.get_logs()

# Download outputs when complete
result.download_outputs(target_dir="./outputs")
```

## Authentication

Set your Prax API token as an environment variable:

```bash
export PRAX_TOKEN="your_token_here"
```

## Documentation

For more detailed documentation, see the [docs](./docs) directory.

## License

MIT
