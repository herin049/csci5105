# System Design

For this programming project, the functionality of the system is made up of three major entities: the client, the server and the coordinator.

The system is implemented in Python and makes use of the [Apache Thrift](https://thrift.apache.org/) RPC library for communication between nodes in the system. The source for the client can be found in the `client.py` file. Likewise, the source for the server/coordinator nodes can be found in the `server.py`. The Thrift object for the system are defined in the `service.thrift` file. 

The goal of this project is to build a simple distributed file system capable of sharing several files between multiple clients replicated to several servers to increased performance and reliability. In order to achieve this goal, Gifford's Quorum-Based Protocol will be used to ensure that read and write operations to the same file are serialized in order to achieve sequential consistency. If we let N<sub>r</sub> and N<sub>w</sub> denote the size of each read and write quorum in the system (i.e. how many servers must a client receive approval from before performing a read or write operation), then if N is the total number of nodes in the system, Gifford's Quorum-Based Protocol requires that.

1. N<sub>r</sub> + N<sub>w</sub> > N
2. N<sub>w</sub> > N / 2
