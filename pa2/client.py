import os
import sys
import glob

# Load the thrift library
THRIFT_LIB_PATH = os.getenv('THRIFT_LIB_PATH')
if THRIFT_LIB_PATH is not None:
    sys.path.insert(0, glob.glob(THRIFT_LIB_PATH)[0])

DEBUG = False

import time

from utils import load_config

from gen.service import SuperNodeService, ChordNodeService

from thrift.transport import TSocket
from thrift.protocol import TBinaryProtocol


def log(message):
    if DEBUG:
        print(f'[Client] {message}')

if __name__ == '__main__':
    config_file = 'config.json'
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    config = load_config(config_file)
    
    super_node_ip = config['super_node']['ip']
    super_node_port = config['super_node']['port']
    commands = config['client_commands']
    DEBUG = config['debug']

    log(f'Connecting to the super node.')
    super_transport = TSocket.TSocket(super_node_ip, super_node_port)
    super_protocol = TBinaryProtocol.TBinaryProtocol(super_transport)
    super_client = SuperNodeService.Client(super_protocol)
    super_transport.open()
    chord_node = super_client.get_node_for_client()
    super_transport.close()
    
    log(f'Connecting to chord node {chord_node.id} with address {chord_node.ip}:{chord_node.port}.')
    chord_transport = TSocket.TSocket(chord_node.ip, chord_node.port)
    chord_protocol = TBinaryProtocol.TBinaryProtocol(chord_transport)
    chord_client = ChordNodeService.Client(chord_protocol)
    chord_transport.open()
    
    start = time.time()
    for c in commands:
        parts = c.split(' ')
        command = parts[0]
        word = parts[1]
        if command == 'put':
            definition = parts[2]
            log(f'Inserting word "{word}" with definition "{definition}" into the DHT.')
            chord_client.put(word, definition)
        elif command == 'get':
            log(f'Retrieving definition for word "{word}" from the DHT.')
            definition = chord_client.get(word)
            log(f'Word "{word}" has definition: "{definition}".')
        else:
            log(f'Unknown command.')
    end = time.time()
    duration = end - start
    log(f'Finished executing {len(commands)} commands in {duration} seconds.')
    chord_transport.close()
