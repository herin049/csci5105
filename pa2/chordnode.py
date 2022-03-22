import os
import sys
import glob

# Load the thrift library
THRIFT_LIB_PATH = os.getenv('THRIFT_LIB_PATH')
if THRIFT_LIB_PATH is not None:
    sys.path.insert(0, glob.glob(THRIFT_LIB_PATH)[0])

from utils import hash, inrange
from typing import List

from gen.service import ChordNodeService, SuperNodeService
from gen.service.ttypes import NodeInfo, DuplicateWord, WordNotFound

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

class ChordNodeHandler:
    def __init__(self, node_info: NodeInfo, predecessor: NodeInfo, finger_table: List[NodeInfo], num_bits: int, caching: bool):
        self.node_info = node_info
        self.predecessor = predecessor
        self.finger_table = finger_table
        self.num_bits = num_bits
        self.caching = caching
        self.table = {}

    def get_preceding_finger(self, id: int) -> NodeInfo:
        for node in reversed(self.finger_table):
            if inrange(self.node_info.id, id, node.id):
                return node
        return self.finger_table[0]

    def put(self, word: str, definition: str) -> None:
        word_id = hash(word, self.num_bits)
        if word in self.table:
            raise DuplicateWord()

        if inrange(self.predecessor.id + 1, self.node_info.id, word_id):
            self.table[word] = definition
        else:
            if self.caching:
                self.table[word] = definition
            next = self.get_preceding_finger(word_id)
            transport = TSocket.TSocket(next.ip, next.port)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = ChordNodeService.Client(protocol)
            transport.open()
            try:
                client.put(word, definition)
            except DuplicateWord as e:
                transport.close()
                raise e
            transport.close()

    def get(self, word: str) -> str:
        word_id = hash(word, self.num_bits)
        if word in self.table:
            return self.table[word]

        if inrange(self.predecessor.id + 1, self.node_info.id, word_id):
            if word not in self.table:
                raise WordNotFound()
            return self.table[word]
        else:
            next = self.get_preceding_finger(word_id)
            transport = TSocket.TSocket(next.ip, next.port)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = ChordNodeService.Client(protocol)
            transport.open()
            try:
                definition = client.get(word)
            except WordNotFound as e:
                transport.close()
                raise e
            transport.close()
            return definition

    def find_successor(self, key: int) -> NodeInfo:
        if inrange(self.predecessor.id + 1, self.node_info.id, self.node_info.id, key):
            return self.node_info
        else:
            next = self.get_preceding_finger(key)
            transport = TSocket.TSocket(next.ip, next.port)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = ChordNodeService.Client(protocol)
            transport.open()
            succ = client.find_successor(key)
            transport.close()
            return succ

    def find_predecessor(self, key: int) -> NodeInfo:
        succ = self.find_predecessor(key)
        transport = TSocket.TSocket(succ.ip, succ.port)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = ChordNodeService.Client(protocol)
        transport.open()
        pred = client.get_predecessor()
        transport.close()
        return pred

    def get_predecessor(self) -> NodeInfo:
        return self.predecessor

    def update_predecessor(self, new_predecessor: NodeInfo) -> None:
        self.predecessor = new_predecessor

    def update_finger_table(self, new_node: NodeInfo, index: int) -> None:
        if inrange(self.node_info.id, self.finger_table[index] - 1, new_node.id):
            self.finger_table[index] = new_node
            transport = TSocket.TSocket(self.predecessor.ip, self.predecessor.port)
            protocol = TBinaryProtocol.TBinaryProtocol(transport)
            client = ChordNodeService.Client(protocol)
            transport.open()
            client.update_finger_table(new_node, index)
            transport.close()


def join_dht(super_node_ip: str, super_node_port: int) -> NodeInfo:
    transport = TSocket.TSocket(super_node_ip, super_node_port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = SuperNodeService.Client(protocol)
    transport.open()
    


def init_chord_node(entry_node: NodeInfo) -> None:
    transport = TSocket.TSocket(entry_node.ip, entry_node.port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ChordNodeService.Client(protocol)
    transport.open()


if __name__ == '__main__':
    node_id = 0
    supernode_ip = None
    supernode_port = None


    if supernode_ip is None:
        print(f'[Node {node_id}] Error, supernode ip was not provided.')
    elif supernode_port is None:
        print(f'[Node {node_id}] Error, supernode port was not provided.')
    else:
        pass
