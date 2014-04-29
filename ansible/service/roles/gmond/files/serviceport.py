# !/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import psutil
import re
import os
import time
_PIPE = subprocess.PIPE

descriptors = []
NAME_PREFIX = 'serviceport'
PID_FILE_MAP={
"zookeeper":"/var/run/zookeeper/zookeeper-server.pid",

"qjm":"/var/run/hadoop-hdfs/hadoop-hdfs-journalnode.pid",
"namenode":"/var/run/hadoop-hdfs/hadoop-hdfs-namenode.pid",
"zkfc":"/var/run/hadoop-hdfs/hadoop-hdfs-zkfc.pid",
"datanode":"/var/run/hadoop-hdfs/hadoop-hdfs-datanode.pid",

"resourcemanager":"/var/run/hadoop-yarn/yarn-yarn-resourcemanager.pid",
"nodemanager":"/var/run/hadoop-yarn/yarn-yarn-nodemanager.pid",
"historyserver":"/var/run/hadoop-mapreduce/yarn-hdfs-historyserver.pid",

"hbasemaster":"/var/run/hbase/hbase-hbase-master.pid",
"regionserver":"/var/run/hbase/hbase-hbase-regionserver.pid",

"hivemetastore":"/var/run/hive/hive-metastore.pid",
"hiveserver":"/var/run/hive/hive-server.pid",
"hiveserver2":"/var/run/hive-server2.pid",

"impalaserver":"/var/run/impala/impalad-impala.pid",
"impalastatestore":"/var/run/impala/statestored-impala.pid",

}
ROLE_PORT_MAP={

"zookeeper":["zookeeper__zookeeper_election_port","zookeeper__zookeeper_client_port","zookeeper__zookeeper_leader_port"],

"qjm":["hdfs__qjournal_http_port","hdfs__qjournal_port"],
"namenode":["hdfs__dfs_namenode_http_address_port","hdfs__dfs_namenode_https_address_port","hdfs__dfs_namenode_servicerpc_address_port","hdfs__dfs_namenode_rpc_address_port"],
"datanode":["hdfs__dfs_datanode_address_port","hdfs__dfs_datanode_ipc_address_port","hdfs__dfs_datanode_http_address_port"],

"resourcemanager":["yarn__yarn_rm_scheduler_port","yarn__yarn_rm_webapp_port","yarn__yarn_rm_port","yarn__yarn_rm_admin_port"],
"nodemanager":["yarn__yarn_nm_port","yarn__yarn_nm_localizer_port","yarn__mapreduce_shuffle_port","yarn__yarn_nm_webapp_port"],
"historyserver":["yarn__mapreduce_jobhistory_webapp_port","yarn__mapreduce_jobhistory_port"],

"hiveserver2":["hive__hive_server2_thrift_port"],
"hivemetastore":["hive__hive_metastore_port"],
"hiveserver":["hive__hive_server_thrift_port"],

"hbasemaster":["hbase__hbase_master_info_port","hbase__hbase_master_port"],
"regionserver":["hbase__hbase_resigionserver_info_port","hbase__hbase_resigionserver_port"],

"impalastatestore":["impala__impala_state_store_web_port","impala__impala_state_store_port"],
"impalaserver":["impala__impala_server_beeswax_port","impala__impala_server_web_port","impala__impala_backend_port","impala__impala_server_hs2_port"],

}
REAL_PORT_MAP={}
LAST_UPDATE = -1
NOW_PORT={}

def execute(cmd):
    """
    execute the cmd and return back (stdout, stderr) output
    """
    try:
        p = subprocess.Popen(cmd, stdin=_PIPE, stdout=_PIPE, stderr=_PIPE, shell=True)
        out, err = p.communicate()
        code = p.returncode
        p.stdin.close()
        return (out, err, code,)
    except Exception, e:
        return ("", e.message, -1,)

def init_now_port():
    global LAST_UPDATE, NOW_PORT
    now_time = int(time.time())
    #如果5秒内更新过将不再获取
    if now_time < 0 or now_time - LAST_UPDATE > 5:
        NOW_PORT = {}  
        out, err, code = execute("netstat -nplt 2>/dev/null | grep LISTEN | grep tcp|awk '{print $4}'")
        if code == 0:
            for line in out.split("\n"):
                index = line.rfind(":")
                if index != -1:
                    port = line[index+1:]
                    NOW_PORT[port] = 1
        LAST_UPDATE = now_time
    
    return NOW_PORT


def get_pid(service_name):
    """
    return the service's pid
    we get the pid from the default service's pid file
    :param proc:
    :return:
    """
    global PID_FILE_MAP
    if PID_FILE_MAP.has_key(service_name):
        file = PID_FILE_MAP[service_name]
        if os.path.exists(file) and os.path.isfile(file):
            f = open(file)
            pid = f.read()
            f.close()
            return pid
    return None

def get_value(name):
    """Return a value for the requested metric"""

    global SERVICES, LPARAMS

    name_parser = re.match("^%s_(.*?)_(.*)_(.*)$" % NAME_PREFIX, name)
    service_name = name_parser.group(1)
    want_port = name_parser.group(2)
    real_port = name_parser.group(3)

    now_port = init_now_port()

    pid = get_pid(service_name)
    if pid == None :
        return 0
    else:
        if now_port.has_key(real_port):
            return 1
    return 0


def metric_init(params):
    global descriptors, SERVICES, PID_FILE_MAP, ROLE_PORT_MAP, REAL_PORT_MAP

    for port_pair in params['port_list'].split(","):
        pair = port_pair.split("=")
        REAL_PORT_MAP[pair[0]]=int(pair[1])

    SERVICES = []

    for service in params['services'].strip().split(","):
        if not PID_FILE_MAP.has_key(service) :
            continue    
        SERVICES.append(service)
        if ROLE_PORT_MAP.has_key(service) :
            for want_port in ROLE_PORT_MAP[service]:
                if REAL_PORT_MAP.has_key(want_port) :
                    _name = "%s_%s_%s_%s" % ( NAME_PREFIX, service, want_port, REAL_PORT_MAP[want_port])
                    descriptors.append({
                        'name': _name,
                        'call_back': get_value,
                        'time_max': 60,
                        'value_type': 'int',
                        'units': '',
                        'slope': 'both',
                        'format': '%d',
                        'description': "uhp services port",
                        'groups': 'uhpservices'
                    })

    return descriptors

def metric_cleanup():
    """Cleanup"""

    pass


if __name__ == '__main__':
    """
    TODO 使用tcpconn类似的异步获取
    """
    #PARAMS = {'services': 'gundan,datanode,hbasemaster,historyserver,hivemetastore,hiveserver,hiveserver2,impalaserver,impalastatestore,namenode,nodemanager,qjm,regionserver,resourcemanager,zookeeper','port_list':'hdfs__dfs_namenode_http_address_port=50070,hdfs__dfs_namenode_https_address_port=50470,hdfs__dfs_namenode_servicerpc_address_port=50901,hdfs__dfs_namenode_rpc_address_port=50900,hdfs__dfs_datanode_address_port=50010,hdfs__dfs_datanode_ipc_address_port=50020,hdfs__dfs_datanode_http_address_port=50075,hdfs__qjournal_http_port=8480,hdfs__qjournal_port=8485,zookeeper__zookeeper_election_port=38880,zookeeper__zookeeper_client_port=21810,zookeeper__zookeeper_leader_port=28880,hive__hive_server2_thrift_port=59300,hive__hive_metastore_port=19083,hive__hive_server_thrift_port=59200,yarn__yarn_nm_port=50841,yarn__yarn_nm_localizer_port=50840,yarn__mapreduce_shuffle_port=18080,yarn__yarn_nm_webapp_port=50088,yarn__mapreduce_jobhistory_webapp_port=50888,yarn__mapreduce_jobhistory_port=50120,yarn__yarn_rm_scheduler_port=50030,yarn__yarn_rm_webapp_port=50088,yarn__yarn_rm_port=50040,yarn__yarn_rm_admin_port=50141,yarn__yarn_rm_resource_tracker_port=50025,hbase__hbase_resigionserver_info_port=50630,hbase__hbase_resigionserver_port=50620,hbase__hbase_master_info_port=50610,hbase__hbase_master_port=50600,impala__impala_state_store_web_port=25010,impala__impala_state_store_port=24000,impala__impala_server_beeswax_port=21000,impala__impala_server_web_port=25000,impala__impala_backend_port=22000,impala__impala_server_hs2_port=21050'}
    PARAMS = {'services': 'datanode','port_list':'hdfs__dfs_namenode_http_address_port=50070,hdfs__dfs_namenode_https_address_port=50470,hdfs__dfs_namenode_servicerpc_address_port=50901,hdfs__dfs_namenode_rpc_address_port=50900,hdfs__dfs_datanode_address_port=50010,hdfs__dfs_datanode_ipc_address_port=50020,hdfs__dfs_datanode_http_address_port=50075,hdfs__qjournal_http_port=8480,hdfs__qjournal_port=8485,zookeeper__zookeeper_election_port=38880,zookeeper__zookeeper_client_port=21810,zookeeper__zookeeper_leader_port=28880,hive__hive_server2_thrift_port=59300,hive__hive_metastore_port=19083,hive__hive_server_thrift_port=59200,yarn__yarn_nm_port=50841,yarn__yarn_nm_localizer_port=50840,yarn__mapreduce_shuffle_port=18080,yarn__yarn_nm_webapp_port=50088,yarn__mapreduce_jobhistory_webapp_port=50888,yarn__mapreduce_jobhistory_port=50120,yarn__yarn_rm_scheduler_port=50030,yarn__yarn_rm_webapp_port=50088,yarn__yarn_rm_port=50040,yarn__yarn_rm_admin_port=50141,yarn__yarn_rm_resource_tracker_port=50025,hbase__hbase_resigionserver_info_port=50630,hbase__hbase_resigionserver_port=50620,hbase__hbase_master_info_port=50610,hbase__hbase_master_port=50600,impala__impala_state_store_web_port=25010,impala__impala_state_store_port=24000,impala__impala_server_beeswax_port=21000,impala__impala_server_web_port=25000,impala__impala_backend_port=22000,impala__impala_server_hs2_port=21050'}
    descriptors = metric_init(PARAMS)
    for d in descriptors:
        print (('%s = %s') % (d['name'], d['format'])) % (d['call_back'](d['name'])) + '  %s' % d['units']
    time.sleep(4)
    for d in descriptors:
        print (('%s = %s') % (d['name'], d['format'])) % (d['call_back'](d['name'])) + '  %s' % d['units']
    time.sleep(5)
    for d in descriptors:
        print (('%s = %s') % (d['name'], d['format'])) % (d['call_back'](d['name'])) + '  %s' % d['units']

