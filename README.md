# rompy-oceanum

[![Documentation](https://github.com/rom-py/rompy-oceanum/actions/workflows/docs.yml/badge.svg)](https://github.com/rom-py/rompy-oceanum/actions/workflows/docs.yml)
[![Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://rom-py.github.io/rompy-oceanum/)

A rompy plugin that provides seamless integration with the oceanum CLI and Prax pipeline backend for executing ocean models on Oceanum's platform. Available as the `oceanum rompy` command group with enhanced user experience and unified authentication.

📖 **[View Full Documentation](https://rom-py.github.io/rompy-oceanum/)**

## Installation

```bash
pip install rompy-oceanum oceanum
```

Verify the integration works:

```bash
oceanum rompy --help
```

## Features

- **Oceanum CLI Integration**: Seamlessly integrated as `oceanum rompy` command group
- **Unified Authentication**: Uses oceanum's built-in authentication system (no manual token management)
- **Enhanced User Experience**: Rich terminal output with progress indicators and organized file management
- **Template-Based Configuration**: Generate optimized rompy configurations automatically
- **Complete Workflow Support**: From configuration creation to result management
- **Pipeline Backend**: Execute rompy models on Oceanum's Prax platform
- **Smart Output Management**: Automatic file organization by stage and type

## Usage

### Quick Start with Oceanum CLI

```bash
# Authenticate with oceanum (one-time setup)
oceanum auth login

# Generate optimized rompy configuration
oceanum rompy init swan --template basic --domain "my_domain"

# Create a project for your pipelines (if you don't have one)
oceanum rompy projects create my-project.yaml

# Deploy the default pipeline template
oceanum rompy pipelines --deploy-default --project-name my-project

# Execute model via Prax pipeline
oceanum rompy run config.yml swan --pipeline-name swan-from-rompy --project my-project

# Monitor execution
oceanum rompy status <run-id> --watch

# Download organized results
oceanum rompy sync <run-id> ./outputs --organize
```

### Available CLI Commands

| Command | Description |
|---------|-------------|
| `oceanum rompy init` | Generate optimized rompy configurations from templates |
| `oceanum rompy run` | Execute models via Prax pipeline with enhanced monitoring |
| `oceanum rompy status` | Monitor pipeline execution with real-time updates |
| `oceanum rompy logs` | View and filter pipeline logs |
| `oceanum rompy sync` | Download and organize pipeline outputs |
| `oceanum rompy projects` | Manage Prax projects for rompy pipelines |
| `oceanum rompy pipelines` | Manage pipeline templates and deployments |

### Basic Pipeline Execution (Programmatic)

```python
import rompy

# Create a rompy model configuration as usual
model_run = rompy.ModelRun(
    config=swan_config,
    output_dir="./outputs",
    run_id="my-run"
)

# Execute using Prax pipeline backend (authentication handled automatically)
result = model_run.pipeline(
    backend="prax",
    pipeline_name="swan-from-rompy",
    wait_for_completion=True,
    download_outputs=True
)

# Check results
if result["success"]:
    print(f"Pipeline completed! Run ID: {result['prax_run_id']}")
    print(f"Downloaded files: {result.get('downloaded_files', [])}")
```

### Configuration Templates

Generate optimized configurations for different use cases:

```bash
# Basic operational configuration
oceanum rompy init swan --template basic --domain "perth_coast"

# Advanced research configuration
oceanum rompy init swan --template research --domain "great_barrier_reef"

# Interactive configuration setup
oceanum rompy init schism --template advanced --interactive

# Custom grid specification
oceanum rompy init ww3 --bbox "110,-35,120,-25" --grid-resolution 0.05
```

Template types:
- `basic`: Essential model physics and standard outputs
- `advanced`: Additional physics, validation, and diagnostics  
- `research`: Comprehensive analysis and statistics
- `operational`: Optimized for speed and monitoring

### Authentication

rompy-oceanum uses oceanum's unified authentication system:

```bash
# Authenticate once (session persists)
oceanum auth login

# Check authentication status
oceanum auth status

# Logout when needed
oceanum auth logout
```

No manual token management is required - all authentication is handled automatically.

### Complete Workflow Example

```bash
#!/bin/bash
# Complete modeling workflow

# Ensure authentication
oceanum auth login

# Generate configuration
oceanum rompy init swan --template operational --domain "perth_coast"

# Create project if needed
oceanum rompy projects create wave-project.yaml

# Deploy the default pipeline template
oceanum rompy pipelines deploy-default --project wave-project

# Execute model
RUN_ID=$(oceanum rompy run config.yml swan --pipeline-name swan-from-rompy --project wave-project | grep "Prax run ID:" | cut -d' ' -f4)

# Monitor execution
oceanum rompy status $RUN_ID --watch

# Download results when complete
oceanum rompy sync $RUN_ID ./outputs --organize
```

### CLI Reference

```bash
# Generate configuration from template
oceanum rompy init swan --template basic --domain "my_domain"

# Create a project for your pipelines
oceanum rompy projects create my-project.yaml

# Deploy the default pipeline template
   oceanum rompy pipelines deploy-default --project rompy-oceanum

# Or create a custom pipeline template
oceanum rompy pipelines create my-pipeline.yaml --project my-project

# Execute model via Prax pipeline
oceanum rompy run config.yml swan --pipeline-name swan-from-rompy --project my-project

# Monitor pipeline execution
oceanum rompy status <run-id> --watch

# View real-time logs
oceanum rompy logs <run-id> --follow

# Download organized outputs
oceanum rompy sync <run-id> ./outputs --organize
```

## Enhanced Features

### Rich Terminal Output

The oceanum CLI integration provides enhanced user experience:

```bash
🚀 Executing pipeline: swan-operational
📊 Model: swan, Run ID: perth_coast_swan_basic
🏢 Org: oceanum, Project: wave-forecasting, Stage: dev
✅ Pipeline executed successfully!
🆔 Prax run ID: prax-perth_coast_swan_basic
💡 Monitor with: oceanum rompy status prax-perth_coast_swan_basic
```

### Organized File Downloads

Automatic file organization by stage and type:

```bash
📁 Files organized by stage and type:
  outputs/
  ├── postprocess/
  │   ├── netcdf/
  │   │   └── wave_height.nc
  │   └── plots/
  │       └── wave_field.png
  ├── run/
  │   └── logs/
  │       └── model.log
  └── run_metadata.json
```

### Automation-Friendly

Perfect for scripts and automation:

```bash
# Batch processing multiple domains
for domain in "perth" "sydney" "melbourne"; do
    oceanum rompy init swan --template operational --domain "$domain" --output "${domain}_config.yml"
    
    # Deploy the default pipeline template if not already done
    oceanum rompy pipelines deploy-default --project wave-project 2>/dev/null || true
    
    oceanum rompy run "${domain}_config.yml" swan --pipeline-name swan-from-rompy --project wave-project &
done
wait  # Wait for all background jobs
```

## Configuration

### Authentication

rompy-oceanum uses oceanum's unified authentication system - no manual token management required:

```bash
# Authenticate once (session persists across terminals)
oceanum auth login

# Check authentication status
oceanum auth status

# Logout when needed
oceanum auth logout
```

### Optional Environment Variables

You can set default values for common parameters:

```bash
export ROMPY_CONFIG="./configs/default.yml"  # Default configuration file
export ROMPY_MODEL="swan"                    # Default model type
export PRAX_PROJECT="wave-forecasting"      # Default project name
export PRAX_STAGE="dev"                     # Default deployment stage
```

### Template Configuration

Generate configurations using built-in templates:

```bash
# List available templates
oceanum rompy init --help

# Generate with template
oceanum rompy init swan --template operational --domain "my_domain"
```

For programmatic configuration:

```bash
export DATAMESH_TOKEN="your_datamesh_token"
export DATAMESH_BASE_URL="https://datamesh.oceanum.io"  # Optional
```

### Configuration Files

You can also provide configuration explicitly in your code:

```python
from rompy_oceanum.config import PraxConfig

config = PraxConfig(
    base_url="https://prax.oceanum.io",
    token="your-token",
    org="your-org",
    project="your-project",
    stage="dev"
)
```

## Architecture

This package implements rompy's plugin architecture:

- **Pipeline Backend**: Registered as `rompy.pipeline` entry point
- **Postprocessor**: DataMesh integration via `rompy.postprocess` entry point
- **Runtime Selection**: Backends chosen at execution time, not configuration time
- **Separation of Concerns**: Model configuration separate from execution configuration

## Migration

If you're upgrading from the legacy `OceanumModelRun` approach, see [MIGRATION.md](./MIGRATION.md) for a complete migration guide.

## Examples

### Complete Workflow Scripts

See workflow automation examples:

```bash
# Batch processing script
for domain in "domain1" "domain2" "domain3"; do
    oceanum rompy init swan --template operational --domain "$domain" --output "${domain}.yml"
    oceanum rompy run "${domain}.yml" swan --pipeline-name swan-operational
done
```

### Python Integration

Use rompy programmatically with oceanum authentication:

```python
import rompy
from rompy_oceanum import PraxConfig

# Create configuration programmatically
config = rompy.SwanConfig(
    grid=rompy.swan.SwanGrid(x0=115.0, y0=-35.0, dx=0.05, dy=0.05, nx=100, ny=80),
    winds=[rompy.swan.SwanWind(speed=10.0, direction=270.0)],
    physics={"whitecapping": True, "breaking": True}
)

# Create ModelRun
model_run = rompy.ModelRun(config=config, output_dir="./outputs")

# Submit to Prax with project specification
prax_config = PraxConfig(
    org="your-org",
    project="wave-project",  # Specify your project
    pipeline_name="swan-pipeline"
)

result = model_run.pipeline(backend="prax", **prax_config.dict())

# Monitor execution
result.wait_for_completion(timeout=3600)

# Download results
if result.is_successful():
    output_paths = result.download_outputs("./results")
```


## Documentation

For comprehensive documentation including CLI reference, configuration guides, and examples:

- **Full Documentation**: [docs/](./docs/) directory
- **CLI Reference**: Complete command documentation with examples
- **Getting Started**: Step-by-step tutorials with oceanum CLI integration
- **Configuration Guide**: Template system and advanced configuration options

## Migration from Standalone CLI

If you were using the standalone `rompy-oceanum` CLI, the new commands are:

| Old Command | New Command |
|-------------|-------------|
| `rompy-oceanum run` | `oceanum rompy run` |
| `rompy-oceanum status` | `oceanum rompy status` |
| `rompy-oceanum logs` | `oceanum rompy logs` |
| `rompy-oceanum download` | `oceanum rompy sync` |
| Manual config | `oceanum rompy init` |
| (New) Project management | `oceanum rompy projects` |
| (New) Pipeline management | `oceanum rompy pipelines` |

Authentication is now handled via `oceanum auth login` instead of environment variables.

## License

MIT
