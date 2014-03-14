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


def getEngine(echo=True):
    if(string.find(config.connection, 'mysql://') >= 0):
        return create_engine(config.connection, isolation_level="READ COMMITTED",echo=echo)
    return create_engine(config.connection, echo=echo)

def getSession(echo=True):
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
    insert(GroupVar("all","","ansible_ssh_user","qiujw",0,"*用于登录到其它机器的用户名称"))
    insert(GroupVar("all","","ansible_ssh_port","9922",0,"*ssh的登录端口"))
    insert(GroupVar("all","","ansible_ssh_pass","just4test",0,"*ssh的登录密码"))
    insert(GroupVar("all","","ansible_sudo_pass","just4test",0,"*ssh登录后的sudo密码"))
    insert(GroupVar("all","","local_repo_enabled","false",0,"*是否使用本地仓库。如果，使用本地仓库，请填写local_http_url"))
    insert(GroupVar("all","","local_http_url","http://localhost:8080/uhp",0,"*是否使用本地仓库。如果，使用本地仓库，请填写local_http_url"))
    
    insert(GroupVar("all","","java_tar","jdk1.6.0_45.tar.gz",0,"*添加机器的时候.检查到没有java的话会安装的java的tar包。请填写绝对路径。"))
    insert(GroupVar("all","","java_untar_floder","jdk1.6.0_45",0,"*安装java的时候tar包解压的名称。推荐安装示例形式填写"))

    #初始化服务数据
    for service in static_config.services:
        insert(Service(service['name']))
    ansible_back_dir = os.path.join(config.uhphome,"conf","ansible_back")
    #插入ansible_back中的变量
    if not config.fade_windows:
        import inventory_tool
        inventory_tool.conf_to_db(ansible_back_dir)
