#!/bin/bash

count=0
while read p; do
   if [ $count == 0  ]; then
      NODE_COMMAND_0=`echo $p | cut --complement -f 1 -d' '`
   elif [ $count == 1  ]; then
      NODE_COMMAND_1=`echo $p | cut --complement -f 1 -d' '`
   elif [ $count == 2  ]; then
      NODE_COMMAND_2=`echo $p | cut --complement -f 1 -d' '`
   elif [ $count == 3  ]; then
      NODE_COMMAND_3=`echo $p | cut --complement -f 1 -d' '`
   elif [ $count == 4  ]; then
      SERVER_COMMAND=`echo $p | cut --complement -f 1 -d' '`
   elif [ $count == 5 ]; then
      CLIENT_COMMAND=`echo $p | cut --complement -f 1 -d' '`
   fi 
   count=`echo "scale=0;$count + 1" | bc`
done < commands.txt

count=0
while read p; do
   varname=`echo $p | cut  -f 1 -d' '`
   varval=`echo $p | cut --complement -f 1 -d' '`
   setenvstring="$setenvstring setenv $varname $varval &&"
   if [ $varname == "PROJ_PATH" ] ; then
      PROJ_PATH=`echo $p | cut --complement -f 1 -d' '`
   fi
   count=`echo "scale=0;$count + 1" | bc`
done < env.txt

count=0
while read p; 
do
  address=`echo $p | awk '{print $2}'`
  if [ $count == 0 ] ; then
     NODE_0_IP=`echo $p | cut --complement -f 1 -d' '`
  elif  [ $count == 1 ] ; then
     NODE_1_IP=`echo $p | cut --complement -f 1 -d' '`
  elif  [ $count == 2 ] ; then
     NODE_2_IP=`echo $p | cut --complement -f 1 -d' '`
  elif  [ $count == 3 ] ; then
     NODE_3_IP=`echo $p | cut --complement -f 1 -d' '`
  elif  [ $count == 4 ] ; then
     SERVER_IP=`echo $p | cut --complement -f 1 -d' '`
  elif  [ $count == 5 ] ; then
     CLIENT_IP=`echo $p | cut --complement -f 1 -d' '`
  fi
  count=`echo "scale=0;$count + 1" | bc`
done < machine.txt

echo $setenvstring

#Get the user ID

USERID=`whoami`

#Start the compute node 0
CA=`echo "$setenvstring  cd $PROJ_PATH &&  nohup $NODE_COMMAND_0 & "`
echo "ssh -t -n -f $USERID@$NODE_0_IP  \"csh -c '$CA'\" > /dev/null"  > command0.sh
source command0.sh

#Start the compute node 1
CA=`echo "$setenvstring cd $PROJ_PATH &&  nohup $NODE_COMMAND_1 & "`
echo "ssh -t -n -f $USERID@$NODE_1_IP  \"csh -c '$CA'\" > /dev/null"  > command1.sh
source command1.sh

#Start the compute node 2
CA=`echo "$setenvstring cd $PROJ_PATH &&  nohup $NODE_COMMAND_2 & "`
echo "ssh -t -n -f $USERID@$NODE_2_IP  \"csh -c '$CA'\" > /dev/null"  > command2.sh
source command2.sh

#Start the compute node 3
CA=`echo "$setenvstring cd $PROJ_PATH && nohup $NODE_COMMAND_3 & "`
echo "ssh -t -n -f $USERID@$NODE_3_IP  \"csh -c '$CA'\" > /dev/null"  > command3.sh
source command3.sh

# Sleep for a few seconds so the servers can startup
echo "Sleeping while waiting for the compute nodes to bootup" 
sleep 4
echo "The compute nodes should have booted up by now"

#Start the server
CA=`echo "$setenvstring cd $PROJ_PATH &&  nohup $SERVER_COMMAND & "`
echo "ssh -t -n -f $USERID@$SERVER_IP  \"csh -c '$CA'\" > /dev/null"  > command4.sh
source command4.sh

# Sleep for a few seconds so the server can startup 
echo "Sleeping while waiting for the server to bootup"
sleep 4
echo "The server should have booted up by now"

#Start the client. It should automatically send the request
CA=`echo "$setenvstring cd $PROJ_PATH && nohup $CLIENT_COMMAND & "`
echo "ssh -t -n -f $USERID@$CLIENT_IP  \"csh -c '$CA'\" > /dev/null"  > command5.sh
source command5.sh

##### Assign Points ####
echo "ssh -t -n -f $USERID@$SERVER_IP  ' ps -ef  > log_0  ' "  > grade0.sh
echo "ssh -t -n -f $USERID@$CLIENT_IP  ' ps -ef > log_1  ' "  > grade1.sh
echo "ssh -t -n -f $USERID@$NODE_0_IP  ' ps -ef  > log_2  ' "  > grade2.sh
echo "ssh -t -n -f $USERID@$NODE_1_IP  ' ps -ef  > log_3  ' "  > grade3.sh
echo "ssh -t -n -f $USERID@$NODE_2_IP  ' ps -ef > log_4  ' "  > grade4.sh
echo "ssh -t -n -f $USERID@$NODE_3_IP  ' ps -ef > log_5  ' "  > grade5.sh

echo "Waiting 60s for logging to complete ..."
sleep 600
score=0
for i in 0 1 2 3 4 5 
do
    source grade$i.sh
    if [ $i -eq 0 ]; then 
      numlines=`cat ~/log_$i | grep "$SERVER_COMMAND" | wc -l`
    elif [ $i -eq 1 ]; then
      numlines=`cat ~/log_$i | grep "$CLIENT_COMMAND" | wc -l`
    elif [ $i -eq 2 ]; then
      numlines=`cat ~/log_$i | grep "$NODE_0_COMMAND" | wc -l`
    elif [ $i -eq 3 ]; then
      numlines=`cat ~/log_$i | grep "$NODE_1_COMMAND" | wc -l`
    elif [ $i -eq 4 ]; then
      numlines=`cat ~/log_$i | grep "$NODE_2_COMMAND" | wc -l`
    elif [ $i -eq 5 ]; then
      numlines=`cat ~/log_$i | grep "$NODE_3_COMMAND" | wc -l`
    fi

    if [ $numlines -gt 1  ]; then
       score=`echo "scale=0;$score + 2 " | bc `
    fi
done

echo "Waiting for 60s for image processing to be completed ..."
sleep 180 
input_lines=`ls -la input_dir/ | wc -l`
output_lines=`ls -la output_dir/ | wc -l`
if [ ! $input_lines -gt $output_lines  ]; then
    if [ $output_lines -gt 3 ]; then 
         score=`echo "scale=0;$score + 3" | bc`
    fi
fi

echo "Your total score is $score"
########################
