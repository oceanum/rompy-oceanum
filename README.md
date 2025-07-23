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

# Execute model via Prax pipeline (use filename from init command)
# Requires DATAMESH_TOKEN environment variable to be set
export DATAMESH_TOKEN="your_datamesh_token"
oceanum rompy run rompy_config_swan_basic.yml --pipeline-name my-pipeline

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

# Execute model
RUN_ID=$(oceanum rompy run config.yml swan --pipeline-name swan-operational | grep "Prax run ID:" | cut -d' ' -f4)

# Monitor execution
oceanum rompy status $RUN_ID --watch

# Download results when complete
oceanum rompy sync $RUN_ID ./outputs --organize
```

### CLI Reference

```bash
# Generate configuration from template
oceanum rompy init swan --template basic --domain "my_domain"

# Execute model via Prax pipeline
oceanum rompy run config.yml swan --pipeline-name my-pipeline

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
    oceanum rompy run "${domain}_config.yml" swan --pipeline-name swan-operational &
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

### Pipeline Requirements

When running SWAN or other models on the Oceanum Prax platform, the following requirements must be met:

#### DataMesh Token

Models that access the DataMesh API require a DataMesh token:

```bash
# Set the token as an environment variable (recommended)
export DATAMESH_TOKEN="your_datamesh_token"

# Or provide it directly when running the command
oceanum rompy run config.yml --pipeline-name swan-from-rompy --token "your_datamesh_token"
```

Without a valid DataMesh token, models that require access to data sources will fail with an error like:
```
⚠ spec.arguments.datamesh-token.value or spec.arguments.datamesh-token.valueFrom is required
```

#### rompy-config Requirement

The Prax pipeline also requires the rompy configuration to be passed as a parameter. This is handled automatically by the `oceanum rompy run` command, but if you're using the direct Prax command, you'll need to provide this:

```bash
# When using oceanum rompy run (handles this automatically)
oceanum rompy run config.yml --pipeline-name swan-from-rompy

# When using direct prax command
oceanum prax submit pipeline swan-from-rompy -p rompy-config="@/path/to/config.yml" -p datamesh-token="$DATAMESH_TOKEN"
```

Without this parameter, you'll get an error like:
```
⚠ spec.arguments.rompy-config.value or spec.arguments.rompy-config.valueFrom is required
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

```python
import subprocess

# Generate configuration
subprocess.run([
    "oceanum", "rompy", "init", "swan",
    "--template", "research",
    "--domain", "research_domain"
], check=True)

# Execute model
result = subprocess.run([
    "oceanum", "rompy", "run", "config.yml", "swan",
    "--pipeline-name", "swan-research", 
    "--wait"
], capture_output=True, text=True, check=True)

# Extract run ID for further processing
for line in result.stdout.split('\n'):
    if '🆔 Prax run ID:' in line:
        run_id = line.split()[-1]
        break
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

Authentication is now handled via `oceanum auth login` instead of environment variables.

## License

MIT
