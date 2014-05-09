#!python
#coding=utf8

import string
import os  
import sys

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import and_
Base = declarative_base()

import config,static_config
from model.user import User
from model.task import Task
from model.instance import Instance
from model.host_group_var import Host,Group,GroupHost,HostVar,GroupVar
from model.services import Service
from model.callback import CallBack
from model.alarm import *
from model.monitor import *
from model.applicationRecord import ApplicationRecord
from model.nmRecord import NmRecord
from model.rmRecord import RmRecord
from model.metricsRecord import MetricsRecord

engine = None

def getEngine(echo=True):
    global engine
    if( engine != None ):
        return engine
    if(string.find(config.connection, 'mysql://') >= 0):
        engine = create_engine(config.connection, isolation_level="READ COMMITTED", echo=echo, pool_recycle=3600, pool_size=15 )
    else:
        engine = create_engine(config.connection, echo=echo)
    return engine

def getSession(echo=False):
    engine =  getEngine(echo)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def getConnect():
    engine =  getEngine()
    conn = engine.connect()
    return conn

def get_all_models():
    models = []
    models.append(User)
    models.append(Task)
    models.append(Instance)
    models.append(Service)
    
    models.append(Host)
    models.append(Group)
    models.append(GroupHost)
    models.append(GroupVar)
    models.append(HostVar)
    
    models.append(CallBack)
    
    models.append(Alarm)
    models.append(AlarmAssist)
    
    models.append(MonitorAssist)
    models.append(MonitorMetric)
    models.append(MonitorGroup)
    models.append(MonitorHost)

    models.append(ApplicationRecord)
    models.append(RmRecord)
    models.append(NmRecord)
    models.append(MetricsRecord)

    return models

def get_model_from_name(name):
    for model in get_all_models():
        if model.__tablename__ == name:
            return model

def create_db():
    engine = getEngine()
    for model in get_all_models():
        model.metadata.create_all(engine) 
    
def drop_db():
    engine = getEngine()
    for model in get_all_models():
        model.metadata.drop_all(engine) 
    
def createIndex():
    pass
    
def showAll():
    session=getSession()
    tasks = session.query(Task)
    for task in tasks:
        print task

def insert(object):
    session=getSession()
    session.merge(object)
    session.commit()
    
def get_golbal_conf(session,name):
    try:
        return str(session.query(GroupVar).filter(and_( GroupVar.group=="all" ,  
                   GroupVar.service=="",GroupVar.name==name)).one().value)
    except NoResultFound:
        return None
                   
def get_service_conf(session,service,name):
    try:
        return str(session.query(GroupVar).filter(and_( GroupVar.group=="all" ,  
                   GroupVar.service==service,GroupVar.name==name)).one().value)
    except NoResultFound:
        return None
    
#获取一批机器的配置
def get_conf_from_host(session,host_list,service,name):
    try:
        #默认
        default_value =get_service_conf(session,service,name)
        ret = {}
        for host in host_list:
            ret[host] = default_value
        
        #组变量
        gv_list = {}
        for gv in session.query(GroupVar).filter(
                            and_(GroupVar.service==service,GroupVar.name==name)):
            gv_list[gv.group] = str(gv.value)
        if len(gv_list) > 0:
            #组关系
            for (group,value) in gv_list.items():
                for gh in session.query(GroupHost).filter(GroupHost.group==group):
                    if ret.has_key(gh.hostname):
                        ret[gh.hostname] = value
        
        #机器变量
        for var in session.query(HostVar).filter(and_(HostVar.service==service,HostVar.name==name)):
            ret[var.host] = str(var.value) 
            
        return ret;
    except NoResultFound:
        return None 

#一些有用的数据库操作封装
#增加活动记录
def build_task(session,taskType,service,host,role,task):
    newTask = Task(taskType,service,host,role,task)
    session.add(newTask)
    session.flush()
    newId = newTask.id
    session.commit()
    return newId
    
def update_task(session,taskId,status,result,msg):
    session.query(Task).filter(Task.id==taskId) \
        .update({Task.status:status,Task.result:result,Task.msg:msg})
    session.commit()
    
def update_instance(session,host,role,status):
    session.query(Instance).filter(and_(Instance.host==host,Instance.role==role)) \
        .update({Instance.status:status})
    session.commit()

def del_instance(session,host,role): 
    session.query(Instance).filter(and_(Instance.host==host,Instance.role==role)) \
        .delete()
    session.commit()

if __name__ == "__main__":
    
    drop_db()
    create_db()
    #默认的admin
    insert(User("admin","admin","admin@ucweb.com",0));
    #默认分组
    insert(Group("all","no chinise"))
    #关键分组变量
    insert(GroupVar("all","","ansible_ssh_user","qiujw",0,u"*用于登录到其它机器的用户名称"))
    insert(GroupVar("all","","ansible_ssh_port","9922",0,u"*ssh的登录端口"))
    insert(GroupVar("all","","ansible_ssh_pass","just4test",0,u"*ssh的登录密码"))
    insert(GroupVar("all","","ansible_sudo_pass","just4test",0,u"*ssh登录后的sudo密码"))
    insert(GroupVar("all","","local_repo_enabled","true",0,u"*是否使用本地仓库。如果，使用本地仓库，请填写local_http_url"))
    insert(GroupVar("all","","local_http_url","http://localhost:8080/uhp",0,u"*本地仓库的HTTP服务local_http_url"))
    
    insert(GroupVar("all","","java_tar","jdk1.6.0_45.tar.gz",0,u"*添加机器的时候.检查到没有java的话会安装的java的tar包。请填写绝对路径。"))
    insert(GroupVar("all","","java_untar_floder","jdk1.6.0_45",0,u"*安装java的时候tar包解压的名称。推荐安装示例形式填写"))

    insert(GroupVar("all","","services_log_root","/var/log",0,u"*各个服务的日志存放地方，需要预留10G空间"))

    #初始化服务数据
    for service in static_config.services:
        insert(Service(service['name']))
    ansible_back_dir = os.path.join(config.uhphome,"conf","ansible_back")
    #插入ansible_back中的变量
    if not config.fade_windows:
        import inventory_tool
        inventory_tool.conf_to_db(ansible_back_dir)
