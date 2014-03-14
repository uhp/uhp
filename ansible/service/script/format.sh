#!/usr/bin/env bash

function zk(){
  expect -c ";
  spawn hdfs zkfc -formatZK;
  expect \"(Y or N)\";
  send \"Y\n\";
  expect";
}

function qjm(){
  expect -c ";
  spawn hdfs namenode -initializeSharedEdits;
  expect \"(Y or N)\";
  send \"Y\n\";
  expect";
}

function nn(){
  expect -c ";
  spawn hdfs namenode -format;
  expect \"(Y or N)\";
  send \"Y\n\";
  expect \"(Y or N)\";
  send \"Y\n\";
  expect \"(Y or N)\";
  send \"Y\n\";
  expect";
}

#function standbynn(){
#  expect -c ";
#  spawn hdfs namenode -bootstrapStandby;
#  expect \"(Y or N)\";
#  send \"Y\n\";
#  expect";
#}
function snn(){
    hostname
}

$1
