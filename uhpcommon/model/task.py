# -*- coding: UTF-8 -*-
from sqlalchemy import Column, Integer, String, Text, schema,SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship, backref
from models import UHPBase
import json,time

BASE = declarative_base()

class Task(BASE, UHPBase):
    """ users tables for uvpkeeper """

    __tablename__ = 'tasks'
    #mysql自增id
    id= Column(Integer, primary_key=True)
    #提交的时间戳
    sumbitTime = Column(Integer, nullable=False)
    #任务类型   [ ansible shell ]
    taskType = Column(String(16), nullable=False)
    #服务 hdfs yarn 
    service = Column(String(64), nullable=False)
    #机器 hostname
    host = Column(String(32))
    #角色 DATANODE NAMENODE 
    role = Column(String(16))
    #任务名称 start stop restart ...
    task = Column(String(30), nullable=False)
    #任务需要的参数 json格式
    params = Column(String(256))
    #任务状态  [ init pending running finish ]
    status = Column(String(16), nullable=False)
    #任务结果  [ unfinish success failed timeout ]
    result = Column(String(16), nullable=False)
    #附加信息 填写运行失败的时候的错误提示
    #当针对service的安装服务的时候，使用如下的返回格式
    #[
    #    {"service":xxx,"host":xx,"role":xx,"result":xx,"msg":"xxx"},
    #    {"service":xxx,"host":xx,"role":xx,"result":xx,"msg":"xxx"}
    #]
    msg = Column(Text)
    
    STATUS_INIT="init"
    STATUS_PENDING="pending"
    STATUS_RUNNING="running"
    STATUS_FINISH="finish"
    STATUS_PROCESS={STATUS_INIT:10,STATUS_PENDING:20,STATUS_RUNNING:30,STATUS_FINISH:100}
    
    RESULT_UNFINISH="unfinish"
    RESULT_SUCCESS="success"
    RESULT_FAILED="failed"
    RESULT_TIMEOUE="timeout"
    RESULT_KILLED="killed"
    
#     taskType_map=["未知","ansible","shell","async"]
#     status_map=["初始 ","待运行 ","运行中 ","运行结束"]
#     result_map=["未完成","成功","失败","超时"]
    
    
    def __init__(self,taskType, service, host, role, task, params = "{}"):
        self.sumbitTime = int(time.time())
        self.taskType = taskType
        self.service = service
        self.host = host
        self.role = role
        self.task = task
        self.params = params
        self.status = Task.STATUS_INIT
        self.result = Task.RESULT_UNFINISH
        
    def format(self):
        ret={}
        ret["id"]=self.id
        ts = time.localtime(self.sumbitTime)
        ret["sumbitTime"]=time.strftime("%Y-%m-%d %H:%M:%S",ts)
        ret['taskType']=self.taskType
        ret['service']=self.service
        ret['host']=self.host
        ret['role']=self.role
        ret['task']=self.task
        ret['status']=self.status
        ret['result']=self.result
        return ret;
    
    def getProcess(self):
        if Task.STATUS_PROCESS.has_key(self.status):
            return Task.STATUS_PROCESS[self.status]
        else:
            return 0
        
        
