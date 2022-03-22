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

class SuperNodeHandler:
    def __init__(self, num_bits: int):
        self.num_bits = num_bits
        self.nodes = []
        self.mutex = Lock()

    def get_join_node(self, ip: str, port: int) -> NodeInfo:
        acquired = self.mutex.acquire(False)
        if not acquired:
            raise DHTBusy()
        elif len(self.nodes) > 0:
            return self.nodes[random.randrange(len(self.nodes))]
        else:
            new_node = NodeInfo(hash(f'{ip}:{port}', self.num_bits), ip, port)
            self.nodes.append(new_node)
            return new_node

    def post_join(self) -> None:
        self.mutex.release()

    def get_node_for_client(self) -> NodeInfo:
        return self.nodes[random.randrange(len(self.nodes))]

if __name__ == '__main__':
    pass