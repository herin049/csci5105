#!/bin/bash
trap terminate INT

function terminate() {
    kill -KILL $NPID1 $NPID2 $NPID3 $NPID4 $SPID $CPID
}

source ./venv/bin/activate
python computeNode.py 0 &
NPID1=$!
python computeNode.py 1 &
NPID2=$!
python computeNode.py 2 &
NPID3=$!
python computeNode.py 3 &
NPID4=$!
sleep 2
python server.py &
SPID=$!
sleep 2
python client.py &
CPID=$!
wait