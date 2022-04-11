import json

def load_config(config_file) -> dict: 
    with open(config_file, 'r') as file:
        data = file.read()
    return json.loads(data)