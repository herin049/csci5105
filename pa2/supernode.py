import os
import sys
import glob

# Load the thrift library
THRIFT_LIB_PATH = os.getenv('THRIFT_LIB_PATH')
if THRIFT_LIB_PATH is not None:
    sys.path.insert(0, glob.glob(THRIFT_LIB_PATH)[0])

from utils import hash

import random
from typing import List
from threading import Lock

from gen.service import ChordNodeService, SuperNodeService
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
        acquired = self.mutex.acquire(False)
        if not acquired:
            log(f'Unable to acquire mutex, returning DHTBusy to {ip}:{port}')
            raise DHTBusy()
        elif len(self.nodes) > 0:
            log(f'Successfully acquired mutex, returning a random node to {ip}:{port}')
            return self.nodes[random.randrange(len(self.nodes))]
        else:
            log(f'DHT is empty, returning empty NodeInfo to {ip}:{port}')
            new_node = NodeInfo(0, '', 0)
            self.nodes.append(NodeInfo(hash(f'{ip}:{port}', self.num_bits), ip, port))
            return new_node

    def post_join(self) -> None:
        log(f'Recieved join event, releasing the DHT mutex.')
        self.mutex.release()

    def get_node_for_client(self) -> NodeInfo:
        log(f'Returning node for client.')
        return self.nodes[random.randrange(len(self.nodes))]

def log(message):
    if DEBUG:
        print(f'[Super Node] {message}')

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('[Super Node] Insufficient number of arguments.')
    super_node_ip = sys.argv[1].split(':')[0]
    super_node_port = int(sys.argv[1].split(':')[1])
    num_bits = int(sys.argv[2])
    DEBUG = int(sys.argv[3]) > 0
    
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