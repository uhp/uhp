#!/bin/bash

ROOT=$(cd $(dirname $0);pwd)

solrctl instancedir --generate $ROOT/check_solr_config
cp /usr/share/doc/search*/examples/solr-nrt/collection1/conf/schema.xml $ROOT/check_solr_config/conf

solrctl instancedir --create check_collection $ROOT/check_solr_config

solrctl collection --create check_collection


hdfs dfs -mkdir -p /user/hdfs/check_solr/indir/
hdfs dfs -mkdir -p /user/hdfs/check_solr/outdir/

hdfs dfs -rmr /user/hdfs/check_solr/indir/*
hdfs dfs -rmr /user/hdfs/check_solr/outdir/*

hdfs dfs -copyFromLocal /usr/share/doc/search*/examples/test-documents/sample-statuses-*.avro /user/hdfs/check_solr/indir/



#solrctl collection --deletedocs check_collection

hadoop --config /etc/hadoop/conf jar  /usr/lib/solr/contrib/mr/search-mr-1.0.0-job.jar  org.apache.solr.hadoop.MapReduceIndexerTool  --morphline-file /usr/share/doc/search-1.0.0/examples/solr-nrt/test-morphlines/tutorialReadAvroContainer.conf --output-dir hdfs://mycluster/user/hdfs/check_solr/outdir --go-live --zk-host hadoop2:21810,hadoop3:21810/solr --collection check_collection hdfs://mycluster/user/hdfs/check_solr/indir



