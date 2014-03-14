# -*- coding: UTF-8 -*-
import time  
import thread 
import threading
import logging
import json

from sqlalchemy import and_

import config
import database
from model.instance import Instance
from model.host_group_var import Host,GroupVar
from model.task import Task
from model.services import Service
from controller import callback_lib
from controller import mm

mutex = threading.Lock()
cache = {}
asyncid = 0
app_log = logging.getLogger("tornado.application")

#async 异步任务状态的修改
def async_run(fun,obj):
    thread.start_new_thread(fun,obj)

def async_setup():
    mutex.acquire()
    global asyncid 
    global cache
    asyncid -= 1
    id = asyncid
    if not cache.has_key(id) :
        cache[id] = {}
    mutex.release()
    return id;
    
def async_set(id,name,value):
    mutex.acquire()
    global cache
    cache[id][name]=value
    mutex.release()
    
def async_push(id,name,value):
    mutex.acquire()
    global cache
    if cache.has_key(id) and cache[id].has_key(name):
        cache[id][name]+="\n"+value
    else:
        cache[id][name]="\n"+value
    mutex.release()

def async_get(id,name,default):
    #锁定
    temp = ""
    mutex.acquire()
    global cache
    if cache.has_key(id) and cache[id].has_key(name):
        temp = cache[id][name]
    mutex.release()
    if temp=="" :
        return default;
    return temp

def async_pop(id,name,default):
    #锁定
    temp = ""
    mutex.acquire()
    global cache
    if cache.has_key(id) and cache[id].has_key(name):
        temp = cache[id][name]
        #使用追加的日志方式
        #cache[id][name]=""
    mutex.release()
    if temp=="" :
        return default;
    return temp

def async_remove(id):
    mutex.acquire()
    global cache
    cache.pop(id)
    mutex.release()
   
#添加机器的服务 
def add_host(asyncId,hosts,user,port,passwd,sudopasswd):  
    #保留10秒后清除
    session=database.getSession()
    idMap = {}
    progress = 0 ;
    progressStep = int( (100-10)/len(hosts) )
    
    #创建任务
    for hostName in hosts:
        taskId = database.build_task(session,"async","add_host",hostName,"machine","connect")
        idMap[hostName] = taskId
    
    async_push(asyncId,"progressMsg","build task")
    progress = 10
    async_set(asyncId,"progress",progress) 

    #交给ansible运行
    async_push(asyncId,"progressMsg","ansible connect and install yum python json.As the yum update automatically,it could be long...")
    progress = 20
    async_set(asyncId,"progress",progress) 
    (user,port,passwd,sudopasswd) = get_default_login(session,user,port,passwd,sudopasswd)
    for host in hosts:
        taskId = idMap[host] 
        database.update_task(session,taskId,Task.STATUS_RUNNING,Task.RESULT_UNFINISH,"") 
    
    if config.fade_windows:
        ret=fade_connect_host(hosts,user,port,passwd,sudopasswd)
    else:
        import ansible_lib
        ret=ansible_lib.connect_host(hosts,user,port,passwd,sudopasswd)

    #处理结果
    success=[]
    failed=[]
    prepareTaskids=[]
    for hostName in ret:
        taskId = idMap[hostName]
        (result,msg,info) = ret[hostName]
        if result:
            #成功连接，添加到host表
            
            success.append(hostName)
            host = Host(hostName,Host.STATUS_CONNECTED)
            host.ip=info['ip']
            host.cpu=info['cpu']
            host.mem=info['mem']
            host.disk=info['disk']
            host.rack=info['rack']
            session.add(host)
            session.commit()
            #提交一个prepare任务,假如运行成功将修改状态到ready
            prepareTaskid = database.build_task(session,"ansible","prepare",hostName,"prepare","prepare")
            prepareTaskids.append(prepareTaskid)
            callback_lib.add_callback(session,prepareTaskid,"changeHostToReady")
            #假如登录信息跟默认的不一致，保存这些登录信息到数据库
            #TODO
            
            #更新任务状态
            database.update_task(session,taskId,Task.STATUS_FINISH,Task.RESULT_SUCCESS,"")
            progress += progressStep
            async_push(asyncId,"progressMsg","finish connect "+hostName)
            async_set(asyncId,"progress",progress)
        else:
            failed.append(hostName)
            database.update_task(session,taskId,Task.STATUS_FINISH,Task.RESULT_FAILED,msg)

    #全部完成
    async_push(asyncId,"progressMsg","success:"+",".join(success)+" failed:"+",".join(failed))
    async_set(asyncId,"progress","100")   
    #发送消息到worker
    retMsg = ""
    msg = ','.join([str(id) for id in prepareTaskids])
    if not mm.send(msg):
        retMsg = "send message to worker error"
    #10秒后清除内存任务
    time.sleep(10)
    async_remove(asyncId)
    session.close()

def get_default_login(session,user,port,passwd,sudopasswd):
    user = database.get_golbal_conf(session,"ansible_ssh_user")
    port = database.get_golbal_conf(session,"ansible_ssh_port")
    passwd = database.get_golbal_conf(session,"ansible_ssh_pass")
    sudopasswd = database.get_golbal_conf(session,"ansible_sudo_pass")
    return (user,port,passwd,sudopasswd)


############################################use for test
def fade_connect_host(hosts,user,port,passwd,sudopasswd):
    time.sleep(5)
    ret={}
    for host in hosts:
        ret[host]=(True,"fade finish",{"ip": "0.0.0.0","cpu":"core","mem":"4G","disk":"1T","rack":""})
    return ret

#fade的增删服务,10秒后修改任务未完成状态
def fade_add_del_service(addRunningId,delRunningId,msg=""):
    time.sleep(5)
    session=database.getSession()
    for id in addRunningId:
        database.update_task(session,id,Task.STATUS_FINISH,Task.RESULT_SUCCESS,msg)
    for id in delRunningId:
        database.update_task(session,id,Task.STATUS_FINISH,Task.RESULT_SUCCESS,msg)
    session.close()

