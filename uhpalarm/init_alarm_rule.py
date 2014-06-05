#!/usr/bin/env python
# coding=utf-8

import os, sys

commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir)

import database
from model.alarm import Alarm

if __name__ == "__main__" :
    session = database.getSession()
    for alarm in session.query(Alarm):
        session.delete(alarm)
    session.commit()
    #base machine resource check
    session.add(Alarm("check load one","max(load_one,cpu_num,cpu_num*2)","send_mail","all"))
    session.add(Alarm("check disk use","disk_use(90,95)","send_mail","all"))
    session.add(Alarm("check swap","max((swap_total-swap_free)/mem_total,0.5,0.7)","send_mail","all"))
    session.add(Alarm("check memory","min(mem_free+mem_cached,2048*1024,1024*1024)","send_mail","all"))
    session.add(Alarm("check bytesin","max(bytes_in,50*1024*1024,80*1024*1024)","send_mail","all"))
    session.add(Alarm("check bytesout","max(bytes_out,50*1024*1024,80*1024*1024)","send_mail","all"))
    session.add(Alarm("check swapadd","max(swap_free-PRE_swap_free,10*1024*1024,100*1024*1024)","send_mail","all"))

    #instance check state
    session.add(Alarm("check instance","check_instance_state()","send_mail","cluster"))

    #zookeeper check
    session.add(Alarm("check zk heap","max(zookeeper_memory_memHeapUsed/zookeeper_memory_memHeapCommitted,0.8,0.9)","send_mail","zookeeper"))


    #hdfs check
    session.add(Alarm("check missing blocks","max(dfs.FSNamesystem.MissingBlocks,0,5)","send_mail","namenode"))
    session.add(Alarm("check lost heartbeat","max(dfs.FSNamesystem.ExpiredHeartbeats-PRE_dfs.FSNamesystem.ExpiredHeartbeats,0,0)","send_mail","namenode"))
    session.add(Alarm("check nmweb","namenode_web()","send_mail","cluster"))

    session.add(Alarm("check nm heap","max(jvm.JvmMetrics.ProcessName=NameNode.MemHeapUsedM/jvm.JvmMetrics.ProcessName=NameNode.MemHeapCommittedM,0.8,0.9)","send_mail","namenode"))
    session.add(Alarm("check nmweb","namenode_web()","send_mail","datanode"))

    session.add(Alarm("check dn heap","max(jvm.JvmMetrics.ProcessName=DataNode.MemHeapUsedM/jvm.JvmMetrics.ProcessName=DataNode.MemHeapCommittedM,0.8,0.9)","send_mail","datanode"))

    #yarn check
    session.add(Alarm("check rmweb","resourcemanager_web()","send_mail","cluster"))
    session.add(Alarm("check rm heap","max(jvm.JvmMetrics.ProcessName=ResourceManager.MemHeapUsedM/jvm.JvmMetrics.ProcessName=ResourceManager.MemHeapCommittedM,0.8,0.9)","send_mail","resourcemanager"))

    session.add(Alarm("check rm heap","max(jvm.JvmMetrics.ProcessName=NodeManager.MemHeapUsedM/jvm.JvmMetrics.ProcessName=NodeManager.MemHeapCommittedM,0.8,0.9)","send_mail","nodemanager"))

    #hbase
    session.add(Alarm("check hm heap","max(hbasemaster_memory_memHeapUsed/hbasemaster_memory_memHeapCommitted,0.8,0.9)","send_mail","hbasemaster"))
    session.add(Alarm("check rs heap","max(regionserver_memory_memHeapUsed/regionserver_memory_memHeapCommitted,0.8,0.9)","send_mail","regionserver"))

    #hive
    session.add(Alarm("check metastore heap","max(hivemetastore_memory_memHeapUsed/hivemetastore_memory_memHeapCommitted,0.8,0.9)","send_mail","hivemetastore"))
    session.add(Alarm("check hiveserver heap","max(hiveserver_memory_memHeapUsed/hiveserver_memory_memHeapCommitted,0.8,0.9)","send_mail","hiveserver"))
    session.add(Alarm("check hiveserver2 heap","max(hiveserver2_memory_memHeapUsed/hiveserver2_memory_memHeapCommitted,0.8,0.9)","send_mail","hiveserver2"))

    session.commit()
    session.close()
