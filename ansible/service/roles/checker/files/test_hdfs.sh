#!/bin/bash

dir=$1

function check(){
    if [ "$1" != "0" ] 
    then
        exit 1;
    fi
}

hdfs dfs -mkdir -p /tmp/checker
hdfs dfs -rm -r /tmp/checker/*
for f in `ls $dir` 
do
    echo $f
    hdfs dfs -copyFromLocal $dir/$f /tmp/checker/
    check $?
    hdfs dfs -text /tmp/checker/$f
    check $?
done

hdfs dfs -rm  -r /tmp/checker/*
check $?
