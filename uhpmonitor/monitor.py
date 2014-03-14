#!/usr/bin/env python
# coding=utf-8

# @author: zhaigy@ucweb.com
# @date  : 2014-01-23

'''
Daemon
定时执行
'''

import os
import sys
import string
import optparse
import logging
import logging.config
import daemon
import time
import snakemq.link
import snakemq.packeter
import snakemq.messaging
import snakemq.message
import threading
import threadpool
import subprocess
import tempfile
import json
import re
import Queue
import thread
import ansible
import ansible.inventory
import ansible.playbook
from ansible import callbacks
from ansible import utils
from ansible.runner import Runner
from ansible import callbacks
import pdb
from common import * 
import lockfile
import lockfile.pidlockfile

sys.path.append(os.path.join(os.getenv('UHP_HOME'), "uhpcommon"))
import config 
import database
from model.instance import Instance
from sqlalchemy import and_

def query():
    """query special id tasks
    
    like sql : "SELECT id, service, role, hostname FROM instance"
    
    return: [ instance ]
    """
  
    session = database.getSession(False)
    rows = session.query(Instance)
    session.close()
    return rows 

def run_update(instance):
    session = database.getSession(False)
    session.query(Instance).filter(Instance.id==instance.id) \
            .update({Instance.health: instance.health,
                Instance.monitor_time: instance.monitor_time,
                Instance.msg: instance.msg})
    session.commit()
    session.close()

def run_success(request, result):
    try:
        ins = request.args[0]
        run_ins_success(ins, result)
    except Exception, e:
        log.exception("save error")

def run_ins_success(ins, result):
    try:
        log.debug("run success")
        log.info("instance[%d] host[%s] check ok: %s" % (ins.id, ins.host, result))
        if ins.msg is None: ins.msg = "" 
        ins.msg += result
        ins.health = Instance.HEALTH_HEALTHY
        ins.monitor_time = int(time.time())
        run_update(ins)
    except Exception, e:
        log.exception("save error")

def run_fault(request, exc_info):
    try:
        ins = request.args[0]
        run_ins_fault(ins, exc_info)
    except Exception, e:
        log.exception(e)

def run_ins_fault(ins, exc_info):
    try:
        log.debug("run fault")
        err = exc_info[1]
        errinfo = str(err)
        log.error("instance[%d] host[%s] check fault: %s" % (ins.id, ins.host, errinfo))
        if ins.msg is None: ins.msg = "" 
        ins.msg += errinfo
        ins.health = Instance.HEALTH_UNHEALTHY
        ins.monitor_time = int(time.time())
        run_update(ins)
    except Exception, e:
        log.exception(e)

def test():
    inv = ansible.inventory.Inventory(config.ansible_host_list)
    check_one_instance(1, 'hadoop2', ['9922'])
    sys.exit(0)

def check_one_instance(ins, ports):
    return execute(ins, ports)
    #try:
    #    return 
    #except Exception, e:
    #    log.exception(e)

# @param ins   : instance object
# @parma ports : [port]
def execute(ins, ports):
    log.debug("check one instance, host[%s]", ins.host)
    
    script = config.monitor_script_checkport
    for port in ports:
        script += " " + port[0]
   
    cmd = ["ansible", "-i", config.ansible_host_list, ins.host, "-m", "script", "-a", script]
    log.debug("cmd="+" ".join(cmd))
    log.debug("host[%s], runner.run", ins.host)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t = int(time.time())
    process_queue.put((t, p))
    out = p.stdout.read() 
    p.wait()
    
    log.debug("host[%s], runner.run end", ins.host)
    if p.returncode != 0:
        raise Exception("check ins[%d] on host[%s] is error, return code:%d" % (ins.id, ins.host, p.returncode))
    
    log.debug("subprocess out = %s" % out)
    ins.msg = out

    stdout = ""
    for line in out.split("\n"):
        line = line.strip()
        if line.startswith("\"stdout\":"):
            stdout = line.split(':', 1)[1]
            stdout = stdout.strip(" \"")
            break
    
    log.debug("stdout: %s" % stdout)
    checked_ports = set([port for port in stdout.split(r'\n') if port]) 
    log.debug(checked_ports)
    exists_ports = []
    not_exists_ports = []
    is_fail = False
    for (port, flag) in ports:
        if port in checked_ports:
            exists_ports.append(port)
            continue
        not_exists_ports.append(port)
        if flag:
            is_fail = True

    out = ("port[%s] exists" % ",".join(exists_ports)) if exists_ports else ""
    out2 = ("port[%s] not exists" % ",".join(not_exists_ports)) if not_exists_ports else ""
    
    if out and out2: 
        out += ", " + out2
    elif out2:
        out = out2

    if is_fail:
        log.debug("host[%s], runner.run check fail", ins.host)
        raise Exception(out)
    
    log.debug("host[%s], runner.run check ok", ins.host)
    return out

# @param instance_ports: [(ins, [port])]
def check_all_instance(instance_ports):
    datas = [(item, {}) for item in instance_ports]
    reqs = threadpool.makeRequests(check_one_instance, datas, run_success, run_fault)
    [pool.putRequest(req) for req in reqs]
    log.debug("pool.wait for check instance")
    pool.wait()
    log.debug("pool.wait end")

def check():
    # 需要知道每台机器，每个角色的端口，
    # 一个角色可能有多个端口，这里仅对应一个主服务端口
    # 主服务端口来自约定
    inv = ansible.inventory.Inventory(config.ansible_host_list)

    instance_ports = {} # {instance:[port]}
    # 标记那些key名称是特性 flag=True:必有端口 flag=False:可有可无
    # {service:{key:flag}}
    port_key_flag = config.port_key_flag

    instances = query() 
    for ins in instances:
        # 收集待判定端口
        ports = []
        
        if ins.service not in port_key_flag: continue
        if ins.role not in port_key_flag[ins.service]: continue
        port_keys = port_key_flag[ins.service][ins.role]
        
        host_vars = inv.get_variables(ins.host) or {}
        for (port_key, flag) in port_keys.iteritems():
            host_vars_find_key = ins.service + '__' + port_key
            if host_vars_find_key not in host_vars:
                raise Exception("special key[%s] not exists for host[%s]" % (host_vars_find_key, ins.host))
            port = host_vars[host_vars_find_key]
        
            port = (port, flag)
            ports.append(port)

        if ports:
            instance_ports[ins] = ports
    
    #check_all_instance(instance_ports)
    # 限制同一个host只有一个
    host_ins_map = {} # {host:[(ins,[port])]}
    for ins, ports in instance_ports.items():
        if ins.host not in host_ins_map:
            host_ins_map[ins.host] = []
        host_ins_map[ins.host].append((ins, ports))

    while host_ins_map:
        batch = [] # [(ins, [port])]
        for host in host_ins_map.keys():
           batch.append(host_ins_map[host].pop())
           if not host_ins_map[host]: 
               host_ins_map.pop(host)
        
        log.debug("check_all_instance on host[%s]", ",".join([str(it[0].id) for it in batch]))
        check_all_instance(batch)
        log.debug("check_all_instance end")

def start_check_timeout_process():
    def _terminate_process(p):
        try:
            if p.poll() != None: # terminateed
                return
            p.terminate()
        except Exception, e:
            log.exception(e)

    def _inner_check_timeout_process(arg):
        while True:
            try:
                log.debug("check timeout process")
                try:
                    (t, p) = process_queue.get(timeout=3.0)
                    if p.poll() != None: # terminateed
                        continue
                    # no terminate
                    now = int(time.time())
                    kill_time = config.monitor_process_timeout - (now - t)
                    
                    if kill_time <= 0:
                        _terminate_process(p)
                        continue

                    time.sleep(kill_time)
                    _terminate_process(p)
                    
                except Queue.Empty:
                    log.debug("no process running")
                    pass
            except Exception, e:
                log.exception(e)
    
    thread.start_new_thread(_inner_check_timeout_process, (None,))

def work():
    #test()
    global pool
    pool = threadpool.ThreadPool(config.monitor_thread_numb) 
    
    start_check_timeout_process()
   
    while True:
        log.debug("check ...")
        check()
        log.debug("check over")
        time.sleep(float(config.monitor_timer_interval))

def valid_config():
    k = "port_key_flag"
    v = config.port_key_flag
    if v.startswith('file://'):
        log.debug("config: %s is file[%s]" % (k, v))
        v = v.replace('file://', '')
        v = open(v, 'r').read()
    config.port_key_flag = json.loads(v)
    log.debug("config: %s = %s" % (k, config.port_key_flag))

###########################################################
os.chdir(config.uhphome)
APP = os.path.splitext(os.path.basename(sys.argv[0]))[0]
logging.config.fileConfig("%s/uhp%s/conf/logging.conf" % (config.uhphome, APP))
log   = logging.getLogger(APP)
pool  = None
#ins_process_map = {} # {ins:[p, start-time, end-time]}
process_queue = Queue.Queue() # Queue((time, p))

def main():
    log.info("start...")
    try:
        valid_config()
        pidfile = "pids/%s/%s.pid" % (APP, APP)
        pidfile = lockfile.pidlockfile.PIDLockFile(pidfile)
        files_preserve=[logging.root.handlers[1].stream.fileno()]
        dmn = daemon.DaemonContext(None, os.getcwd(), pidfile=pidfile, files_preserve=files_preserve)
        dmn.open()
        work()
    except Exception as e:
        log.exception(e)
    log.info("end!")

if __name__ == "__main__": 
    main()
else: 
    print "no import me!"
    sys.exit(-1)
