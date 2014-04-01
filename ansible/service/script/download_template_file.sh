#!/bin/bash

host=$1
dir=$2
tempdir=$3

cd $UHP_HOME/ansible/service/
cp conf_download.yml conf_download_${tempdir}.yml 
sed "s#WANT_HOST#$host#g" -i conf_download_${tempdir}.yml
sed "s#WANT_DIR#$dir#g" -i conf_download_${tempdir}.yml
sed "s#WANT_FILE#$file#g" -i conf_download_${tempdir}.yml
sed "s#TMP_DIR#$tempdir#g" -i conf_download_${tempdir}.yml

if [ "$dir" == "hdfs" || "dir" == "yarn" ] 
then
    sed "s#SET_VAR#hadoop_conf_dir#g" -i conf_download_${tempdir}.yml"
fi;
if [ "$dir" == "zookeeper" ] 
then
    sed "s#SET_VAR#zookeeper_conf_dir#g" -i conf_download_${tempdir}.yml"
fi;
if [ "$dir" == "hbase" ] 
then
    sed "s#SET_VAR#hbase_conf_dir#g" -i conf_download_${tempdir}.yml"
fi;
if [ "$dir" == "hive" ] 
then
    sed "s#SET_VAR#hive_conf_dir#g" -i conf_download_${tempdir}.yml"
fi;




#ansible-playbook -i $UHP_HOME/inventor/mysqlinventory.py conf_download_${tempdir}.yml

rm conf_download_${tempdir}.yml
mv /tmp/$host/tmp/${tempdir} /tmp/${host}_${dir}_${file}_${tempdir}
