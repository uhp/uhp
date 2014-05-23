#!/bin/bash

hbase-indexer add-indexer \
--name checkIndexer \
--indexer-conf $HOME/morphline-hbase-mapper.xml \
--connection-param solr.zk=hadoop2:21810,hadoop3:21810/solr \
--connection-param solr.collection=check_hbase_collection \
--zookeeper hadoop2:21810
