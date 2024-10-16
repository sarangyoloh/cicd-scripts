import json
import os

apply_path = "./apply.json"
lambda_config_path = "./lambda_config.json"
cli_commands_path = "./cli_commands.json"

create_function_cmd = "aws lambda create-function"
update_function_code_cmd = "aws lambda update-function-code"
update_function_config_cmd = "aws lambda update-function-configuration"
create_function_version_cmd = "aws lambda publish-version"
create_function_alias_cmd = "aws lambda create-alias"
update_function_alias_cmd = "aws lambda update-alias"

# create_function without alias -> just execute the create_function_command
# create_function with alias -> just execute the create_alias comamand and also create the version
# update_function code -> just update the code
# create_version -> just execute the create version command
# update_function_configuration -> 
# create the zip inside the script itself and save it in the runner and reference it if needed in the command
# can create the jar everytime and then save it in the .m2 so not needed next time.

cli_commands = []
apply_json = {}
lambda_config_json = {}
build_proj_names = {}
is_parent_built = False

def parse_json(file_path):
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)
            return data
        except json.JSONDecodeError as e:
            print(f"Error parsing {file_path}: {e}")
            return None

def apply_file_reader(content):
    create_function_reader(content["create_function"])
    update_function_code_reader(content["update_function_code"])

def update_function_code_reader(update_function_code):
    if(len(update_function_code) > 0): 
        global is_parent_built
        if not is_parent_built:
            install_parent_build()
            is_parent_built = True

    for logical_id in update_function_code:
        aws_cli_update_code_cmd_gen(get_lambda_config_detail(logical_id))

def create_function_reader(create_function):
    if(len(create_function) > 0):
        install_parent_build()
        global is_parent_built
        is_parent_built = True

        for logical_id in create_function:
            aws_cli_create_function_cmd_gen(get_lambda_config_detail(logical_id))
        
def get_lambda_config_detail(config_name):
    if is_logical_id_present(config_name):
        return lambda_config_json.get(config_name)

def is_logical_id_present(config_name):
    return lambda_config_json.get(config_name)

def aws_cli_update_code_cmd_gen(lambda_config_detail):
    update_code_cmd = {}
    cmd = update_function_code_cmd
    project_dir = lambda_config_detail.get("project_dir")
    if(project_dir not in build_proj_names):
        jar_path = package_child_build(project_dir)
        update_code_cmd['description'] = f"deploying the jar present in path: {jar_path}"
        update_code_cmd['cmd'] = f"aws s3 cp {jar_path} s3://<Bucket>/<Key>"
        cli_commands.append(update_code_cmd.copy())
        build_proj_names[f"{project_dir}"] = jar_path
        
    jar_name = build_proj_names.get(project_dir).split("/")[-1]
    cmd = argument_appender(cmd, "function-name", lambda_config_detail.get("function-name"))
    cmd = argument_appender(cmd, "s3-bucket", lambda_config_detail.get("function-name"))
    cmd = argument_appender(cmd, "s3-key", jar_name)

    update_code_cmd['description'] = f"updating the function code for {lambda_config_detail.get("function-name")}"
    update_code_cmd['cmd'] = cmd
    cli_commands.append(update_code_cmd.copy())

def aws_cli_create_function_cmd_gen(lambda_config_detail):
    create_cmd = {}
    cmd = create_function_cmd
    for config_key in lambda_config_detail:
        if(config_key == "project_dir"):
            project_dir = lambda_config_detail.get("project_dir")
            
            if(project_dir not in build_proj_names):
                jar_path = package_child_build(project_dir)
                create_cmd['description'] = f"deploying the jar present in path: {jar_path}"
                create_cmd['cmd'] = f"aws s3 cp {jar_path} s3://<Bucket>/<Key>"
                cli_commands.append(create_cmd.copy())
                build_proj_names[f"{project_dir}"] = jar_path
            
            jar_name = build_proj_names.get(project_dir).split("/")[-1]
            cmd = comma_sep_argument_appender(cmd, "code", {'S3Bucket': "name", "S3Key": jar_name})         
        
        config_val = lambda_config_detail.get(config_key)    
        
        if config_key != "function-alias" and config_key != "function-version" and config_key != "project_dir":
            cmd = argument_appender(cmd, config_key, config_val)     
    
    create_cmd['description'] = f"create the {lambda_config_detail['function-name']}"
    create_cmd['cmd'] = cmd
    cli_commands.append(create_cmd)
    
def install_parent_build():
    os.system("mvn clean install -f cicd-feasibility-check/parent-lambda")
    pass

def package_child_build(project_dir):
    os.system(f"mvn clean package -f cicd-feasibility-check/{project_dir}")
    target_dir = f"cicd-feasibility-check/{project_dir}/target"
    result = ""
    for fn in os.listdir(target_dir):
       full_path = os.path.join(target_dir, fn)
       if fn.startswith(project_dir) and os.path.isfile(full_path):
           result = full_path
           break
    return result        

# S3Bucket=<your-bucket-name>,S3Key=<your-lambda-code>.jar

def argument_appender(cmd, config_key, config_val):
    return cmd + f' --{config_key} {config_val}'

def comma_sep_argument_appender(cmd, config_key, args):
    cmd = cmd + f" --{config_key} "
    for key, val in args.items():
        cmd = cmd + key + "=" + val + ","
    return cmd[:-1]
    
if os.path.exists(apply_path) and os.path.exists(lambda_config_path):
    print("Both the files apply.json and lambda_config.json found")
    apply_json = parse_json(apply_path)
    lambda_config_json = parse_json(lambda_config_path)
    apply_file_reader(apply_json)
            
else:
    print("One or both files apply.json at {} and lambda_config.json at {} not found.", apply_path, lambda_config_path)

with open(cli_commands_path, 'w') as output_file:
    json.dump(cli_commands, output_file)

print(f"Output JSON written to {cli_commands_path}")
print(build_proj_names)
