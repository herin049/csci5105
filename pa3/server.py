
import sys
import os
import time
from typing import List, Tuple
from random import sample
from threading import Lock, Thread
from pathlib import Path

from gen.service import CoordinatorService, ServerService
from gen.service.ttypes import FileNotFound, FileObject

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from utils import load_config
from locks import ReadWriteLock, StandardLock

def log_server(message: str) -> None:
    if DEBUG:
        print(f'[Server {server_num}] ({host}): {message}')


def log_coordinator(message: str) -> None:
    if DEBUG:
        print(f'[Coordinator] ({host}): {message}')


def connect_server(host: str, port: int) -> Tuple[ServerService.Client, TSocket.TSocket]:
    transport = TSocket.TSocket(host=host, port=port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ServerService.Client(protocol)
    return client, transport


def connect_coordinator(host: str, port: int) -> Tuple[CoordinatorService.Client, TSocket.TSocket]:
    transport = TSocket.TSocket(host=host, port=port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = CoordinatorService.Client(protocol)
    return client, transport


class CoordinatorHandler:
    def __init__(self, q_write: int, q_read: int, servers: List, locking_scheme: str):
        self.q_write = q_write
        self.q_read = q_read
        self.locking_scheme = locking_scheme
        self.servers = servers
        self.file_table = {}
        self.file_table_lock = Lock()

    def get_file_lock(self, file_name: str):
        with self.file_table_lock:
            if file_name in self.file_table:
                file_lock = self.file_table[file_name]
            else:
                file_lock = self.file_table[file_name] = ReadWriteLock() if self.locking_scheme == 'readwrite' else StandardLock()
            return file_lock

    def write(self, file_name: str, content: str) -> None:
        log_coordinator(f'Received request to write "{content}" to "{file_name}".')
        file_lock = self.get_file_lock(file_name)
        file_lock.acquire_write()
        log_coordinator(f'Successfully acquired file lock.')
        try:
            version = 0
            write_quorum = sample(self.servers, self.q_write)
            log_coordinator(f'Formed write quorum consisting of servers: {write_quorum}.')
            for server in write_quorum:
                host, port = server
                client, transport = connect_server(host, port)
                transport.open()
                server_version = client.get_version(file_name)
                log_coordinator(f'Server {host}:{port} has version {server_version} for file "{file_name}".')
                version = max(client.get_version(file_name), version)
                transport.close()
            log_coordinator(f'The version for file "{file_name}" is {version}.')
            version += 1
            log_coordinator(f'Updating file contents across all servers in write quorum.')
            for server in write_quorum:
                host, port = server
                client, transport = connect_server(host, port)
                transport.open()
                client.update(file_name, version, content)
                transport.close()
            log_coordinator(f'Finished writing to "{file_name}".')
            return
        finally:
            file_lock.release_write()

    def read(self, file_name: str) -> str:
        log_coordinator(f'Received request to read contents from "{file_name}".')
        file_lock = self.get_file_lock(file_name)
        file_lock.acquire_read()
        try:
            version = 0
            read_server = None
            read_quorum = sample(self.servers, self.q_read)
            log_coordinator(f'Formed read quorum consisting of servers: {read_quorum}.')
            for server in read_quorum:
                host, port = server
                client, transport = connect_server(host, port)
                transport.open()
                server_version = client.get_version(file_name)
                log_coordinator(f'Server {host}:{port} has version {server_version} for file "{file_name}".')
                transport.close()
                if server_version > version:
                    read_server = server
                    version = server_version
            if read_server is None:
                log_coordinator('No server was found to have a file version number greater than 0.')
                raise FileNotFound()
            read_host, read_port = read_server
            log_coordinator(f'Server {read_host}:{read_port} has the highest version ({version}) for file "{file_name}".')
            read_client, read_transport = connect_server(read_host, read_port)
            read_transport.open()
            file_content = read_client.fetch(file_name)
            read_transport.close()
            log_coordinator(f'The contents for file "{file_name}" are "{file_content}".')
            return file_content
        finally:
            file_lock.release_read()

    def list_files(self) -> List[FileObject]:
        log_coordinator(f'Received request to list all files and versions.')
        with self.file_table_lock:
            acquired_locks = []
            try:
                for _, lock in self.file_table.items():
                    lock.acquire_read()
                    acquired_locks.append(lock)
                file_versions = {}
                read_quorum = sample(self.servers, self.q_read)
                log_coordinator(f'Formed read quorum consisting of servers: {read_quorum}.')
                for server in read_quorum:
                    host, port = server
                    client, transport = connect_server(host, port)
                    transport.open()
                    files = client.get_files()
                    log_coordinator(f'Server {host}:{port} has files with associated versions: {files}.')
                    transport.close()
                    for f in files:
                        if f.version > file_versions.get(f.file_name, 0):
                            file_versions[f.file_name] = f.version
                log_coordinator(f'Found files and associated versions to be: {file_versions}')
                return [FileObject(f, v) for f, v in file_versions.items()]
            finally:
                for lock in acquired_locks:
                    lock.release_read()


class ServerHandler:
    def __init__(self, coordinator_host: str, coordinator_port: int, storage_path: str):
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
        self.storage_path = storage_path
        self.version_table = {}
        self.version_table_lock = Lock()

    def write(self, file_name: str, content: str) -> None:
        log_server(f'Received request to write "{content}" to "{file_name}".')
        client, transport = connect_coordinator(self.coordinator_host, self.coordinator_port)
        transport.open()
        client.write(file_name, content)
        transport.close()
        log_server(f'Coordinator finished processing request to write to "{file_name}".')

    def read(self, file_name: str) -> str:
        log_server(f'Received request to read contents from "{file_name}".')
        client, transport = connect_coordinator(self.coordinator_host, self.coordinator_port)
        transport.open()
        content = client.read(file_name)
        transport.close()
        log_server(f'Coordinator finished processing request to read from "{file_name}".')
        return content

    def list_files(self) -> List[FileObject]:
        log_server('Received request to list all files and versions.')
        log_server(f'{self.coordinator_host} {self.coordinator_port}')
        client, transport = connect_coordinator(self.coordinator_host, self.coordinator_port)
        transport.open()    
        files = client.list_files()
        transport.close()
        log_server(f'Coordinator finished processing request to list all files and versions.')
        return files

    def get_files(self) -> List[FileObject]:
        log_server('Received request to retrieve all files and current versions.')
        with self.version_table_lock:
            return [FileObject(f, v) for f, v in self.version_table.items()]

    def get_version(self, file_name: str) -> int:
        with self.version_table_lock:
            return self.version_table.get(file_name, 0)

    def update(self, file_name: str, version: int, content: str) -> None:
        log_server(f'Updating contents of file "{file_name}" to "{content}".')
        Path(os.path.join(self.storage_path, file_name)).write_text(content)
        with self.version_table_lock:
            log_server(f'Updating version for file "{file_name}" from {self.version_table.get(file_name, 0)} to {version}.')
            self.version_table[file_name] = version

    def fetch(self, file_name: str) -> str:
        log_server(f'Fetching contents of "{file_name}" for coordinator.')
        with self.version_table_lock:
            if file_name not in self.version_table:
                raise FileNotFound()
        return Path(os.path.join(self.storage_path, file_name)).read_text()


def start_coordinator(coordinator_port: int, q_write: int, q_read: int, servers: List, locking_scheme: str):
    coordinator_handler = CoordinatorHandler(q_write, q_read, servers, locking_scheme)
    processor = CoordinatorService.Processor(coordinator_handler)
    transport = TSocket.TServerSocket(port=coordinator_port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    log_coordinator('Starting coordinator...')
    server.serve()
    log_coordinator('Done.')


def start_server(server_port: int, coordinator_host: str, coordinator_port: int, storage_path: str):
    server_handler = ServerHandler(coordinator_host, coordinator_port, storage_path)
    processor = ServerService.Processor(server_handler)
    transport = TSocket.TServerSocket(port=server_port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    log_server('Starting server...')
    server.serve()
    log_server('Done.')

def main():
    global DEBUG, host, server_num
    if len(sys.argv) < 2:
        print('[Server] Insufficient number of arguments.')
        return
    server_num = int(sys.argv[1])
    config_file = 'config.json'
    if len(sys.argv) > 2:
        config_file = sys.argv[2]
    config = load_config(config_file)
    DEBUG = config.get('debug', True)
    q_write = config['q_write']
    q_read = config['q_read']
    storage_path = os.path.join(config['storage_path'], str(server_num))
    coordinator_port = config.get('coordinator_port', 8080)
    coordinator_sleep_delay = config.get('coordinator_sleep_delay', 3)
    locking_scheme = config.get('locking_scheme', 'default')

    server_info = config['servers'][server_num]
    host = server_info['host']
    port = server_info['port']
    is_coordinator = server_info.get('coordinator', False)
    coordinator_host = next((s['host'] for s in config['servers'] if s.get('coordinator', False)), None)
    if coordinator_host is None:
        print('[Server] Error, coordinator not provided in configuration file.')
        return

    Path(storage_path).mkdir(parents=True, exist_ok=True)

    coordinator_thread = None
    if is_coordinator:
        log_coordinator('Initializing coordinator handler...')
        servers = [(s['host'], s['port']) for s in config['servers']]
        coordinator_thread = Thread(target=start_coordinator, args=(coordinator_port, q_write, q_read, servers, locking_scheme,))
        coordinator_thread.start()
    else:
        time.sleep(coordinator_sleep_delay)

    start_server(port, coordinator_host, coordinator_port, storage_path)
    coordinator_thread.join()


if __name__ == '__main__':
    main()
