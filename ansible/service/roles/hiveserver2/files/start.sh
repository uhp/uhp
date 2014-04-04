#!/bin/bash

function check_start(){
  status=`/sbin/service hive-server2 status`
  
  if [[ "$status" =~ "server2 is running" ]] ;
  then
    echo "0"
  else
    echo "1"
  fi;
}

now=`check_start`

if [ "$now" == "1" ];
then
    /sbin/service hive-server2 start 
    exit `check_start`
fi;
