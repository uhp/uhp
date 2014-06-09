#!/bin/bash

host=$1
dir=$2
file=$3
ts=$4
tar=$5


cd $UHP_HOME/ansible/service/
mkdir -p /tmp/$ts/$host/$dir/

ansible-playbook -i $UHP_HOME/inventor/mysqlinventory.py build_conf.yml -e '{"WANT_HOST":"$host","WANT_DIR":"$dir","WANT_FILE":$file,"TS":"$ts"}'

if [ "$tar" == "true" ]
then
cd /tmp
tar -zcvf ${ts}_${host}_${dir}.tar.gz $ts/$host/$dir/
fi






