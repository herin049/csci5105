import sys
import random
import time
from typing import Tuple

from thrift.transport import TSocket
from thrift.protocol import TBinaryProtocol

from gen.service import ServerService
from gen.service.ttypes import FileNotFound

from utils import load_config

def log_client(message: str) -> None:
    print(f'[Client {client_num}] {message}')

def connect_server(host: str, port: int) -> Tuple[ServerService.Client, TSocket.TSocket]:
    transport = TSocket.TSocket(host, port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ServerService.Client(protocol)
    return client, transport

def main():
    global client_num
    if len(sys.argv) < 2:
        print('[Client] Insufficient number of arguments.')
        return
    client_num = int(sys.argv[1])
    config_file = 'config.json'
    if len(sys.argv) > 2:
        config_file = sys.argv[2]
    
    config = load_config(config_file)
    servers = [(s['host'], s['port']) for s in config['servers']]
    commands_file = config['clients'][client_num]['commands_file']

    with open(commands_file) as file:
        lines = [line.rstrip() for line in file]
        start = time.time()
        for line in lines:
            if len(line) == 0:
                continue
            parts = line.strip().split(' ', 2)
            if len(parts) == 0:
                log_client(f'Unknown command: {line}')
            elif parts[0] == 'write' and len(parts) >= 3:
                server = random.choice(servers)
                client, transport = connect_server(server[0], server[1])
                transport.open()
                try:
                    client.write(parts[1], parts[2])
                    log_client(f'Wrote "{parts[2]}" to file "{parts[1]}".')
                finally:
                    transport.close()
            elif parts[0] == 'read' and len(parts) >= 2:
                server = random.choice(servers)
                client, transport = connect_server(server[0], server[1])
                transport.open()
                try:
                    content = client.read(parts[1])
                    log_client(f'File "{parts[1]}" has content: "{content}".')
                except FileNotFound as _:
                    log_client(f'Could not find file: "{parts[1]}".')
                finally:
                    transport.close()
            elif parts[0] == 'sleep' and len(parts) >= 2:
                log_client(f'Sleeping for {parts[1]} seconds.')
                time.sleep(float(parts[1]))
            elif parts[0] == 'list':
                server = random.choice(servers)
                client, transport = connect_server(server[0], server[1])
                transport.open()
                try:
                    files = client.list_files()
                    log_client(f'Current files with versions are: {[(f.file_name, f.version) for f in files]}.')
                finally:
                    transport.close()
            else:
                log_client(f'Unknown command: {line}')
        end = time.time()
        log_client(f'Finished executing all commands in {end - start} seconds.')

if __name__ == '__main__':
    main()