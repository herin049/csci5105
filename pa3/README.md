# System Design

For this programming project, the functionality of the system is made up of three major entities: the client, the server and the coordinator.

The system is implemented in Python and makes use of the [Apache Thrift](https://thrift.apache.org/) RPC library for communication between nodes in the system. The source for the client can be found in the `client.py` and `client_interactive.py` files. Likewise, the source for the server/coordinator nodes can be found in the `server.py` file. The Thrift object for the system are defined in the `service.thrift` file. 

The goal of this project is to build a simple distributed file system capable of sharing several files between multiple clients replicated to several servers to increased performance and reliability. In order to achieve this goal, Gifford's Quorum-Based Protocol will be used to ensure that read and write operations to the same file are serialized in order to achieve sequential consistency. If we let N<sub>r</sub> and N<sub>w</sub> denote the size of each read and write quorum in the system (i.e. how many servers must a client receive approval from before performing a read or write operation), then if N is the total number of nodes in the system, Gifford's Quorum-Based Protocol requires that

1. N<sub>r</sub> + N<sub>w</sub> > N
2. N<sub>w</sub> > N / 2

The first requirement ensures that there are no read-write conflicts. Furthermore, it also ensures that at least one node in any read quorum contains the most up-to-date version of a given object. Likewise, the second requirement ensures that there are no write-write conflicts. With Gifford's Quorum-Based Protocol, the system can be implemented by first forming a collection of N servers and designating one of these servers to the coordinator. When a client wishes to perform a read/write operation, it will then be able to contact an arbitrary server which will forward its request to the coordinator. From here, the coordinator will form a read/write quorum to successfully perform the operation and return the result back to the client. 


The implementation for a server which is not designated as a coordinator is very straightfroward since most of the logic for Gifford's Quorum-Based Protocol is handled by the coordinator. Each server implements the `ServerService` Thrift service which exposes functions for the client for reading, writing and listing files in the system as well as function for the coordinator for updating, reading and retrieving versions for different files. When a regular server node recieves a request to read, write or list files in the system, it simply forwards the request to the coordinator server. Internally, each server contains a table which contains all the files and their associated versions that are currently located on the given server. When a server receives a request from the coordinator to retrieve all of the files on the server and their versions, the server simply returns every file and its version present in its file version table. Getting the content for the current version of a file is also very simple and simply involves reading the file in the server's storage path and sending back the content to the coordinator. Likewise, updating the content and version for a file simply involves writing the new content provided to the associated file and incrementing the version number. 

The implementation for the coordinator server is slightly more complicated and involves ensuring the Gifford's Quorum-Based Protocol is followed correctly. Because each coordinator is also a regular server, the coordinator also has a server handler which handles all requests made through the `ServerService` interface. Each coordinator also implements the `CoordinatorService` Thrift service which exposes functions to the other servers for reading, writing and listing files in the system. The coordinator server internally has a table containing a lock for each file in the system. When the coordinator receives a request to read from a file, it first acquires the corresponding lock for the file. Next, it forms a read quourum with size N<sub>r</sub> which is specified in the configuration file. It then contacts all of the servers in this write quorum and retrieves the contents of the file from the server with the highest version number, forwaring the result back to the caller. Finally, it releases the lock for the file so that other operations can be performed on this file. Handling a write request is analogous to handling a read request with the exception that the coordinator first finds the server with the highest version number and increments it by one. Then, it makes a request to each server in the write quourum to update the version and content of the file accordingly. Hnadling a request to retrieve all the file and their associated versions is slightly different. First, the coordinator acquires the file table lock to ensure that no new files are created or modified while retrieving all the files in the system. Next, the coordinator forms a read quorum and contacts each server requesting all of its files and associated versions. The coordinator then returns a list of all files returned from the servers in the read quorum with the version number for each file being the maximum version number for the given file.

As mentioned earlier, there are the `client.py` and `client_interactive.py` files for the client. Both files are identical in functionality except that the `client.py` file executes commands provided in the configuration file and the `client_interactive.py` executes commands typed in manually by the user. The former file is used by the `run.py` script while the latter one is useful for manual testing. The client supports 4 different commands. The `write` command accepts two arguments: the name of the file to write to and the new contents of the corresponding file. For example, `write myfile.txt hello` will write the contents "hello" to the file `myfile.txt`. Analogously the `read` commands accepts a single argument which is the name of the file to read. For example, `read myfile.txt` will read the contents of `myfile.txt` and print the output in console. The `list` command accept no arguments and simply outputs the list of files on the system and their associated version numbers in console. Finally, the `sleep` command accepts a single argument which determine the amount of time the client should sleep for. This command is obviously not present in the interactive client for it is only useful for automated testing. For example, `sleep 3` will make the client sleep for 3 seconds before executing the next command. 

# Operation & Usage

To run the system, start by initializing a python virtual environment by running 
```bash
source create-env.sh
```
in the root directory of the project. Alternatively, one can create the Python virtual environment by running
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Next, one needs to generate the required Thrift files by either running
```bash
source thrift-gen.sh
```
or by running
```bash
mkdir -p gen
thrift -r --gen py -out gen service.thrift
```

After creating the virtual environment and generating the Thrift files, the system can be ran by running
```
python run.py <clients|servers|all> <config file>
```
Specifying `clients` as the first argument will just start the clients provided in the configuration file and specifying `servers` as the first argument will just start the servers provided in the configuration file. Likewise, specifying `all` as the first argument will start both the clients and servers. If a configuration file is not passed to `run.py` then the default configuration file `config.json` will be used. 

Below is an example configuration file for the system
```json
{
    "debug": true,
    "q_write": 4,
    "q_read": 4,
    "storage_path": "file_data",
    "coordinator_port": 8080,
    "coordinator_sleep_delay": 3,
    "locking_scheme": "default",
    "servers": [
        {
            "host": "127.0.0.1",
            "port": 8081,
            "coordinator": true
        },
        {
            "host": "127.0.0.1",
            "port": 8082
        },
        {
            "host": "127.0.0.1",
            "port": 8083
        },
        {
            "host": "127.0.0.1",
            "port": 8084
        },
        {
            "host": "127.0.0.1",
            "port": 8085
        },
        {
            "host": "127.0.0.1",
            "port": 8086
        },
        {
            "host": "127.0.0.1",
            "port": 8087
        }
    ],
    "clients": [
        {
            "host": "127.0.0.1",
            "commands_file": "tests/0/commands0.txt"
        },
        {
            "host": "127.0.0.1",
            "commands_file": "tests/0/commands1.txt"
        },
        {
            "host": "127.0.0.1",
            "commands_file": "tests/0/commands2.txt"
        }
    ]
}
```

A description of the dehavior of each of the configuration options are given below.

The `debug` option prints out additional information about requests being made when set to `true`.

The `q_write` and `q_read` options specify the corresponding write and read quorum sizes. 

The `storage_path` option specifies where the servers should store their files. For example, setting `storage_path` to `file_data` means that server 3 will store its files in `./file_data/3` relative to the root project directory.

The `coordinator_port` option specifies the port that the coordinator server should listen on.

The `coordinator_sleep_delay` option specifies the amount of time that non-coordinator servers should wait before starting.

The `locking_scheme` option specifies which types of locks the coordinator should use for managing reads and writes. Setting the locking scheme to `default` means that a standard lock is used implying that concurrent reads to the same file are note allowed. However, setting the locking scheme to `readwrite` means that a read-write lock is used implying that concurrent reads to the same file are allowed, but concurrent writes are still disallowed. 

The `servers` option contains a list of server objects that each contain a `host` and `port` field. If the host is `127.0.0.1` then the `run.py` script will run the server locally by creating a new process. Otherwise, the run script will SSH into the host provided and change directories into the project directory with the user being the current user running the script. Then, the run script will activate the virtual environment and start the server remotely. If a server sets the field `coordinator` to `true` then it will act as the coordinator for the system.

The `clients` option contains a list of client objects that each contain a `host` and `commands_file` field. If the host is `127.0.0.1` then the `run.py` script will run the client locally by creating a new process.  Otherwise, the run script will SSH into the host provided and change directories into the project directory with the user being the current user running the script. Then, the run script will activate the virtual environment and start the client remotely. If `commands_file` must refer to a file with contains a list of client commands. An example commands file can be see in `tests/0/commands0.txt`.

It is important to note that the `run.py` script should always be ran in the root of the project directory. Furthermore, the contents in the project directory path should be identical across all node servers to ensure that each node has the same Python files and configuration files. Likewise, it is also important that the Python virtual environment is present in the `venv` folder and the thrift files should be generated into the `gen` folder. 

# Test Cases & Expected Output

# Performance Analysis
