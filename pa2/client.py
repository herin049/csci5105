import sys
import time
from utils import load_config

from gen.service import SuperNodeService, ChordNodeService
from gen.service.ttypes import DuplicateWord, WordNotFound

def log(message):
    if DEBUG:
        print(f'[Client] {message}')

if __name__ == '__main__':
    # Load the config file
    config_file = 'config.json'
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    config = load_config(config_file)
    
    from thrift.transport import TSocket
    from thrift.protocol import TBinaryProtocol

    # Extract information from the config
    reuse_connection = config['reuse_connection']
    super_node_ip = config['super_node']['ip']
    super_node_port = config['super_node']['port']
    commands = config['client_commands']
    global DEBUG
    DEBUG = config['debug']

    # Connect to the super node
    log(f'Connecting to the super node.')
    super_transport = TSocket.TSocket(super_node_ip, super_node_port)
    super_protocol = TBinaryProtocol.TBinaryProtocol(super_transport)
    super_client = SuperNodeService.Client(super_protocol)
    super_transport.open()

    chord_node = super_client.get_node_for_client()
    
    # Connect to the chord node returned from the super node
    log(f'Connecting to chord node {chord_node.id} with address {chord_node.ip}:{chord_node.port}.')
    chord_transport = TSocket.TSocket(chord_node.ip, chord_node.port)
    chord_protocol = TBinaryProtocol.TBinaryProtocol(chord_transport)
    chord_client = ChordNodeService.Client(chord_protocol)
    chord_transport.open()
    
    # Function to reconnect to a new chord node if not reusing connections
    def reconnect():
        global chord_transport, chord_protocol, chord_client, chord_transport
        chord_transport.close()
        chord_node = super_client.get_node_for_client()
        chord_transport = TSocket.TSocket(chord_node.ip, chord_node.port)
        chord_protocol = TBinaryProtocol.TBinaryProtocol(chord_transport)
        chord_client = ChordNodeService.Client(chord_protocol)
        chord_transport.open()
        return

    # Execute each command provided in the config
    start = time.time()
    for c in commands:
        parts = c.split(' ')
        command = parts[0]
        word = parts[1]
        if command == 'put':
            # Insert a word into the DHT
            definition = parts[2]
            log(f'Inserting word "{word}" with definition "{definition}" into the DHT.')
            try:
                if not reuse_connection:
                    reconnect()
                chord_client.put(word, definition)
            except DuplicateWord as e:
                log(f'Error, word "{word}" is already in the DHT.')
        elif command == 'get':
            # Retrieve a definition for a word from the DHT
            log(f'Retrieving definition for word "{word}" from the DHT.')
            try:
                if not reuse_connection:
                    reconnect()
                definition = chord_client.get(word)
                log(f'Word "{word}" has definition: "{definition}".')
            except WordNotFound as e:
                log(f'Word "{word}" has no definition associated to it.')
        elif command == 'store':
            # Store the contents of a dictionary file into the DHT
            file_name = parts[1]
            log(f'Storing dictionary file "{file_name}".')
            with open(file_name, 'r') as file:
                lines = file.read().splitlines()
                for word, definition in zip(lines[0::2], lines[1::2]):
                    if len(word) > 0 and len(definition) > 0:
                        seperator_pos = definition.find(':')
                        if seperator_pos == -1:
                            continue
                        definition_text = definition[(seperator_pos + 1):].strip()
                        log(f'Inserting word "{word}" with definition "{definition_text}" into the DHT.')
                        try:
                            if not reuse_connection:
                                reconnect()
                            chord_client.put(word, definition_text)
                        except DuplicateWord as e:
                            log(f'Error, word "{word}" is already in the DHT.')
            log(f'Finished storing contents of dictionary file.')
        elif command == 'load':
            # Load the definitions from a word list from the DHT
            file_name = parts[1]
            dest_file_name = parts[2] if len(parts) > 2 else None
            definitions = []
            lines = []
            log(f'Loading definitions from word list file "{file_name}".')
            with open(file_name, 'r') as file:
                lines = file.read().splitlines()
                for word in lines:
                    if len(word) > 0:
                        try:
                            if not reuse_connection:
                                reconnect()
                            definition_text = chord_client.get(word)
                            log(f'Word "{word}" has definition: "{definition_text}".')
                            definitions.append(definition_text)
                        except WordNotFound as e:
                            log(f'Word "{word}" has no definition associated to it.')
                            definitions.append('')
                    else:
                        definitions.append('')
            log(f'Finished loading definitions from word list file "{file_name}".')
            if dest_file_name is not None:
                log(f'Writing loaded definitions to destination file "{dest_file_name}".')
                with open(dest_file_name, 'w') as file:
                    for word, definition in zip(lines, definitions):
                        file.write(f'{word}\n Defn: {definition}\n')
        else:
            log(f'Unknown command.')
    end = time.time()
    duration = end - start
    # Log the execution time in seconds
    log(f'Finished executing {len(commands)} commands in {duration} seconds.')
    chord_transport.close()
    super_transport.close()

