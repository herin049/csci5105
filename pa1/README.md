# System Design

In accordance with the requirements of the assignment, the system is broken up into three major components: the client, the server and the compute nodes.

The project is implemented in Python, the source for the client can be found in the `client.py` file. Likewise, the source for the server can be found in the `server.py` file and the source for the compute node can be found in the `computeNode.py` file.

At a high level, the system works by having the client initially submit a job to the server with a data directory and a list of files to process. Next, the server will take each of these files and create a task for each one, assigning each task to a random compute node. Under the "random" policy, each compute node will always accept the task and simply inject delay randomly depending on its "load probability". After processing the image, each compute node will write its result into the output directory. Once all tasks have completed, the server will return the elapsed time in seconds to the client. A more details description of the requirements and design of the system can be found in the Programming Assignment 1 PDF.

As mentioned earlier, the project is implemented in Python. Furthermore, the [Thrift](https://thrift.apache.org/) and [OpenCV](https://opencv.org/) libraries are used in the project. The project's Thrift objects are defined in the `service.thrift` file. This file contains a few structures and services, most notably the `ServerService` which defines the service the server implements which accepts a `Job` returns the elapsed time as a double, and the `ComputeService` which accept a `Task` and potentially throws a `TaskRejected` exception.

The compute node implementation is relatively straightforward. Under the "load" policy, the compute node will reject the task with probability equal to its load probability, which can be defined in the configuration file. Furthermore, if it accepts the task, it will inject delay again based on its load probability. The amount of delay injected can be specified in the configuation file. After injecting delay, the compute node will process the image by coloring it gray and applying the OpenCv Canny filter, writing the result to the output directory. 

The server implementation is slightly more involved. When the server recieves a job from the client, it will create a `Task` object for each file sent by the client. Then, it will create a seperate thread for each task where it will randomly assign the task to a given compute node. The list of compute nodes is given in the `machine.txt` file and parsed by the server. Once all of the tasks have been processed, the server returns the elapsed time in seconds to the client. 

The client implementation is also straightforward. First, the client will parse the `machine.txt` file to get the address of the server. Then, the client will collect all of the file names in the directory `PROJ_PATH/data/input_dir` where `PROJ_PATH` is provided as an environment variable or just the current working directory by default. Then, the client will create the job and submit it to the server. Furthermore, for testing purposes one can choose to have the client submit the same job multiple times by changing the `num_samples` field in the configuration file. The client will print out the total time it took for all the sample as well as the average time. 

# Operation & Usage

As mentioned above, there are two main files used for configuring the system: the `machine.txt` file which contains a list of nodes followed by their machine address and the `config.json` file which contains options for each of the node types. 

To run the project start by creating a Python virtual environment by typing
```bash
python3 -m venv ./venv
```
Next, activate the environment and install the required packages
```bash
source ./venv/bin/activate
pip install -r requirements.txt
```
Alternatively, one can install Thrift and OpenCV and set the environment variables `THRIFT_LIB_PATH` and `OPENCV_LIB_PATH` to point to your Thrift and OpenCV Python installation.

Next, one needs to generate the required Thrift files by either running the `thrift-gen.sh` shell script or running
```bash
mkdir -p gen
thrift -r --gen py -out gen service.thrift
```

Next, modify the `config.json` and `machine.txt` files depending on how the system is being ran. Entries in the `machine.txt` file follow the format `<node_type> <node_address>` where `node_type` is either `client`, `server` or `node_<node_num>` for compute nodes.

The compute nodes can be ran by executing 
```bash
python computeNode.py <node_num>
```
Where `node_num` ranges from 0 to the number of compute nodes minus one. 

Likewise, the server can be ran by executing 
```bash
python server.py
```
and the client can be ran by executing 
```bash
python client.py
```

# Test Cases & Expected Output

The shell script `test.sh` provides a convient way to run and test the system. Using the default options provided in the `config.json` file and the default images in the data directory, one should expect an output similar to the output below 
```bash
[Compute 3] Initializing the compute handler with a load probability of 0.2, a load delay of 3 seconds and a compute policy of "random".
[Compute 0] Initializing the compute handler with a load probability of 0.2, a load delay of 3 seconds and a compute policy of "random".
[Compute 1] Initializing the compute handler with a load probability of 0.2, a load delay of 3 seconds and a compute policy of "random".
[Compute 0] Starting compute node...
[Compute 3] Starting compute node...
[Compute 1] Starting compute node...
[Compute 2] Initializing the compute handler with a load probability of 0.2, a load delay of 3 seconds and a compute policy of "random".
[Compute 2] Starting compute node...
[Server] Initializing server handler.
[Server] Starting server...
[Client] Submitting job to process images [starry_night.jpg, mask.png, HappyFish.jpg, baboon.jpg, squirrel_cls.jpg, fruits.jpg] in the directory ./data
[Server] Recieved job to process images [starry_night.jpg, mask.png, HappyFish.jpg, baboon.jpg, squirrel_cls.jpg, fruits.jpg] in the directory: ./data
[Compute 3] Recieved task to process the file "starry_night.jpg".
[Compute 3] Recieved task to process the file "mask.png".
[Compute 0] Recieved task to process the file "squirrel_cls.jpg".
[Compute 3] Recieved task to process the file "HappyFish.jpg".
[Compute 3] Injecting delay of 3 seconds.
[Compute 3] Recieved task to process the file "baboon.jpg".
[Compute 3] Injecting delay of 3 seconds.
[Compute 0] Recieved task to process the file "fruits.jpg".
[Compute 3] Finished processing "mask.png".
[Compute 0] Finished processing "squirrel_cls.jpg".
[Compute 0] Finished processing "fruits.jpg".
[Compute 3] Finished processing "starry_night.jpg".
[Compute 3] Finished processing "HappyFish.jpg".
[Compute 3] Finished processing "baboon.jpg".
[Server] Finished processing job in 3.0239341259002686 seconds.
[Client] Server finished processing job in 3.0239341259002686 seconds.
[Client] Finished processing the job 1 times in 3.0239341259002686 seconds for an average delay of 3.0239341259002686 seconds.
```

# Performance Evaluation Results
