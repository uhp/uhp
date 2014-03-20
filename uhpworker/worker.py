#!/usr/bin/env python
# coding=utf-8

# @author: zhaigy@ucweb.com
# @date  : 2014-01-23

'''
Daemon
逐个执行Task
'''

import os
import sys
import string
import logging
import logging.config
import daemon
import time
import snakemq.link
import snakemq.packeter
import snakemq.messaging
import snakemq.message
import thread
import threading
import threadpool
import tempfile
import ansible
import ansible.playbook
import ansible.callbacks
import ansible.utils
from multiprocessing import Pool
from multiprocessing import Process
import Queue
import lockfile
import lockfile.pidlockfile
import pdb
import traceback
import subprocess

sys.path.append(os.path.join(os.getenv('UHP_HOME'), "uhpcommon"))
import config
import database
from model.task import Task
from sqlalchemy import and_

def query_tasks(ids=None):
    """query special id tasks
    
    param:
        ids: [ taskid ]
  
    return: [ task ]
    """
    session = database.getSession(False)
    tasks   = session.query(Task).filter(
            and_(Task.status.in_([Task.STATUS_INIT]),
                Task.taskType.in_(['ansible', 'shell'])))
    if ids:
        tasks = tasks.filter(Task.id.in_(ids))
    session.close()
    return tasks 

def run_update(task):
    session = database.getSession(False)
    session.query(Task).filter(Task.id==task.id) \
            .update({Task.status: task.status,
                Task.result: task.result,
                Task.msg: task.msg})
    session.commit()
    session.close()

def update_running(task):
    log.debug("update task running")
    task.status = Task.STATUS_RUNNING
    task.msg = ""
    run_update(task)

def run_success(request, result):
    try:
        task = request.args[0]
        run_task_success(task)
    except:
        log.exception("save error")

def run_task_success(task):
    log.error("task[%d] is ok" % task.id)
    task.status = Task.STATUS_FINISH
    task.result = Task.RESULT_SUCCESS
    msg = task.msg or ""
    msg = msg + "OK"
    task.msg = msg
    run_update(task)

def run_fault(request, exc_info):
    try:
        task = request.args[0]
        run_task_fault(task, exc_info)
    except:
        log.exception("save error")

def run_task_fault(task, exc_info):
    err = exc_info[1]
    errinfo = str(err)
    #exc_tb = exc_info[2]
    #for filename, linenum, funcname, source in traceback.extract_tb(exc_tb):
    #    print "%-23s:%s '%s' in %s()" % (filename, linenum, source, funcname)
    log.error("task[%d] is error: %s" % (task.id, errinfo))
    task.status = Task.STATUS_FINISH
    task.result = Task.RESULT_FAILED
    if errinfo.startswith('ansible return code:'):
        return_code = errinfo.replace('ansible return code:', '')
        return_code = int(return_code)
        if return_code < 0:
            task.result = Task.RESULT_KILLED
    msg = task.msg or ""
    msg = msg + errinfo 
    task.msg = msg
    run_update(task)

def update_msg(task, line):
    session = database.getSession(False)
    msg = task.msg or ""
    msg = msg + line
    task.msg = msg
    session.query(Task).filter(Task.id==task.id) \
            .update({Task.msg: task.msg})
    session.commit()
    session.close()

# 把输出转到表的msg字段，注意是累加的
class MyOut(object):
    #encoding = "UTF-8"
    def __init__(self, task):
        self.task = task

    def write(self, s):
        update_msg(self.task, s)

class Executor(object):
    def execute(self, task):
        pass

class ShellExecutor(Executor):
    pass

class AnsibleExecutor(Executor):
   
    def __init__(self):
        self.service_path = config.service_path
  
    # task: task object
    # return: ansible.playbook.PlayBook object
    def parse_task(self, task):
        playbook = None
  
        if not task.host:
            # for service
            playbook = "%s/%s_%s.yml" % (self.service_path, task.task, task.service)
        else:
            # for instance
            host = task.host
            role = task.role
  
            outFile = tempfile.NamedTemporaryFile(delete=False)
            outFile.write("---\n")
            outFile.write("# auto generate\n")
            outFile.write("- hosts: %s\n" % host)
            outFile.write("  tasks:\n")
            outFile.write("  - include: %s/roles/%s/tasks/%s.yml" % (self.service_path, role, task.task) )
            outFile.close()
            playbook = outFile.name
  
        log.debug("playbook:%s", playbook)
  
        return playbook
  
    # return ""
    # throw RuntimeException(msg) if fail
    def execute(self, task):
        pb = self.parse_task(task)
        
        # 重定向
        myout      = MyOut(task)
        #tmp_out    = sys.stdout
        #sys.stdout = myout
        
        cmd = ["/usr/bin/ansible-playbook", "-i", config.ansible_host_list, pb]
        cmd_str = "cmd="+" ".join(cmd)
        myout.write(cmd_str)
        myout.write("\n")
        log.debug(cmd_str)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=config.uhphome, env={'UHP_HOME':config.uhphome})
        task_process_map[task.id] = p
        while p.poll() == None:
            line = p.stdout.readline() 
            while line: 
                myout.write(line)
                line = p.stdout.readline() 

        if p.returncode == 0:
            return "OK"
        
        raise Exception("ansible return code:%d" % p.returncode)

# run in 
def run(task):
    try:
        log.debug("run task: %d" % task.id)
        if(task.taskType == "ansible" ):
            executor = AnsibleExecutor()
        elif(task.taskType == "shell"):
            executor = ShellExecutor()
        else:
            raise Exception("task type[%s] is not known." % task.taskType)
   
        update_running(task)
        try:
            return executor.execute(task)
        finally:
            try:
                task_process_map.pop(task.id)
            except Exception:
                pass
    except BaseException, e:
        raise Exception(e)

# 使用多线程
def run_tasks(tasks):
    log.debug("run tasks") 
    
    datas = [((task,), {}) for task in tasks]
    reqs = threadpool.makeRequests(run, datas, run_success, run_fault)
    [pool.putRequest(req) for req in reqs]
    pool.wait() # 阻塞直到完成

    log.debug("run tasks over") 

# ids: [id]
# 会阻塞，直到全部完成
def do_tasks_by_ids(ids):
    try:
        tasks = query_tasks(ids)
        
        # 分组，是因为同Host不能同时执行Yum，为了安全，限定一批次的Task是在不同Host上执行的
        group = {}
        for t in tasks:
            if t.host not in group:
                group[t.host] = []
            group[t.host].append(t)

        while group:
            # 按host选出一组Task
            checked_tasks = []
            for host in group.keys():
                checked_tasks.append(group[host].pop())
                if not group[host]: group.pop(host)
            run_tasks(checked_tasks)
    except:
        log.exception('do tasks by ids[%s] error' % ",".join(ids))

# kill 对应Process，更新数据库
def kill_running_task(id):
    id = int(id)
    log.debug("kill running task[%d]" % id)
    ids = task_process_map.keys()
    if id not in ids: 
        log.debug("running task[%d] not found" % id)
        return
    
    p = task_process_map.get(id)

    if p and p.poll() == None:
        # p exists, and alive, kill 
        try:
            log.debug("kill task[%d]" % id)
            p.terminate()
        except:
            log.exception('kill process[%s] error' % p.name)
            return
    else:
        log.debug("task[%d] not running" % id)

def on_recv(conn, ident, message):
    try:
        log.info("on_recv: %s, %s", ident, message.data)
        msg = message.data
        if msg.startswith('killtask:'):
            id = msg.replace('killtask:', '')
            kill_running_task(id)
        else:
            ids = msg.split(',')
            task_queue.put(ids, True)
    except:
        log.exception('deal message error')

def start_mq():
    my_link = snakemq.link.Link()
    my_link.add_listener((config.mq_host, config.mq_port))
    my_packeter = snakemq.packeter.Packeter(my_link)
    my_messaging = snakemq.messaging.Messaging(APP, "", my_packeter)
    my_messaging.on_message_recv.add(on_recv)
  
    my_link.loop()

def start_check_omitted_task():
    def _check_omitted_task():
        tasks = query_tasks()
        ids = [str(task.id) for task in tasks]
        if ids:
            task_queue.put(ids)
        
    def _inner_check_omitted_task(arg):
        while True:
            try:
                log.debug("check omitted task")
                _check_omitted_task()
            except Exception, e:
                log.exception(e)
            time.sleep(10)
  
    thread.start_new_thread(_inner_check_omitted_task, (None,))

def start_task_work():
    def _task_work(something):
        log.info("start task work thread")
        # 管理Run Task进程
        while True:
            try:
                ids = task_queue.get(True, timeout=3.0)
                log.debug("get tasks[%s] to run" % ",".join(ids))
                # 执行Task会阻塞
                try:
                    do_tasks_by_ids(ids)
                except:
                    log.exception('do tasks by ids is error')
            except Queue.Empty:
                log.debug("no task to run")

    thread.start_new_thread(_task_work, (None,))

def work():
    global pool
    pool = threadpool.ThreadPool(config.worker_thread_numb)
    start_task_work()
    start_check_omitted_task()
    start_mq()

###########################################################
os.chdir(config.uhphome)
APP = os.path.splitext(os.path.basename(sys.argv[0]))[0]
logging.config.fileConfig("%s/uhp%s/conf/logging.conf" % (config.uhphome, APP))
log = logging.getLogger(APP)
pool = None
task_process_map = {}
task_queue = Queue.Queue()

def main():
    log.info("start...")
    try:
        pidfile = "pids/%s/%s.pid" % (APP, APP)
        pidfile = lockfile.pidlockfile.PIDLockFile(pidfile)
        files_preserve=[logging.root.handlers[1].stream.fileno()]
        dmn = daemon.DaemonContext(None, os.getcwd(), pidfile=pidfile, files_preserve=files_preserve)
        dmn.open()
        work()
    except Exception, e:
        log.exception(e)
    log.info("end!")

if __name__ == "__main__": 
    main()
else:
    print "no import me!"
    sys.exit(1)

