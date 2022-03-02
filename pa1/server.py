import os
import sys
import glob

# Load the thrift library
THRIFT_LIB_PATH = os.getenv('THRIFT_LIB_PATH')
if THRIFT_LIB_PATH is not None:
    sys.path.insert(0, glob.glob(THRIFT_LIB_PATH)[0])

# Initialize the project path
PROJ_PATH = os.getenv('PROJ_PATH')
if PROJ_PATH is None:
    PROJ_PATH = '.'

import time
from threading import Thread
from random import randrange
import json

from gen.service import ComputeService, ServerService
from gen.service.ttypes import Job, Task, TaskRejected

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

# Function to process a task on a seperate thread
def process_task(data_dir: str, file_name: str, compute_nodes: list):
    while True:
        # Select a random node number from [0, len(compute_nodes)]
        node_num = randrange(len(compute_nodes))
        # Connect to the compute node
        transport = TSocket.TSocket(compute_nodes[node_num], 9091 + node_num)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = ComputeService.Client(protocol)
        transport.open()

        # Submit the task
        try:
            task = Task(data_dir, file_name)
            client.process(task)
            # Break from the loop if processed successfully, otherwise try again
            break 
        except TaskRejected as e:
            print(f"[Server] Compute node {node_num} rejected the task.")

        transport.close()

class ServerHandler:
    def __init__(self, compute_nodes: list):
        self.compute_nodes = compute_nodes
    
    def process(self, job: Job) -> float:
        print(f"[Server] Recieved job to process images [{', '.join(job.file_names)}] in the directory: {job.data_dir}")

        start = time.time()
        threads = []
        # Start a thread to process each file name in the job
        for file_name in job.file_names:
            thread = Thread(target=process_task, args=[job.data_dir, file_name, self.compute_nodes])
            thread.start()
            threads.append(thread)

        # Join on all the threads
        for thread in threads:
            thread.join()

        end = time.time()
        duration = end - start
        print(f"[Server] Finished processing job in {duration} seconds.")
        # Return the time it took to process the job back to the client
        return duration

# Function to get the addresses of each of the compute nodes from the "machine.txt" file
def get_compute_nodes() -> list:
    compute_nodes = []
    machine_file = os.path.join(PROJ_PATH, 'machine.txt')
    with open(machine_file) as f:
        lines = f.read().splitlines()
        for l in lines:
            parts = l.strip().split(' ')
            if len(parts) >= 2 and parts[0].startswith('node'):
                compute_nodes.append(parts[1])
    return compute_nodes


if __name__ == '__main__':
    # Get the addresses of the compute nodes
    compute_nodes = get_compute_nodes()

    if len(compute_nodes) == 0:
        print('[Server] No compute nodes were provided in the \"machine.txt\" file, exiting...')
    else:
        print(f"[Server] Initializing server handler.")
        # Initialize the server handler
        handler = ServerHandler(compute_nodes)
        processor = ServerService.Processor(handler)
        transport = TSocket.TServerSocket(port=9090)
        tfactory = TTransport.TBufferedTransportFactory()
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()

        # Initialize the server
        server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)

        print('[Server] Starting server...')
        server.serve()
        print('[Server] Done.')
