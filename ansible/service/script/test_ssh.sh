#!/bin/bash

port=$1
host=$2

function test_ssh(){
    expect -c "
    spawn ssh -p $1 $2  \"hostname;\"
    expect {
        \"*assword\" {exit 1;}
        \"yes/no\" {send \"yes\r\"; exp_continue;}
          }
    "
    if [ "$?" == "1" ]
    then
        echo "SSH_FAILED!!!!"
    else
        echo "SSH_OK."
    fi
    
}

test_ssh $port $host
