# System Design

For this programming assignment, the functionality of the system is is broken up into three major components: the client, the super node and the chord nodes.

The system is implemented in Python and makes use of the [Apache Thrift](https://thrift.apache.org/) RPC library for communication between nodes in the system. The source for the client can be found in the `client.py` file. Furthermore, the source for the super node can be found in the `supernode.py` file and the source for the chord node can be found in the `chordnode.py` file. 

A significant portion of the logic for the chord nodes is derived from the work presented in the original [Chord](https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf) paper. That is, each chord node is assigned a unique id and for each key the successor (the node with the smallest id greater than or equal to the given key) is responsible for storing the value for the key. When a chord node joins the system, it locates its predecessor and successor to update their successor and predecessor accordingly. Furthermore, it also notifies all nodes in the system that may need to update their finger tables. When performing an insert or lookup, each node will recurisvely call other chord nodes in the system by using its finger table until the destination node is located. Once the destination node is located, either the insertion takes place or the value for the key is forwarded back to the original caller. 

 In this sytem, each chord node is assigned an id according to its assigned domain name (e.g. `kh4250-11.cselabs.umn.edu`, `237.52.76.142` or `127.0.0.1`) and port (e.g. 8080).
