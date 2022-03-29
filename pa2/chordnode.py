import sys
import time
from utils import hash, inrange, load_config
from typing import List, Tuple
from threading import Thread

from gen.service import ChordNodeService, SuperNodeService
from gen.service.ttypes import DHTBusy, NodeInfo, DuplicateWord, WordNotFound

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

class ChordNodeHandler:
    def __init__(self, node_info: NodeInfo, predecessor: NodeInfo, finger_table: List[NodeInfo], num_bits: int, caching: bool):
        self.node_info = node_info
        self.predecessor = predecessor
        self.finger_table = finger_table
        self.num_bits = num_bits
        self.caching = caching
        self.table = {}

    def put(self, word: str, definition: str) -> None:
        word_id = hash(word, self.num_bits)
        log(f'Associating "{word}" ({word_id}) with definition "{definition}".', self.node_info)
        if self.caching and word in self.table:
            # Return an error if caching is enabled and the word is already in the DHT
            log(f'Error, word "{word}" ({word_id}) is already present in the DHT.', self.node_info)
            raise DuplicateWord()
        elif inrange((self.predecessor.id + 1) % 2 ** self.num_bits, self.node_info.id, word_id):
            # If the word id is in the range (pred, curr] update and stop forwarding the request
            log(f'Word "{word}" ({word_id}) inserted with definition "{definition}".', self.node_info)
            self.table[word] = definition
            return
        elif self.caching:
            # If caching is enabled, store the word in the current node
            log(f'Caching word "{word}" ({word_id}) with definition "{definition}".', self.node_info)
            self.table[word] = definition
        # Get the finger that the call should be forwarded to
        finger = self.get_preceding_finger(word_id)
        if finger == self.node_info:
            raise RuntimeError('Error while calling put.')
        client, transport = connect(finger)
        transport.open()
        try:
            # Forward the request to the next node in the DHT
            log(f'Forwarding request to insert "{word}" ({word_id}) with definition "{definition}" to {finger.ip}:{finger.port} ({finger.id}).', self.node_info)
            client.put(word, definition)
        except DuplicateWord as e:
            transport.close()
            raise e
        transport.close()
            
    def get(self, word: str) -> str:
        word_id = hash(word, self.num_bits)
        log(f'Retrieving definition for word "{word}" ({word_id})', self.node_info)
        if word in self.table:
            # If the word is in the table, return its definition
            log(f'Word found in table "{word}" ({word_id}) to be "{self.table[word]}", returning result.', self.node_info)
            return self.table[word]
        elif inrange((self.predecessor.id + 1) % 2 ** self.num_bits, self.node_info.id, word_id):
            # If the word id is in the range (pred, curr] return the word if present and stop forwarding the request
            if word not in self.table:
                log(f'Error, word "{word}" ({word_id}) was not found in the DHT.', self.node_info)
                raise WordNotFound()
            return self.table[word]
        # Get the finger that the call should be forwarded to
        finger = self.get_preceding_finger(word_id)
        if finger == self.node_info:
            raise RuntimeError('Error while calling get.')
        client, transport = connect(finger)
        transport.open()
        try:
            # Forward the request to the next node in the DHT
            log(f'Forwarding request to retrieve definition for word "{word}" ({word_id}) to {finger.ip}:{finger.port} ({finger.id})', self.node_info)
            definition = client.get(word)
        except WordNotFound as e:
            transport.close()
            raise e
        transport.close()
        return definition

    def get_preceding_finger(self, key: int) -> NodeInfo:
        # Logic to find the preceding finger in the finger table for a given key
        for node in reversed(self.finger_table):
            if self.node_info.id != node.id and key != self.node_info.id and key != node.id and inrange(self.node_info.id, key, node.id):
                return node
        return self.finger_table[0]

    def find_predecessor(self, key: int) -> NodeInfo:
        if inrange((self.node_info.id + 1) % 2 ** self.num_bits, self.finger_table[0].id, key):
            # If the key is in the range (curr, succ] then the predecessor is this node
            log(f'Key {key} is in the range ({self.node_info.id}, {self.finger_table[0].id}], returning current node info as the predecessor.', self.node_info)
            return self.node_info
        # Get the finger that the call should be forwarded to
        finger = self.get_preceding_finger(key)
        if finger == self.node_info:
            raise RuntimeError('Error while finding predecessor.')
        log(f'Forwarding request to find the predecessor of {key} to {finger.ip}:{finger.port} ({finger.id}).', self.node_info)
        client, transport = connect(finger)
        transport.open()
        predecessor = client.find_predecessor(key)
        transport.close()
        return predecessor

    def find_successor(self, key: int) -> NodeInfo:
        # Find the predecessor of the key
        predecessor = self.find_predecessor(key)
        if predecessor == self.node_info:
            return self.finger_table[0]
        client, transport = connect(predecessor)
        transport.open()
        # Get the successor of the predecessor, which is the successor for the key
        successor = client.get_successor()
        log(f'Found the successor for key {key} to be {successor.ip}:{successor.port} ({successor.id}).', self.node_info)
        transport.close()
        return successor

    def get_predecessor(self) -> NodeInfo:
        return self.predecessor

    def get_successor(self) -> NodeInfo:
        return self.finger_table[0]

    def update_predecessor(self, new_predecessor: NodeInfo) -> None:
        log(f'Updating predecessor from {self.predecessor.id} to {new_predecessor.id}.', self.node_info)
        self.predecessor = new_predecessor

    def update_successor(self, new_successor: NodeInfo) -> None:
        log(f'Updating successor from {self.finger_table[0].id} to {new_successor.id}', self.node_info)
        self.finger_table[0] = new_successor

    def update_finger_table(self, new_node: NodeInfo, index: int) -> None:
        # The finger table should be updated only if the new node id is in the range (curr, ft[i])
        if self.node_info.id == new_node.id or self.finger_table[index].id == new_node.id or not inrange(self.node_info.id, self.finger_table[index].id, new_node.id):
            return
        log(f'Updating finger table entry {index + 1} from {self.finger_table[index].id} to {new_node.id}', self.node_info)
        self.finger_table[index] = new_node
        log(f'Finger table updated to: {str(self.get_pretty_finger_table())}', self.node_info)
        # If the predecessor is not the joining node, forward the update to the predecessor
        if self.predecessor != new_node:
            client, transport = connect(self.predecessor)
            transport.open()
            client.update_finger_table(new_node, index)
            transport.close()

    def get_pretty_finger_table(self):
        return [f'({(self.node_info.id + 2 ** i) % (2 ** self.num_bits)},{e.id})' for i, e in enumerate(self.finger_table)]

def connect(node_info: NodeInfo) -> Tuple[ChordNodeService.Client, TSocket.TSocket]:
    transport = TSocket.TSocket(node_info.ip, node_info.port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ChordNodeService.Client(protocol)
    return client, transport


def get_join_node(super_node_ip: str, super_node_port: int, node_info: NodeInfo, sleep_delay: int) -> NodeInfo:
    transport = TSocket.TSocket(super_node_ip, super_node_port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = SuperNodeService.Client(protocol)
    transport.open()
    # Loop until a join node is returned from the super node
    while True:
        try:
            log('Requesting a join node from super node.', node_info)
            join_node = client.get_join_node(node_info.ip, node_info.port)
            log('Successfully received a join node from super node.', node_info)
            transport.close()
            return join_node
        except DHTBusy as e:
            log('The DHT is busy, sleeping...', node_info)
            time.sleep(sleep_delay)
    

def post_join(super_node_ip: str, super_node_port: int):
    # Notify the super node when the current node has finished joining the DHT
    transport = TSocket.TSocket(super_node_ip, super_node_port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = SuperNodeService.Client(protocol)
    transport.open()
    client.post_join()
    transport.close()


def init_server(handler: ChordNodeHandler, port: int) -> TServer.TThreadedServer:
    # Initialize the chord node RPC server
    processor = ChordNodeService.Processor(handler)
    transport = TSocket.TServerSocket(port=port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    return server

def init_chord_node(super_node_ip: str, super_node_port: int, node_ip: str, node_port: int, sleep_delay: int, num_bits: int, caching: bool):
    # Initialize the node info and get the join node from the super node
    node_info = NodeInfo(hash(f'{node_ip}:{node_port}', num_bits), node_ip, node_port)
    join_node = get_join_node(super_node_ip, super_node_port, node_info, sleep_delay)
    if len(join_node.ip) > 0:
        # If the join node ip is not empty, connect to it
        join_client, join_transport = connect(join_node)
        join_transport.open()
        # Find the predecessor of the node id
        predecessor = join_client.find_predecessor(node_info.id)
        finger_table = [None] * num_bits
        # Find the successor of the node id and set it as the first finger table entry (the successor)
        finger_table[0] = join_client.find_successor(node_info.id)
        # Loop to initialize the finger table, see the original chord paper for details
        for i in range(num_bits - 1):
            # Key to find the successor for (n + 2 ^ i)
            finger_succ = (node_info.id + 2 ** (i + 1)) % (2 ** num_bits)
            # If n + 2 ^ i is in the range (pred, curr] then set the finger table entry to the current node
            if inrange(predecessor.id, node_info.id, finger_succ) and finger_succ != predecessor.id:
                finger_table[i + 1] = node_info
            # If n + 2 ^ i is in the range [curr, f[i]) then the successor is still f[i]
            elif inrange(node_info.id, finger_table[i].id, finger_succ) and finger_succ != finger_table[i].id:
                finger_table[i + 1] = finger_table[i]
            # If above two cases don't hold, call the join client to get the successor
            else:
                finger_table[i + 1] = join_client.find_successor(finger_succ)
        join_transport.close()
        # Connect to the successor and update its predecessor
        succ_client, succ_transport = connect(finger_table[0])
        succ_transport.open()
        succ_client.update_predecessor(node_info)
        succ_transport.close()
        # Connect to the predecessor and update its successor
        pred_client, pred_transport = connect(predecessor)
        pred_transport.open()
        pred_client.update_successor(node_info)
        pred_transport.close()
        # Initialize the chord node handler
        node_handler = ChordNodeHandler(node_info, predecessor, finger_table, num_bits, caching)
        log(f'Finger table initialized to {node_handler.get_pretty_finger_table()}.', node_handler.node_info)
        # Loop to update the finger tables of other nodes
        for i in range(num_bits):
            # Want to update pred(n - 2 ^ i + 1) for potential finger table updates
            update_id = (node_info.id - (2 ** i) + 1 + 2 ** num_bits) % (2 ** num_bits)
            update_node = node_handler.find_predecessor(update_id)
            # If the node to be updated isn't the current node, send the update
            if update_node != node_info:
                update_client, update_transport = connect(update_node)
                update_transport.open()
                update_client.update_finger_table(node_info, i)
                update_transport.close()
    else:
        # If the DHT is empty, create the initial chord node
        log('DHT is empty, initializing first node.', node_info)
        node_handler = ChordNodeHandler(node_info, node_info, [node_info] * num_bits, num_bits, caching)
    # Initialize and start the chord node server
    server = init_server(node_handler, node_port)
    log(f'Initialized chord node server...', node_info)
    return server


def start_server(server):
    server.serve()


def log(message, node_info: NodeInfo):
    if DEBUG:
        print(f'[Chord Node {node_info.id}] {message}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('[Chord Node] Insufficient number of arguments.')
    # Extract the node number and load the config
    node_num = int(sys.argv[1])
    config_file = 'config.json'
    if len(sys.argv) > 2:
        config_file = sys.argv[2]
    config = load_config(config_file)

    # Extract relevant config values
    super_node_ip = config['super_node']['ip']
    super_node_port = config['super_node']['port']
    node_ip = config['chord_nodes'][node_num]['ip']
    node_port = config['chord_nodes'][node_num]['port']
    sleep_delay = config['sleep_delay']
    num_bits = config['num_bits']
    caching = config['caching']
    global DEBUG
    DEBUG = config['debug']

    if super_node_ip is None:
        print('[Chord Node] Error, supernode ip was not provided.')
    elif super_node_port is None:
        print('[Chord Node] Error, supernode port was not provided.')
    else:
        # Initailze the chord node and start the RPC server
        chord_server = init_chord_node(super_node_ip, super_node_port, node_ip, node_port, sleep_delay, num_bits, caching)
        chord_thread = Thread(target=start_server, args=(chord_server,))
        chord_thread.start()
        post_join(super_node_ip, super_node_port)
        chord_thread.join()      
  