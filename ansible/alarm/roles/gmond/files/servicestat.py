# !/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import psutil
import re
import os
import time
_PIPE = subprocess.PIPE

descriptors = []
NAME_PREFIX = 'servicestat'
LABELS = ['exist', 'cpu', 'mem', 'io_count', 'io_bytes']
UNITS = ['', '%', 'Bytes', 'num', 'bytes']
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

NOW_CACHE = {}
LAST_UPDATE = -1

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

def is_exist(pid):
    cmd = "ps aux | grep %d | grep -v grep | wc -l" % int(pid)
    (out, err, code,) = execute(cmd)
    if code == 0:
        if int(out) == 1 :
            return True
    return False

def init_cache():
    global NOW_CACHE, SERVICES, LAST_UPDATE
    now  = int(time.time())
    if now < 0 or now - LAST_UPDATE > 5:
        #INIT AGAIN
        NOW_CACHE = {}
        for service in SERVICES:
            temp = {}
            pid = get_pid(service)
            if pid == None:
                continue
            if is_exist(pid):
                temp['exist_exist'] = 1
            try:
                ps = psutil.Process(int(pid))
                temp['cpu_percent'] = float(ps.cpu_percent(0.1))
                temp['mem_rss'] = float(ps.memory_info()[0])
                temp['mem_vms'] = float(ps.memory_info()[1])
                temp['io_count_read'] = float(ps.io_counters()[0])
                temp['io_count_write'] = float(ps.io_counters()[1])

                temp['io_bytes_read'] = float(ps.io_counters()[3]) / 8
                temp['io_bytes_write'] = float(ps.io_counters()[4]) / 8
            except:
                pass
            NOW_CACHE[service] = temp
        LAST_UPDATE = now
    return NOW_CACHE

def get_value(name):
    """Return a value for the requested metric"""
    _value = 'unknown'
    cpu_percent = 0
    mem_rss = 0
    mem_vms = 0
    io_count_read = 0
    io_count_write = 0
    io_bytes_read = 0
    io_bytes_write = 0

    global SERVICES, LPARAMS

    name_parser = re.match("^%s_(.*)_(exist|cpu|mem|io_count|io_bytes)_(.*)$" % NAME_PREFIX, name)
    service_name = name_parser.group(1)
    label = name_parser.group(2)
    metric = name_parser.group(3)
    want_name = "%s_%s" % ( label, metric )

    now_cache = init_cache()
    if now_cache.has_key(service_name) and now_cache[service_name].has_key(want_name):
        return now_cache[service_name][want_name];
    else:
        return 0

def metric_init(params):
    global descriptors, LPARAMS, SERVICES, LABELS, PID_FILE_MAP
    LPARAMS = params

    SERVICES = []

    for service in params['services'].strip().split(","):
        if not PID_FILE_MAP.has_key(service) :
            continue    
        SERVICES.append(service)

        metrics = ['percent']

        for i in range(len(LABELS)):
            if LABELS[i] == 'exist':
                metrics = ['exist']
            if LABELS[i] == 'cpu':
                metrics = ['percent']
            if LABELS[i] == 'mem':
                metrics = ['rss', 'vms']
            if LABELS[i] == 'io_count' or LABELS[i] == 'io_bytes':
                metrics = ['read', 'write']

            for metric in metrics:
                _name = "%s_%s_%s_%s" % (NAME_PREFIX, service, LABELS[i], metric)
                descriptors.append({
                    'name': _name,
                    'call_back': get_value,
                    'time_max': 60,
                    'value_type': 'float',
                    'units': UNITS[i],
                    'slope': 'both',
                    'format': '%0.2f',
                    'description': "uhp services",
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
    PARAMS = {'services': 'gundan,datanode,hbasemaster,historyserver,hivemetastore,hiveserver,hiveserver2,impalaserver,impalastatestore,namenode,nodemanager,qjm,regionserver,resourcemanager,zookeeper'}
    descriptors = metric_init(PARAMS)
    for d in descriptors:
        print (('%s = %s') % (d['name'], d['format'])) % (d['call_back'](d['name'])) + '  %s' % d['units']

