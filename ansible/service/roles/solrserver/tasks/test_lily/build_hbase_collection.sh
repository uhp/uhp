#!/bin/bash

#solrctl instancedir --generate $HOME/check_hbase_collection
#edit $HOME/check_hbase_collection/conf/schema.xml
#cp $HOME/schema.xml $HOME/check_hbase_collection/conf/schema.xml
#solrctl instancedir --create check_hbase_collection $HOME/check_hbase_collection
solrctl collection --create check_hbase_collection


#hbase-indexer add-indexer \
#--name checkIndexer \
#--indexer-conf $HOME/morphline-hbase-mapper.xml \
#--connection-param solr.zk=hadoop2:21810,hadoop3:21810/solr \
#--connection-param solr.collection=check_hbase_collection \
#--zookeeper hadoop2:21810
