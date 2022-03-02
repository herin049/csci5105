import os
import sys
import glob

# Load the thrift library
THRIFT_LIB_PATH = os.getenv('THRIFT_LIB_PATH')
if THRIFT_LIB_PATH is not None:
    sys.path.insert(0, glob.glob(THRIFT_LIB_PATH)[0])

# Lopad the opencv library
OPENCV_LIB_PATH = os.getenv('OPENCV_LIB_PATH')
if OPENCV_LIB_PATH is not None:
    sys.path.insert(0, glob.glob(OPENCV_LIB_PATH)[0])

# Initialize the project path
PROJ_PATH = os.getenv('PROJ_PATH')
if PROJ_PATH is None:
    PROJ_PATH = '.'

import cv2

from random import random
from time import sleep
import json

from gen.service import ComputeService
from gen.service.ttypes import Task, TaskRejected

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

class ComputeHandler:
    def __init__(self, load_probability: float, load_delay: float, policy: str):
        self.load_probability = load_probability
        self.load_delay = load_delay
        self.policy = policy

    def process(self, task: Task) -> None:
        print(f"[Compute {node_num}] Recieved task to process the file \"{task.file_name}\".")
        # If the policy is "load", reject the task with probability load_probability
        if self.policy == 'load' and random() <= self.load_probability:
            print(f"[Compute {node_num}] Load exceeded, rejecting task.")
            raise TaskRejected("Load exceeded")

        # Inject delay with probability load_probability
        if random() <= self.load_probability:
            print(f"[Compute {node_num}] Injecting delay of {self.load_delay} seconds.")
            sleep(self.load_delay)

        # Read the image and process it
        img = cv2.imread(filename=os.path.join(task.data_dir, 'input_dir', task.file_name))
        gray = cv2.cvtColor(src=img, code=cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(image=gray, threshold1=100, threshold2=200)
        # Write the result to the output directory
        cv2.imwrite(filename=os.path.join(task.data_dir, 'output_dir', task.file_name), img=edges)
        print(f"[Compute {node_num}] Finished processing \"{task.file_name}\".")
        

# Function to load the compute config options from the "config.json" file
def load_compute_config() -> dict:
    config = {}
    config_file = os.path.join(PROJ_PATH, 'config.json')
    if os.path.exists(config_file):
        with open(config_file) as json_file:
            config = json.load(json_file)
            config = config.get('compute', {})
    return config


if __name__ == '__main__':
    # Get the node number and calculate the port the node should listen on
    node_num = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    node_port = 9091 + int(node_num)

    # Load the compute config
    compute_config = load_compute_config()
    
    # Initialize variables, e.g. compute policy, load probability and load delay
    compute_policy = compute_config.get('compute_policy', 'random')
    load_probs = compute_config.get('load_probs', [])
    load_probability = load_probs[node_num] if node_num < len(load_probs) else 0.5
    load_delay = compute_config.get('load_delay', 3)

    # Initialize the compute handler
    handler = ComputeHandler(load_probability=load_probability, load_delay=load_delay, policy=compute_policy)
    print(f"[Compute {node_num}] Initializing the compute handler with a load probability of {load_probability}, a load delay of {load_delay} seconds and a compute policy of \"{compute_policy}\".")

    # Initialize and compute service processor
    processor = ComputeService.Processor(handler)
    transport = TSocket.TServerSocket(port=node_port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    # Initialize the server
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)

    print(f"[Compute {node_num}] Starting compute node...")
    server.serve()
    print(f"[Compute {node_num}] Done.")
