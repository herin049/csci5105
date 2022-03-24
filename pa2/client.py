import os
import sys
import glob

# Load the thrift library
THRIFT_LIB_PATH = os.getenv('THRIFT_LIB_PATH')
if THRIFT_LIB_PATH is not None:
    sys.path.insert(0, glob.glob(THRIFT_LIB_PATH)[0])

DEBUG = False

from gen.service import SuperNodeService, ChordNodeService

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

def log(message):
    if DEBUG:
        print(f'[Client] {message}')

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('[Client] Insufficient number of arguments.')
    super_node_ip = sys.argv[1].split(':')[0]
    super_node_port = int(sys.argv[1].split(':')[1])
    commands_file = sys.argv[2]
    DEBUG = int(sys.argv[3]) > 0

    with open(commands_file) as f:
        commands = list(map(lambda l: l.split(' '), f.read().splitlines()))

    super_transport = TSocket.TSocket(super_node_ip, super_node_port)
    super_protocol = TBinaryProtocol.TBinaryProtocol(super_transport)
    super_client = SuperNodeService.Client(super_protocol)
    super_transport.open()
    chord_node = super_client.get_node_for_client()
    super_transport.close()

    chord_transport = TSocket.TSocket(chord_node.ip, chord_node.port)
    chord_protocol = TBinaryProtocol.TBinaryProtocol(chord_transport)
    chord_client = ChordNodeService.Client(chord_protocol)
    chord_transport.open()
    
    for c in commands:
        command = c[0]
        word = c[1]
        if command == 'put':
            definition = c[2]
            log(f'Inserting word "{word}" with definition "{definition}"')
            chord_client.put(word, definition)
        elif command == 'get':
            log(f'Retrieving definition for word "{word}"')
            definition = chord_client.get(word)
            log(f'Word "{word}" has definition "{definition}"')
        else:
            log(f'Unknown command.')

    chord_transport.close()
