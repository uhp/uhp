#!python
# -*- coding: UTF-8 -*-

import time  
import thread 
import threading
import logging
import json
import sys,os

from sqlalchemy import and_

import database
import config
from model.instance import Instance
from model.host_group_var import Host,GroupVar
from model.task import Task
from model.services import Service
from model.callback import CallBack

callback_log = logging.getLogger("callback.lib")
    
class CallBackMap:
    
    def __init__(self):
        pass           
         
    def test(self,session,task,params):
        print task
        print params["a"]
        
    def changeHostToReady(self,session,task,params):
        if task.result == Task.RESULT_SUCCESS :
            session.query(Host).filter( Host.hostname == task.host).update({Host.status:Host.STATUS_READY})
            session.commit()
            
    def dealAddInstance(self,session,task,params):
        #一般的单个机器任务
        if task.result == Task.RESULT_SUCCESS :
            database.update_instance(session,task.host,task.role,Instance.STATUS_STOP)
        else:
            database.del_instance(session,task.host,task.role)
            
    def dealDelInstance(self,session,task,prams):
        if task.result == Task.RESULT_SUCCESS :
            database.del_instance(session,task.host,task.role)

    
    
def begin():
    thread.start_new_thread(run,())
    
def run():
    session = database.getSession(False)
    logCount = 0 ;
    while True:
        cbs = session.query(CallBack).filter( CallBack.status == CallBack.STATUS_CHECK )
        idList = []
        cbcache = {}
        
        for cb in cbs:
            idList.append(cb.taskid)
            if not cbcache.has_key(cb.taskid) :
                cbcache[cb.taskid]=[]
            cbcache[cb.taskid].append(cb)
        
        logCount = logCount + 1
        if logCount == 10:
            callback_log.info("find " + str( len(idList) ) + " need to callback" )
            logCount = 0
        if len(idList) != 0 :
            for task in session.query(Task).filter(Task.id.in_(idList)):
                callback_log.info(str(task.id)+" "+str(task.status))
                if task.status ==  Task.STATUS_FINISH:
                    remove_callback(session,task.id)
                    callback_log.info("remove "+str(task.id) )
                    if cbcache.has_key(task.id) :
                        for cb in cbcache[task.id]:
                            callback_log.info("call back "+str(cb.taskid)+" "+cb.func+" "+cb.params )
                            deal_callback(session, task, cb.func, json.loads(cb.params))
#         session.
        session.commit()
        #session.flush()
        time.sleep(3)

def add_callback(session,taskid,fun,params={}):
    cb = CallBack(taskid,fun,json.dumps(params))
    session.add(cb)
    session.commit()
    
def remove_callback(session,taskid):   
    session.query(CallBack).filter( CallBack.taskid == taskid ) \
        .update({CallBack.status:CallBack.STATUS_PASS});
    session.commit()
    
def deal_callback(session,task,func,params):
    cbm = CallBackMap()
    callback_log.info(dir(cbm))
    if hasattr(cbm, func) :
        fun = getattr(cbm, func);
        if callable(fun):
            apply(fun,(session,task,params))
        else:
            callback_log.error(func+" is not callable")
    else:
        callback_log.error("unable to find "+func+" in CallBackMap")
    
if __name__ == "__main__":
    try:
        deal_callback(database.session,None,"changeHostToReady",{"host":"hadoop1"})
    except:
        callback_log.exception("begin find exception")
    
    