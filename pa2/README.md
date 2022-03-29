# System Design

For this programming assignment, the functionality of the system is is broken up into three major components: the client, the super node and the chord nodes.

The system is implemented in Python and makes use of the [Apache Thrift](https://thrift.apache.org/) RPC library for communication between nodes in the system. The source for the client can be found in the `client.py` file. Furthermore, the source for the super node can be found in the `supernode.py` file and the source for the chord node can be found in the `chordnode.py` file. The corresponding Thrift objects are defined in the `service.thrift` file.

A significant portion of the logic in the system is derived from the work presented in the original [Chord](https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf) paper. That is, each chord node is assigned a unique id and for each key the successor (the node with the smallest id greater than or equal to the given key) is responsible for storing the value for the key. When a chord node joins the system, it locates its predecessor and successor to update their successor and predecessor accordingly. Furthermore, it also notifies all nodes in the system that may need to update their finger tables. When performing an insert or lookup, each node will recurisvely call other chord nodes in the system by using its finger table until the destination node is located. Once the destination node is located, either the insertion takes place or the value for the key is forwarded back to the original caller. The super node in this system merely acts as an entry point in to the DHT for the client and manages nodes joining the DHT, ensuring that only one node is joining the DHT at any given point in time. Likewise, the clients in the system are the nodes that initiate operations to read or update the conents of the DHT.

 As mentioned earlier, the implementation of the chord node in the system relies heavily on the work in the original Chord paper. In this sytem, each chord node is assigned an id according to its assigned domain name (e.g. `kh4250-11.cselabs.umn.edu`, `237.52.76.142` or `127.0.0.1`) and port (e.g. `8080`). Its id is obtained by taking the SHA256 hash of `<ip>:<port>` and discarding some of the higher bits depending on the key size provided in the configuration file. The implementation details for joining the DHT and performing operations are very similar to the details presented in the Chord paper, with a few subtle differences. Most notably, when updating finger tables, the new node n, contacts pred(n - 2<sup>i</sup>+1) instead of pred(n - 2 <sup>i</sup>) in the rare instance that n - 2 <sup>i</sup> is actually a node in the system. However, in practice the likelihood of a node with this key being present in the system is very unlikely with large key sizes. When a node initially request to join the system, it makes a request to the super node for a reference to an existing node in the DHT. In the event that the super node throws a `DHTBusy` exception, the node will wait a certain amount of time according to the sleep delay before attempting to request another node. After successfully receiving an existing node in the DHT, if the node is the empty node then the node initializes its successor and all entries in its finger table to reference itself. Otherwise, the node will use the entry node to find its successor and predecessor and subsequently make calls to them to update their predecessor and successor. Furthermore, it will initialize its finger table and update all nodes whose finger tables may need to be updated. Finally, the node will make another call to the super node to notify it that the node has finished joining the DHT. Performing insertions and retrieving definitions is done by using the key for a given word and finding its successor using the finger table of each node. This process is descriped in depth in the original Chord paper. The key for a given word is obtained by simply taking its SHA256 hash and discarding the higher bits depending on the key size. 
 
As mentioned earlier, the only responsibility of the super node is to provide access into the DHT and coordinate nodes joining the DHT. As a result, its implementation is relatively straightforward. When a chord node makes a request to the super node to join the DHT, the super node first attempts to acquire a mutex. If the mutex could not be acquired, the super node will throw a `DHTBusy` exception. Otherwise, if the DHT is empty the super node will return an empty node information object, letting the chord node know that it is the first node in the DHT. If the DHT is not empty, the super node will return a random node from the list of nodes already in the DHT. In both cases, the super node will add the joining node to a list of nodes in the system. When a node makes a call to the super node to notify it that the node has finished joining the DHT, the mutex will be released, allowing other chord nodes to join the DHT. If a client makes a request to the super node for a chord node, the super node will simply randomly return a chord node in its list of chord nodes. 

The implementation for the client is also relatively straightforward. First, the client will make a request to the super node to receive a reference to a node in the DHT. After receiving a reference to a chord ndoe in the DHT, it will subsequently execute each of the commands provided in the configuration file. There are four client commands. The `get` command accepts one argument which is the word to retrieve the definition. For example, the command `get foo` will retrieve the definition for the word `foo` and output it to the console. Likewise, the `put` command accepts a word and a definition as arguments. For example, the command `put foo cat` will store `cat` as the definition for `foo`. The `store` command accepts a text file as its only argument which contains words and definitions provided in the format seen in the `dictionary_words.txt` file. An insertion will be made into the DHT for each word and definition in the provided file. For example, the command `store dictionary_words.txt` will insert each word and its corresponding definition from the file `dictionary_words.txt` into the DHT. Finally, the `load` command accepts a text file which contains a list of words seperated by a new line. Furthermore, it optionally accepts a second argument which is the destination file to store the definitions for each word found in the DHT. The `load` command also outputs the definitions to console. For example, the command `load words.txt defs.txt` will load the definitions for each word in `words.txt` and store the definitions into the file `defs.txt`.

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
python run.py <config file>
```
If a configuration file is not passed to `run.py` then the default configuration file `config.json` will be used. 
