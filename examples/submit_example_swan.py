import json

import rompy
import yaml

import rompy_oceanum

# Load model configuration
model_config = yaml.safe_load(open("example_swan.yaml"))


# Create a rompy model configuration as usual
model_run = rompy.model.ModelRun(**model_config)

# # Write the model configuration to a file
# yaml.dump(model_run.dump_inputs_dict(), open("model_config.yaml", "w"))
# json.dump(model_run.dump_inputs_json(), open("model_config.json", "w"))
# exit()


# Submit to Prax pipeline
result = model_run.submit_to_prax(
    pipeline_name="swan-from-rompy",
    user="t.durrant@oceanum.science",
    org="oceanum",
    project="rompy-oceanum",
    stage="dev",
)

# Monitor status
status = result.get_status()
# sleep until status is "running"
while status.get("status", "unknown").lower() != "running":
    print(f"Status: {status.get('status', 'unknown')}")
    time.sleep(5)
    status = result.get_status()


# Get logs
logs = result.get_logs()
print("Intermediate logs:")
print(logs)
print("\n")


# Wait for completion
print("Waiting for completion...")
result.wait_for_completion()

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
result.download_outputs(target_dir="./outputs")
