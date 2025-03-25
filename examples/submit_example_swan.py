import yaml
import rompy
import rompy_oceanum

# Load model configuration
model_config = yaml.safe_load(open("example_swan.yaml"))


# Create a rompy model configuration as usual
model_run = rompy.model.ModelRun(**model_config)

# Submit to Prax pipeline
result = model_run.submit_to_prax(
    pipeline_name="swan-from-rompy",
    user="t.durrant@oceanum.science",
    org="oceanum",
    project="rompy-test",
    stage="dev"
)

# Monitor status
status = result.get_status()

# Get logs
logs = result.get_logs()

# Download outputs when complete
result.download_outputs(target_dir="./outputs")