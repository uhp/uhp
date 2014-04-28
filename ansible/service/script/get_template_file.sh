#!/bin/bash

host=$1
dir=$2
file=$3
tempfile=$4

cd $UHP_HOME/ansible/service/
cp conf_look.yml conf_look_${tempfile}.yml 

targetfile=${host}_${dir}_${file}_${tempfile}

sed "s#WANT_HOST#$host#g" -i conf_look_${tempfile}.yml
sed "s#WANT_DIR#$dir#g" -i conf_look_${tempfile}.yml
sed "s#WANT_FILE#$file#g" -i conf_look_${tempfile}.yml
sed "s#TMP_FILE#$targetfile#g" -i conf_look_${tempfile}.yml

ansible-playbook -i $UHP_HOME/inventor/mysqlinventory.py conf_look_${tempfile}.yml

rm conf_look_${tempfile}.yml
#mv /tmp/$host/tmp/${tempfile} /tmp/${host}_${dir}_${file}_${tempfile}
