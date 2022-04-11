
import sys
import os
from typing import List, Tuple
from random import sample
from threading import Lock, Condition
from pathlib import Path

from gen.service import CoordinatorService, ServerService
from gen.service.ttypes import FileNotFound

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from utils import load_config


def log_server(message: str) -> None:
    if DEBUG:
        print(f'[Server] ({HOST}-{SERVER_NUM}): {message}')


def log_coordinator(message: str) -> None:
    if DEBUG:
        print(f'[Coordinator] ({HOST}-{SERVER_NUM}): {message}')


def connect_server(host: str, port: int) -> Tuple[ServerService.Client, TSocket.TSocket]:
    transport = TSocket.TSocket(host, port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = ServerService.Client(protocol)
    return client, transport


def connect_coordinator(host: str, port: int) -> Tuple[CoordinatorService.Client, TSocket.TSocket]:
    transport = TSocket.TSocket(host, port)
    protocol = TBinaryProtocol.TBinaryProtocol(transport)
    client = CoordinatorService.Client(protocol)
    return client, transport


class StandardLock:
    def __init__(self):
        self.lock = Lock()

    def acquire_read(self):
        self.lock.acquire()

    def release_read(self):
        self.lock.release()

    def acquire_write(self):
        self.lock.acquire()
    
    def release_write(self):
        self.lock.acquire()


class ReadWriteLock:
    def __init__(self):
        self.cv = Condition(Lock())
        self.readers = 0

    def acquire_read(self):
        with self.cv: 
            self.readers += 1

    def release_read(self):
        with self.cv:
            self.readers -= 1
            if self.readers == 0:
                self.cv.notify()

    def acquire_write(self):
        self.cv.acquire()
        self.cv.wait_for(lambda: self.readers > 0)

    def release_write(self):
        self.cv.release()


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
        finally:
            file_lock.realse_write()

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


class ServerHandler:
    def __init__(self, server_num: int, coordinator_host: str, coordinator_port: int, storage_path: str):
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
        self.storage_path = os.path.join(storage_path, str(server_num))
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


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('[Server] Insufficient number of arguments.')
    SERVER_NUM = int(sys.argv[1])
    config_file = 'config.json'
    if len(sys.argv) > 2:
        config_file = sys.argv[2]
    config = load_config(config_file)

    DEBUG = config['debug']
    server_info = config['servers'][SERVER_NUM]
    HOST = server_info['host']
    is_coordinator = server_info.get('coordinator', False)
    storage_path = server_info['storage_path']
    locking_scheme = config.get('locking_scheme', 'default')

    Path(storage_path).mkdir(parents=True, exist_ok=True)


    if is_coordinator:
        log_coordinator('Initializing coordinator handler...')
            
