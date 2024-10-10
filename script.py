import json
import os

current_file_path = "./current.json"
config_file_path = "./config.json"
output_file_path = "./output.json"

create_function_command = "aws lambda create-function"
update_function_code_command = "aws lambda update-function-code"
update_function_config_command = "aws lambda update-function-configuration"
create_function_version_command = "aws lambda publish-version"
create_function_alias_command = "aws lambda create-alias"
update_function_alias_command = "aws lambda update-alias"

# create_function without alias -> just execute the create_function_command
# create_function with alias -> just execute the create_alias comamand and also create the version
# update_function code -> just update the code
# create_version -> just execute the create version command
# update_function_configuration -> 
# create the zip inside the script itself and save it in the runner and reference it if needed in the command
# can create the jar everytime and then save it in the .m2 so not needed next time.

output_data = {}

# Function to parse JSON file
def parse_json(file_path):
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)
            return data
        except json.JSONDecodeError as e:
            print(f"Error parsing {file_path}: {e}")
            return None

if os.path.exists(current_file_path) and os.path.exists(config_file_path):
    print("Both current and config files found. Parsing...")

    current_file_data = parse_json(current_file_path)
    if current_file_data:
        output_data["create"] = current_file_data.get('create', [])
        output_data["update_code"] = current_file_data.get('update_code', [])
        output_data["update_config"] = current_file_data.get('update_config', [])

    config_data = parse_json(config_file_path)
    if config_data:
        output_data["config"] = config_data
else:
    print("One or both files not found.")

with open(output_file_path, 'w') as output_file:
    json.dump(output_data, output_file)

print(f"Output JSON written to {output_file_path}")
