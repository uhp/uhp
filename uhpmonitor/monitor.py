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
import lockfile
import lockfile.pidlockfile

sys.path.append(os.path.join(os.getenv('UHP_HOME'), "uhpcommon"))

import config 
import database
from model.instance import Instance
from sqlalchemy import and_

# 用于跳出多层循环
class FoundException(Exception):pass

def query_all_instance():
    """query all instance 
    
    like sql : "SELECT id, service, role, hostname FROM instance"
    
    return: [ instance ]
    """
  
    session = database.getSession(False)
    try:
        rows = session.query(Instance)
    finally:
        session.close()
    return rows 

def run_update(instance):
    session = database.getSession(False)
    try:
        session.query(Instance).filter(Instance.id==instance.id) \
                .update({Instance.health: instance.health,
                    Instance.monitor_time: instance.monitor_time,
                    Instance.msg: instance.msg})
        session.commit()
    finally:
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
        log.exception("")

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
        log.exception("")

def update_ins_health(ins, health, msg):
    try:
        log.info("instance[%d] host[%s] check:%s" % (ins.id, ins.host, msg))
        ins.msg = msg 
        ins.health = health 
        ins.monitor_time = int(time.time())
        run_update(ins)
    except Exception, e:
        log.exception("")

def test():
    inv = ansible.inventory.Inventory(config.ansible_host_list)
    #check_one_instance(1, 'hadoop2', ['9922'])
    sys.exit(0)

def check_one_host(host, ins_ports_key_list):
    try:
        check_one_host_(host, ins_ports_key_list)
    except:
        log.exception("")

def check_one_host_(host, ins_ports_key_list):
    """对同一台机器上的所有实例进行监控

    @param host          : 机器
    @param ins_ports_key : [(ins obj, [ports], key)]
    """

    log.debug("check all instance on host[%s]", host)
   
    ins_dict = {}
    # usage: $myname "insid:port,port,-port:key" "..."
    script = config.monitor_script_checkport
    for ins, ports, key in ins_ports_key_list:
        script += " %d:%s:%s " % (ins.id, ",".join(ports), key)
        ins_dict[ins.id] = ins 
    cmd = ["/usr/bin/env", "ansible", "-s", "-i", config.ansible_host_list, ins.host, "-m", "script", "-a", script]
    
    log.debug("cmd="+" ".join(cmd))
    log.debug("host[%s], runner.run", host)

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t = int(time.time())
    process_queue.put((t, p))
    out = p.stdout.read() 
    p.wait()
    
    log.debug("host[%s], runner.run end", host)

    if p.returncode != 0:
        raise Exception("check ins[%d] on host[%s] is error, return code:%d" % (ins.id, ins.host, p.returncode))
    
    log.debug("subprocess out = %s" % out)

    # 解析
    # 更新数据
    try:
        json_str = out.split(">>",1)[1]
        json_obj = json.loads(json_str)

        stdout = json_obj['stdout']
        #通过特别标记获取脚本的输出，避免ansible的其它输出的影响
        s=stdout.index(":CHECKSTART:")+len(":CHECKSTART:")
        e=stdout.index(":CHECKEND:")
        check_out = stdout[s:e] 
        log.debug("check_out: %s" % check_out)
        insid_state_msg_list = json.loads(check_out)
        log.debug(insid_state_msg_list)
        for insid_state_msg in insid_state_msg_list:

            insid = insid_state_msg['insid']
            state = insid_state_msg['state']
            msg   = insid_state_msg['msg']
            msg   = json.dumps(msg)

            ins    = ins_dict[insid]
            health = Instance.HEALTH_UNKNOW

            if state == 0: # ok
                health = Instance.HEALTH_HEALTHY
            elif state == 1: # port lask
                health = Instance.HEALTH_UNHEALTHY
            elif state == 2: # donw
                health = Instance.HEALTH_DOWN

            update_ins_health(ins, health, msg)
    except:
        log.exception("")
    
    log.debug("host[%s], runner.run check ok", host)
    return out

# @param instance_ports: [(ins, [port])]
def check_all_instance(instance_ports):
    # host_ins_map = {} # {host:[(ins,[port])]}
    datas = [(item, {}) for item in instance_ports]
    reqs = threadpool.makeRequests(check_one_instance, datas, run_success, run_fault)
    [pool.putRequest(req) for req in reqs]
    log.debug("pool.wait for check instance")
    pool.wait()
    log.debug("pool.wait end")

def check_all_host(host_ins_map):
    """检查全部机器上的全部实例

    @param host_ins_map = {} # {host:[(ins,[port], key)]}
    """

    datas = [(item, {}) for item in host_ins_map.iteritems()]
    reqs = threadpool.makeRequests(check_one_host, datas, None, None)
    [pool.putRequest(req) for req in reqs]
    log.debug("pool.wait for check instance")
    pool.wait()
    log.debug("pool.wait end")

def check():
    """完整的一轮端口检查

    需要知道每台机器，每个角色的端口，
    一个角色可能有多个端口
    主服务端口来自约定
    """

    inv = ansible.inventory.Inventory(config.ansible_host_list)

    instance_ports = {} # {instance:([port],key)}

    # 标记那些key名称是特性: flag=True:必有端口 flag=False:可有可无
    # {service:{key:flag}}
    port_key_flag = config.port_key_flag

    # 收集待判定端口
    for ins in query_all_instance():
        try:
            ports = []
            
            if ins.service not in port_key_flag: continue
            if ins.role not in port_key_flag[ins.service]: continue
            port_keys = port_key_flag[ins.service][ins.role]
       
            key = ins.role # 默认使用角色名
            host_vars = inv.get_variables(ins.host) or {}
            for (port_key, flag) in port_keys.iteritems():
                if port_key == "key": 
                    key = flag
                    continue
                host_vars_find_key = ins.service + '__' + port_key
                if host_vars_find_key not in host_vars:
                    # 跳过此ins
                    raise FoundException("special key[%s] not exists for host[%s]" % (host_vars_find_key, ins.host))
                port = host_vars[host_vars_find_key]
       
                if not flag: port = "-" + port
                ports.append(port)

            if ports:
                instance_ports[ins] = (ports, key)
        except FoundException, e:
            log.exception(e)
    
    # 同一个host上的instance同时检查
    host_ins_map = {} # {host:[(ins,[port],key)]}
    for ins, (ports, key) in instance_ports.items():
        if ins.host not in host_ins_map:
            host_ins_map[ins.host] = []
        host_ins_map[ins.host].append((ins, ports, key))

    check_all_host(host_ins_map)

def start_check_timeout_process():
    def _terminate_process(p):
        try:
            if p.poll() != None: # terminateed
                return
            log.warn("p timeout, terminate it")
            p.terminate()
        except Exception, e:
            log.exception("")

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
                log.exception("")
    
    thread.start_new_thread(_inner_check_timeout_process, (None,))

def work():
    #test()
    global pool
    pool = threadpool.ThreadPool(config.monitor_thread_numb) 
    
    start_check_timeout_process()
   
    while True:
        try:
            log.debug("check ...")
            check()
            log.debug("check over")
            time.sleep(float(config.monitor_timer_interval))
        except:
            log.exception("")

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
        log.exception("")
    log.info("end!")

if __name__ == "__main__": 
    main()
else: 
    print "no import me!"
    sys.exit(-1)
