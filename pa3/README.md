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

In the `tests` directory there are several sub-directories labeled `0-6` that each contain a corresponding configuration file and commands files. To run the system with any of these configuration files, simply provide the location to the configuration file as the seocnd argument to the run script. For example, execute `python run.py all tests/2/config.json` to run test `2`.

## Test Case 0: Basic Functionality

As an initial test case, we expect the system to function properly under very simple scenarios. Using the configuration file `tests/0/config.json` which makes the three clients execute a few simple commands, we expect that the system provides an output similar to the output below
```
Starting server 0 (127.0.0.1).
Starting server 1 (127.0.0.1).
Starting server 2 (127.0.0.1).
Starting server 3 (127.0.0.1).
Starting server 4 (127.0.0.1).
Starting server 5 (127.0.0.1).
Starting server 6 (127.0.0.1).
Waiting for servers to boot up...
[Coordinator] (127.0.0.1): Initializing coordinator handler...
[Coordinator] (127.0.0.1): Starting coordinator...
[Server 0] (127.0.0.1): Starting server...
[Server 1] (127.0.0.1): Starting server...
[Server 2] (127.0.0.1): Starting server...
[Server 3] (127.0.0.1): Starting server...
[Server 5] (127.0.0.1): Starting server...
[Server 6] (127.0.0.1): Starting server...
[Server 4] (127.0.0.1): Starting server...
Starting client 0 (127.0.0.1).
Starting client 1 (127.0.0.1).
Starting client 2 (127.0.0.1).
[Server 2] (127.0.0.1): Received request to write "bcd" to "b.txt".
[Server 3] (127.0.0.1): Received request to write "abc" to "a.txt".
[Coordinator] (127.0.0.1): Received request to write "abc" to "a.txt".
...
[Client 0] Current files with versions are: [('b.txt', 1), ('a.txt', 1), ('3.txt', 1), ('2.txt', 1), ('c.txt', 1), ('1.txt', 1)].
...
[Coordinator] (127.0.0.1): Formed read quorum consisting of servers: [('127.0.0.1', 8081), ('127.0.0.1', 8087), ('127.0.0.1', 8085), ('127.0.0.1', 8082)].
[Coordinator] (127.0.0.1): Server 127.0.0.1:8081 has version 1 for file "1.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8083 has version 1 for file "2.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8081 has version 0 for file "3.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8083 has version 0 for file "1.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8085 has version 0 for file "2.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8087 has version 0 for file "3.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8087 has version 0 for file "1.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8081 has the highest version (1) for file "1.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8081 has version 1 for file "2.txt".
[Server 0] (127.0.0.1): Fetching contents of "1.txt" for coordinator.
[Coordinator] (127.0.0.1): Server 127.0.0.1:8085 has version 0 for file "3.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8082 has version 1 for file "2.txt".
[Coordinator] (127.0.0.1): The contents for file "1.txt" are "123".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8083 has the highest version (1) for file "2.txt".
[Server 0] (127.0.0.1): Coordinator finished processing request to read from "1.txt".
[Client 0] File "1.txt" has content: "123".
[Client 0] Finished executing all commands in 0.06023573875427246 seconds.
[Coordinator] (127.0.0.1): Server 127.0.0.1:8082 has version 1 for file "3.txt".
[Server 2] (127.0.0.1): Fetching contents of "2.txt" for coordinator.
[Coordinator] (127.0.0.1): Server 127.0.0.1:8082 has the highest version (1) for file "3.txt".
[Coordinator] (127.0.0.1): The contents for file "2.txt" are "234".
[Server 1] (127.0.0.1): Fetching contents of "3.txt" for coordinator.
[Server 3] (127.0.0.1): Coordinator finished processing request to read from "2.txt".
[Client 1] File "2.txt" has content: "234".
[Client 1] Finished executing all commands in 0.06087160110473633 seconds.
[Coordinator] (127.0.0.1): The contents for file "3.txt" are "345".
[Server 1] (127.0.0.1): Coordinator finished processing request to read from "3.txt".
[Client 2] File "3.txt" has content: "345".
[Client 2] Finished executing all commands in 0.05925726890563965 seconds.
```

As we can see the system behaves as expected. Each client was able to succesfully read back the same content that they wrote to each file, e.g. Client 0 wrote "123" to `1.txt` and was able to succesfully read back "123". Likewise, the list operation also correctly lists all of the files in the system and their correct versions.

## Test Case 1: Mixed Workload

The next test case is to ensure that the system is able to handle several read/write operations at once. We expect that the clients should finish executing their operations in a reasonable amount of time and the changes should be correctly reflected on the corresponding files. Using the configuration file `tests/1/config.json` we expect an output similar to the output below

```
...
[Server 4] (127.0.0.1): Coordinator finished processing request to write to "2-2.txt".
[Server 2] (127.0.0.1): Updating contents of file "0-1.txt" to "27M8V7AM79WIC7RHA4EYLW6M3N3KXAB8139R71K3YNMMT4ITVX2KZNPOT049X0KBCI4HA02GYZ2ETR8NNTXYS6VS8M8TRAKS342I".
[Client 2] Wrote "JYG2DID5BTN9J25J0NMXFUM9M8WIK9M4YDQ16SSW9RJFRN3UAXYWTAR3NAGCIIURABV14BBGARXA8YPIW2HDUVWP4O4L15F05I4B" to file "2-2.txt".
[Client 2] Finished executing all commands in 2.4185805320739746 seconds.
[Server 2] (127.0.0.1): Updating version for file "0-1.txt" from 14 to 15.
[Coordinator] (127.0.0.1): Finished writing to "0-1.txt".
[Server 4] (127.0.0.1): Coordinator finished processing request to write to "0-1.txt".
[Client 0] Wrote "27M8V7AM79WIC7RHA4EYLW6M3N3KXAB8139R71K3YNMMT4ITVX2KZNPOT049X0KBCI4HA02GYZ2ETR8NNTXYS6VS8M8TRAKS342I" to file "0-1.txt".
[Server 4] (127.0.0.1): Received request to write "SL51WR6EGPG7F94MZM0F32WWBFIKT797IPBQOKDRILUWFM4VID7TU3CUF7LX4DB0BCZ57HKSWO0J7D94X5ZXV1ASJH96L59ZR6VZ" to "0-6.txt".
[Coordinator] (127.0.0.1): Received request to write "SL51WR6EGPG7F94MZM0F32WWBFIKT797IPBQOKDRILUWFM4VID7TU3CUF7LX4DB0BCZ57HKSWO0J7D94X5ZXV1ASJH96L59ZR6VZ" to "0-6.txt".
[Coordinator] (127.0.0.1): Successfully acquired file lock.
[Coordinator] (127.0.0.1): Formed write quorum consisting of servers: [('127.0.0.1', 8084), ('127.0.0.1', 8085), ('127.0.0.1', 8082), ('127.0.0.1', 8087)].
[Coordinator] (127.0.0.1): Server 127.0.0.1:8084 has version 9 for file "0-6.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8085 has version 7 for file "0-6.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8082 has version 8 for file "0-6.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8087 has version 9 for file "0-6.txt".
[Coordinator] (127.0.0.1): The version for file "0-6.txt" is 9.
[Coordinator] (127.0.0.1): Updating file contents across all servers in write quorum.
[Server 3] (127.0.0.1): Updating contents of file "0-6.txt" to "SL51WR6EGPG7F94MZM0F32WWBFIKT797IPBQOKDRILUWFM4VID7TU3CUF7LX4DB0BCZ57HKSWO0J7D94X5ZXV1ASJH96L59ZR6VZ".
[Server 3] (127.0.0.1): Updating version for file "0-6.txt" from 9 to 10.
[Server 4] (127.0.0.1): Updating contents of file "0-6.txt" to "SL51WR6EGPG7F94MZM0F32WWBFIKT797IPBQOKDRILUWFM4VID7TU3CUF7LX4DB0BCZ57HKSWO0J7D94X5ZXV1ASJH96L59ZR6VZ".
[Server 4] (127.0.0.1): Updating version for file "0-6.txt" from 7 to 10.
[Server 1] (127.0.0.1): Updating contents of file "0-6.txt" to "SL51WR6EGPG7F94MZM0F32WWBFIKT797IPBQOKDRILUWFM4VID7TU3CUF7LX4DB0BCZ57HKSWO0J7D94X5ZXV1ASJH96L59ZR6VZ".
[Server 1] (127.0.0.1): Updating version for file "0-6.txt" from 8 to 10.
[Server 6] (127.0.0.1): Updating contents of file "0-6.txt" to "SL51WR6EGPG7F94MZM0F32WWBFIKT797IPBQOKDRILUWFM4VID7TU3CUF7LX4DB0BCZ57HKSWO0J7D94X5ZXV1ASJH96L59ZR6VZ".
[Server 6] (127.0.0.1): Updating version for file "0-6.txt" from 9 to 10.
[Coordinator] (127.0.0.1): Finished writing to "0-6.txt".
[Server 4] (127.0.0.1): Coordinator finished processing request to write to "0-6.txt".
[Client 0] Wrote "SL51WR6EGPG7F94MZM0F32WWBFIKT797IPBQOKDRILUWFM4VID7TU3CUF7LX4DB0BCZ57HKSWO0J7D94X5ZXV1ASJH96L59ZR6VZ" to file "0-6.txt".
[Client 0] Finished executing all commands in 2.4242374897003174 seconds.
```

As we can see the system was able to handle all 630 requests from 3 clients in approximately 2.42 seconds meaing that each client was able to approximately execute 86 read/write operations per second. This result is certainly acceptable and demonstrates that the system does not have any significant performance issues. Likewise, manual verification will allow one to conclude that all files contain the correct information at all times while the system is running. For example, when Client 0 executed `write 0-9.txt QUOJOLATMOJIHN51FRNIB1R3H5KF9V62VH5FOJBE6AK90992LQVPVRS1N13Q6ZDGGJVE5A5L34SOMULEVFCU951S2YUOJFKEXYKB` followed a little while later by `read 0-9.txt`, we see that Client 0 read `QUOJOLATMOJIHN51FRNIB1R3H5KF9V62VH5FOJBE6AK90992LQVPVRS1N13Q6ZDGGJVE5A5L34SOMULEVFCU951S2YUOJFKEXYKB` which is the correct content for file `0-9.txt`.

## Test Case 2: Read Heavy Workload

The next test case is to observe the behavior of the system when approximately 80% of the operations are read operations. We expect that the clients should finish executing their operations quicker than the mixed test case because read operations are generally less expensive than write operations. Using the configuration file `tests/2/config.json` we expect an output similar to the output below

```
...
[Coordinator] (127.0.0.1): Server 127.0.0.1:8086 has version 4 for file "0-5.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8082 has the highest version (4) for file "0-5.txt".
[Server 0] (127.0.0.1): Fetching contents of "1-4.txt" for coordinator.
[Coordinator] (127.0.0.1): The contents for file "1-4.txt" are "CZUFK8Y677QOFYSKMSRUV9CFHXP0WVXP5DAE1PGM7AFLFSVV6R69TDPED94GD88YXXH4DAXLEBEO63PYG7BX699RAR1OJZYZUVVN".
[Server 1] (127.0.0.1): Fetching contents of "0-5.txt" for coordinator.
[Server 6] (127.0.0.1): Coordinator finished processing request to read from "1-4.txt".
[Client 1] File "1-4.txt" has content: "CZUFK8Y677QOFYSKMSRUV9CFHXP0WVXP5DAE1PGM7AFLFSVV6R69TDPED94GD88YXXH4DAXLEBEO63PYG7BX699RAR1OJZYZUVVN".
[Client 1] Finished executing all commands in 1.816753625869751 seconds.
[Coordinator] (127.0.0.1): The contents for file "0-5.txt" are "N1LVDVB8CE0BV1BR9TSUT25TJIL76L69VGDCRNYHVQV76HJW6NU3J65HEMUFQAHAZEZ0DIHPO0XCP26SA62KB572MXJSZPDUV2TG".
[Server 4] (127.0.0.1): Coordinator finished processing request to read from "0-5.txt".
[Client 0] File "0-5.txt" has content: "N1LVDVB8CE0BV1BR9TSUT25TJIL76L69VGDCRNYHVQV76HJW6NU3J65HEMUFQAHAZEZ0DIHPO0XCP26SA62KB572MXJSZPDUV2TG".
[Server 3] (127.0.0.1): Received request to read contents from "0-8.txt".
[Coordinator] (127.0.0.1): Received request to read contents from "0-8.txt".
[Coordinator] (127.0.0.1): Formed read quorum consisting of servers: [('127.0.0.1', 8085), ('127.0.0.1', 8087), ('127.0.0.1', 8081), ('127.0.0.1', 8083)].
[Coordinator] (127.0.0.1): Server 127.0.0.1:8085 has version 4 for file "0-8.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8087 has version 2 for file "0-8.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8081 has version 3 for file "0-8.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8083 has version 3 for file "0-8.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8085 has the highest version (4) for file "0-8.txt".
[Server 4] (127.0.0.1): Fetching contents of "0-8.txt" for coordinator.
[Coordinator] (127.0.0.1): The contents for file "0-8.txt" are "2J0HES84KRI4GLIX1O5720O0XATYLZ4QSHJ3CURLONH40BNROZUTFALMAN42HP4I5J75GPRLTCKYSAXSQIIS55P3WQ0HHUHJH1HU".
[Server 3] (127.0.0.1): Coordinator finished processing request to read from "0-8.txt".
[Client 0] File "0-8.txt" has content: "2J0HES84KRI4GLIX1O5720O0XATYLZ4QSHJ3CURLONH40BNROZUTFALMAN42HP4I5J75GPRLTCKYSAXSQIIS55P3WQ0HHUHJH1HU".
[Client 0] Finished executing all commands in 1.8191101551055908 seconds.
```
As we predicted, the read heavy workload was able to complete much faster than the mixed workload, indicating that there are no significant issues with the read operations. Likewise, manual verification will show that the contents of the files are correct for each read operation.

## Test Case 3: Write Heavy Workload

As a follow up to the read heavy workload test, it makes sense to also test the system under a write heavy workload when approximately 80% of the operations are write operations. In this test, we expect that the client should finish executing their commands in a longer amount of time compared to both the mixed and read heavy workloads because write operations are the most expensive operation in the system. Using the configuration file `tests/3/config.json` we expect an output similar to the output below

```
...
[Server 6] (127.0.0.1): Updating version for file "1-5.txt" from 12 to 13.
[Server 2] (127.0.0.1): Fetching contents of "2-1.txt" for coordinator.
[Coordinator] (127.0.0.1): The version for file "0-6.txt" is 23.
[Coordinator] (127.0.0.1): Updating file contents across all servers in write quorum.
[Coordinator] (127.0.0.1): Finished writing to "1-5.txt".
[Server 6] (127.0.0.1): Coordinator finished processing request to write to "1-5.txt".
[Client 1] Wrote "5A7NHWRBUH1BVMTJTMAKX7EDZSXKQL5JH2RGSM4HFWYBMSX9LQQOEKTVBLBQA50VM0G9BF38I3UPN3GRQIRN2QDTYXYG4ZF73764" to file "1-5.txt".
[Client 1] Finished executing all commands in 3.035496950149536 seconds.
[Coordinator] (127.0.0.1): The contents for file "2-1.txt" are "RBA5ESEOYWS745IIPY0XQK48RM43IH54K943AJ4TPP39WES3HTXNFDMQ7WCMYR5AO8PFJOR7VE878ZTF4OOVOAITY54NZROV9F51".
[Server 0] (127.0.0.1): Coordinator finished processing request to read from "2-1.txt".
[Server 5] (127.0.0.1): Updating contents of file "0-6.txt" to "8QONI90O3PIW7D43TP4VRGPCMYYNQS0CJQMUO0QHY1VBWQUX1JI9TYG68UJWAB9RGB58QWNWOGLL4GFOPL82X2JUPOUSZ40UAAHC".
[Client 2] File "2-1.txt" has content: "RBA5ESEOYWS745IIPY0XQK48RM43IH54K943AJ4TPP39WES3HTXNFDMQ7WCMYR5AO8PFJOR7VE878ZTF4OOVOAITY54NZROV9F51".
[Client 2] Finished executing all commands in 3.0356786251068115 seconds.
[Server 5] (127.0.0.1): Updating version for file "0-6.txt" from 22 to 24.
[Server 2] (127.0.0.1): Updating contents of file "0-6.txt" to "8QONI90O3PIW7D43TP4VRGPCMYYNQS0CJQMUO0QHY1VBWQUX1JI9TYG68UJWAB9RGB58QWNWOGLL4GFOPL82X2JUPOUSZ40UAAHC".
[Server 2] (127.0.0.1): Updating version for file "0-6.txt" from 23 to 24.
[Server 0] (127.0.0.1): Updating contents of file "0-6.txt" to "8QONI90O3PIW7D43TP4VRGPCMYYNQS0CJQMUO0QHY1VBWQUX1JI9TYG68UJWAB9RGB58QWNWOGLL4GFOPL82X2JUPOUSZ40UAAHC".
[Server 0] (127.0.0.1): Updating version for file "0-6.txt" from 21 to 24.
[Server 3] (127.0.0.1): Updating contents of file "0-6.txt" to "8QONI90O3PIW7D43TP4VRGPCMYYNQS0CJQMUO0QHY1VBWQUX1JI9TYG68UJWAB9RGB58QWNWOGLL4GFOPL82X2JUPOUSZ40UAAHC".
[Server 3] (127.0.0.1): Updating version for file "0-6.txt" from 23 to 24.
[Coordinator] (127.0.0.1): Finished writing to "0-6.txt".
[Server 4] (127.0.0.1): Coordinator finished processing request to write to "0-6.txt".
[Client 0] Wrote "8QONI90O3PIW7D43TP4VRGPCMYYNQS0CJQMUO0QHY1VBWQUX1JI9TYG68UJWAB9RGB58QWNWOGLL4GFOPL82X2JUPOUSZ40UAAHC" to file "0-6.txt".
[Client 0] Finished executing all commands in 3.0383620262145996 seconds.
```
Just as we expected, the write heavy workload took longer than both the mixed and read heavy workloads took to execute. These results indicate that performance wise our read and write operations are behaving as expected. Again, manual verification will show that the contents of the files are correct for each read operation.

## Test Case 4: Read-Write Locks & Conflicting Operations

Another test case is to ensure that the read-write lock options works as expected. That is, multiple readers should be able to read from the same file at once. Likewise, we should also expect that operations are serialized in order to guarentee sequential consistency. Using the configuration file `test/4/config.json` we expect an output similar to the output below

```
...
[Server 3] (127.0.0.1): Updating contents of file "0-1.txt" to "2OJDN121YQFZWD00UXCAQU44ZH31WGIH4QE6TAHWL5C2VSLFOYE4LBSEHSOI7YJ9VMGZCLB8BJQ8R1A01KJLMST6X7HOO4EBBMNS".
[Server 3] (127.0.0.1): Updating version for file "0-1.txt" from 29 to 32.
[Server 4] (127.0.0.1): Updating contents of file "0-1.txt" to "2OJDN121YQFZWD00UXCAQU44ZH31WGIH4QE6TAHWL5C2VSLFOYE4LBSEHSOI7YJ9VMGZCLB8BJQ8R1A01KJLMST6X7HOO4EBBMNS".
[Server 4] (127.0.0.1): Updating version for file "0-1.txt" from 31 to 32.
[Server 5] (127.0.0.1): Updating contents of file "0-1.txt" to "2OJDN121YQFZWD00UXCAQU44ZH31WGIH4QE6TAHWL5C2VSLFOYE4LBSEHSOI7YJ9VMGZCLB8BJQ8R1A01KJLMST6X7HOO4EBBMNS".
[Server 5] (127.0.0.1): Updating version for file "0-1.txt" from 30 to 32.
[Server 2] (127.0.0.1): Updating contents of file "0-1.txt" to "2OJDN121YQFZWD00UXCAQU44ZH31WGIH4QE6TAHWL5C2VSLFOYE4LBSEHSOI7YJ9VMGZCLB8BJQ8R1A01KJLMST6X7HOO4EBBMNS".
[Server 2] (127.0.0.1): Updating version for file "0-1.txt" from 27 to 32.
[Coordinator] (127.0.0.1): Finished writing to "0-1.txt".
[Server 1] (127.0.0.1): Coordinator finished processing request to write to "0-1.txt".
[Client 0] Wrote "2OJDN121YQFZWD00UXCAQU44ZH31WGIH4QE6TAHWL5C2VSLFOYE4LBSEHSOI7YJ9VMGZCLB8BJQ8R1A01KJLMST6X7HOO4EBBMNS" to file "0-1.txt".
[Server 4] (127.0.0.1): Received request to read contents from "0-9.txt".
[Coordinator] (127.0.0.1): Received request to read contents from "0-9.txt".
[Coordinator] (127.0.0.1): Formed read quorum consisting of servers: [('127.0.0.1', 8082), ('127.0.0.1', 8086), ('127.0.0.1', 8087), ('127.0.0.1', 8085)].
[Coordinator] (127.0.0.1): Server 127.0.0.1:8082 has version 30 for file "0-9.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8086 has version 32 for file "0-9.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8087 has version 32 for file "0-9.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8085 has version 31 for file "0-9.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8086 has the highest version (32) for file "0-9.txt".
[Server 5] (127.0.0.1): Fetching contents of "0-9.txt" for coordinator.
[Coordinator] (127.0.0.1): The contents for file "0-9.txt" are "3AS1D62QCI9G09MZRHL5QPZHRJMT6KFZWMQYXCEM7KOJUM03A0CDIU2XZ56VLS611HS8HSJ5G4YX308U70C1F4HXSOY2Y6DBYXJV".
[Server 4] (127.0.0.1): Coordinator finished processing request to read from "0-9.txt".
[Client 0] File "0-9.txt" has content: "3AS1D62QCI9G09MZRHL5QPZHRJMT6KFZWMQYXCEM7KOJUM03A0CDIU2XZ56VLS611HS8HSJ5G4YX308U70C1F4HXSOY2Y6DBYXJV".
[Client 0] Finished executing all commands in 7.214054822921753 seconds.
```
As expected the operations take a considerably longer amount of time to execute because different clients are writing to the same file. However, we should see that indeed read/write operations are ordered properly and no concurrency issues are present.

## Test Case 5: Error Handling

We should expect our system to be robust to different types of errors. One such error is attempting to read from a file that does not exist. We expect that the server will simply throw a `FileNotFound` error. Using the configuration file `tests/5/config.json` we expect an output similar to the output below
```
...
[Coordinator] (127.0.0.1): Server 127.0.0.1:8086 has version 0 for file "y.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8083 has version 0 for file "y.txt".
[Server 6] (127.0.0.1): Received request to read contents from "x.txt".
[Coordinator] (127.0.0.1): Received request to read contents from "x.txt".
[Coordinator] (127.0.0.1): Formed read quorum consisting of servers: [('127.0.0.1', 8083), ('127.0.0.1', 8082), ('127.0.0.1', 8085), ('127.0.0.1', 8084)].
[Coordinator] (127.0.0.1): Server 127.0.0.1:8082 has version 0 for file "y.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8083 has version 0 for file "x.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8084 has version 0 for file "y.txt".
[Coordinator] (127.0.0.1): No server was found to have a file version number greater than 0.
[Coordinator] (127.0.0.1): Server 127.0.0.1:8082 has version 0 for file "x.txt".
[Client 1] Could not find file: "y.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8085 has version 0 for file "x.txt".
[Server 4] (127.0.0.1): Received request to read contents from "999.txt".
[Coordinator] (127.0.0.1): Received request to read contents from "999.txt".
[Coordinator] (127.0.0.1): Server 127.0.0.1:8084 has version 0 for file "x.txt".
[Coordinator] (127.0.0.1): Formed read quorum consisting of servers: [('127.0.0.1', 8083), ('127.0.0.1', 8086), ('127.0.0.1', 8082), ('127.0.0.1', 8085)].
[Coordinator] (127.0.0.1): No server was found to have a file version number greater than 0.
[Client 2] Could not find file: "x.txt".
...
```
From the output above, we see that the system correctly handles the case when a file being read is not present. Likewise, the client correctly indicates that it could not find the corresponding file.

## Test Case 6: Remote Execution

As a final test case, we expect our system to work correctly when different nodes are located on different machines. 


# Performance Analysis
