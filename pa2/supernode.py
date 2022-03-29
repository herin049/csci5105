import os
import sys
import glob

# Load the thrift library
THRIFT_LIB_PATH = os.getenv('THRIFT_LIB_PATH')
if THRIFT_LIB_PATH is not None:
    sys.path.insert(0, glob.glob(THRIFT_LIB_PATH)[0])

import random
from threading import Lock

from utils import hash, load_config

from gen.service import SuperNodeService
from gen.service.ttypes import NodeInfo, DHTBusy

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

DEBUG = False

class SuperNodeHandler:
    def __init__(self, num_bits: int):
        self.num_bits = num_bits
        self.nodes = []
        self.mutex = Lock()

    def get_join_node(self, ip: str, port: int) -> NodeInfo:
        log(f'Node {ip}:{port} has requested to join the DHT.')
        log(f'Attempting to acquire the DHT mutex.')
        # Attempt to acquire the DHT mutex (in non-blocking mode)
        acquired = self.mutex.acquire(False)
        if not acquired:
            # If the mutex could not be acquired, throw a DHTBusy exception
            log(f'Unable to acquire mutex, returning DHTBusy to {ip}:{port}')
            raise DHTBusy()
        elif len(self.nodes) > 0:
            # If there are nodes already in the DHT, randomly return one of them
            log(f'Successfully acquired mutex, returning a random node to {ip}:{port}')
            return self.nodes[random.randrange(len(self.nodes))]
        else:
            # If the DHT is empty, return an empty NodeInfo object
            log(f'DHT is empty, returning empty NodeInfo to {ip}:{port}')
            new_node = NodeInfo(0, '', 0)
            self.nodes.append(NodeInfo(hash(f'{ip}:{port}', self.num_bits), ip, port))
            return new_node

    def post_join(self) -> None:
        # Release the DHT mutex when the current node finishes joining
        log(f'Recieved join event, releasing the DHT mutex.')
        self.mutex.release()

    def get_node_for_client(self) -> NodeInfo:
        # Return a random node to the client
        log(f'Returning node for client.')
        return self.nodes[random.randrange(len(self.nodes))]

def log(message):
    if DEBUG:
        print(f'[Super Node] {message}')

if __name__ == '__main__':
    # Load the config file
    config_file = 'config.json'
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    config = load_config(config_file)

    # Extract all the relevant configuration values
    super_node_ip = config['super_node']['ip']
    super_node_port = config['super_node']['port']
    num_bits = config['num_bits']
    DEBUG = config['debug']
    
    # Initialize the super node RPC server
    handler = SuperNodeHandler(num_bits)
    processor = SuperNodeService.Processor(handler)
    transport = TSocket.TServerSocket(port=super_node_port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    log('Starting server...')
    server.serve()
    log('Done.')
    pass