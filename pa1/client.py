import os
import sys
import glob
import json

# Load the thrift library
THRIFT_LIB_PATH = os.getenv('THRIFT_LIB_PATH')
if THRIFT_LIB_PATH is not None:
    sys.path.insert(0, glob.glob(THRIFT_LIB_PATH)[0])

# Initialize the project path
PROJ_PATH = os.getenv('PROJ_PATH')
if PROJ_PATH is None:
    PROJ_PATH = '.'

from gen.service import ServerService
from gen.service.ttypes import Job

from thrift.transport import TSocket
from thrift.protocol import TBinaryProtocol

# Function to get the server address from the "machine.txt" file
def get_server():
    server = None
    machine_file = os.path.join(PROJ_PATH, 'machine.txt')
    with open(machine_file) as f:
        lines = f.read().splitlines()
        for l in lines:
            parts = l.strip().split(' ')
            if len(parts) >= 2 and parts[0] == 'server':
                server = parts[1]
                break
    return server

# Function to load the client config options from the "config.json" file
def load_client_config() -> dict:
    config = {}
    config_file = os.path.join(PROJ_PATH, 'config.json')
    if os.path.exists(config_file):
        with open(config_file) as json_file:
            config = json.load(json_file)
            config = config.get('client', {})
    return config

if __name__ == '__main__':
    # Get the server ip and load the client config
    server = get_server()
    client_config = load_client_config()
    num_samples = client_config.get('num_samples', 1)

    if server is None:
        print('[Client] No server was provided in the \"machine.txt\" file, exiting...')
    else:
        # Initialize the thrift client to communicate with the server
        transport = TSocket.TSocket(server, 9090)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = ServerService.Client(protocol)
        transport.open()

        # Get the data directory and file names in the input directory
        data_dir = PROJ_PATH
        input_dir = os.path.join(data_dir, './input_dir')
        file_names = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        # Create the job
        job = Job(data_dir, file_names)
        total_duration = 0
        # Submit the job "num_samples" times
        for _ in range(num_samples):
            print(f"[Client] Submitting job to process images [{', '.join(file_names)}] in the directory {data_dir}")
            duration = client.process(job)
            print(f"[Client] Server finished processing job in {duration} seconds.")
            total_duration += duration
    
        # Print the total time to complete and the average time per job
        print(f"[Client] Finished processing the job {num_samples} times in {total_duration} seconds for an average delay of {total_duration / num_samples} seconds.")
        transport.close()
