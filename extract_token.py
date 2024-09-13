import re
import time
import os
import json

# Debug print: Check if script is running
print("Running extract_token.py...")

# Path to Jupyter log file and config.py file
log_file_path = "/app/jupyter.log"
config_file_path = "/app/solidus/config.py"  # Ensure this points to the correct config file path

# Check if log file exists
if not os.path.exists(log_file_path):
    print(f"Error: Log file '{log_file_path}' not found.")
    exit(1)

# Debug print: Log file found
print(f"Log file '{log_file_path}' found.")

# Wait a bit longer to ensure the log is fully written
time.sleep(5)

# Try reading the Jupyter log file
try:
    with open(log_file_path, "r") as log_file:
        log_content = log_file.read()
        # Debug print: Successfully read the log file
        print("Jupyter log content:")
        print(log_content)
except Exception as e:
    print(f"Error reading log file: {e}")
    exit(1)

# Use regex to search for the token in the log file
token_match = re.search(r"token=([a-zA-Z0-9]+)", log_content)

if token_match:
    jupyter_token = token_match.group(1)
    # Print the extracted token
    print(f"Jupyter token found: {jupyter_token}")

    # Try updating the config_json variable in the config.py file
    try:
        # Read the config.py file
        with open(config_file_path, "r") as config_file:
            config_content = config_file.read()

        # Use regex to locate the config_json content inside config.py
        config_json_match = re.search(r'config_json\s*=\s*("""[\s\S]+?""")', config_content)

        if config_json_match:
            # Extract the current config_json value
            config_json_str = config_json_match.group(1)
            config_data = json.loads(config_json_str.strip('"""'))

            # Update or add the PYTHON_TOKEN key
            config_data["PYTHON_TOKEN"] = jupyter_token

            # Convert back to JSON and ensure formatting is preserved
            updated_config_json = json.dumps(config_data, indent=4)

            # Replace the old config_json content with the updated one
            new_config_content = re.sub(
                r'config_json\s*=\s*("""[\s\S]+?""")',
                f'config_json = """{updated_config_json}"""',
                config_content
            )

            # Write the updated content back to the config.py file
            with open(config_file_path, "w") as config_file:
                config_file.write(new_config_content)

            print("Config file updated successfully.")
        else:
            print("Error: config_json variable not found in the config.py file.")
            exit(1)

    except Exception as e:
        print(f"Error updating config file: {e}")
        exit(1)
else:
    print("Error: Unable to find Jupyter token in the log file.")
    exit(1)