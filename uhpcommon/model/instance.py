# -*- coding: UTF-8 -*-
from sqlalchemy import Column, Integer, String, Text, schema,SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, func,Index, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from models import UHPBase
import time

BASE = declarative_base()


# instance 的状态转移说明
# 安装服务后插入记录  status为setup,提交安装的task并获取对应的runningid
# 异步检测runningid成功执行后 status转为stop,不成功则删除记录
# 
# 收到启动任务start则转status为starting,并获取对应的runningid
# 异步检测runningid成功执行后 转starting为start,不成功转stop
#
# 收到删除任务stop转为removeing,并获取对应的runningid
# 异步检测runningid成功执行后 删除记录,失败则不转移状态
#

class Instance(BASE, UHPBase):
    """ users tables for uhpkeeper """

    __tablename__ = 'instance'
    __table_args__ = ( UniqueConstraint('service', 'host','role', name='_name_host_role') , UHPBase.__table_args__ )
    id= Column(Integer, primary_key=True)
    service = Column(String(16))
    host = Column(String(32))
    role = Column(String(16))
    #网络机架
    rack = Column(String(32), nullable=False)
    # [ setup -> stop -> starting -> start -> stoPping -> stop -> removing]
    status = Column(String(16), nullable=False)
    # [unknow healthy unhealthy down]
    health = Column(String(16), nullable=False)
    # 信息字段
    msg = Column(Text)
    # 启动状态时间
    uptime = Column(Integer)
    # 检测时间
    monitor_time = Column(Integer)
    
    STATUS_SETUP     = "setup"
    STATUS_STOPPING  = "stopping"
    STATUS_STOP      = "stop"
    STATUS_STARTING  = "starting"
    STATUS_START     = "start"
    STATUS_REMOVING  = "removing"

    HEALTH_UNKNOW    = "unknow"
    HEALTH_HEALTHY   = "healthy"
    HEALTH_UNHEALTHY = "unhealthy"
    HEALTH_DOWN      = "down"


    def __init__(self, service, host, role,status=STATUS_SETUP ):
        self.service = service
        self.host = host
        self.role = role
        self.rack = "default"
        self.status = status
        self.health = "unknow"
        self.more = "{}"
        self.uptime = 0
        self.monitor_time = 0
    
    #转化字段为最终可以显示的字段
    def format(self):
        ret={};
        ret["service"] = self.service;
        ret["name"] = self.get_instance_name(self.host,self.role)
        ret["host"] = self.host;
        ret["role"] = self.role;
        ret["rack"] = self.rack;
        ret["status"] = self.status;
        ret["health"] = self.health;
        if self.uptime == 0 :
            ret["uptime"] = "----"
        else:
            timeArray = time.localtime(self.uptime)
            ret["uptime"] = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        if self.monitor_time == None or self.monitor_time == 0  :
            ret["monitor_time"] = "----"
        else:
            ret["monitor_time"] = int(time.time()) - self.monitor_time
            if ret["monitor_time"] < 0 :
                ret["monitor_time"] = 0
            elif ret["monitor_time"] >3600 :
                ret["monitor_time"] = ">3600"
        ret["msg"] = self.msg 
        return ret;
            
    @staticmethod
    def get_instance_name(host, role):
        '''将host和role组合为instance name'''
        return "%s(%s)" % (host, role)

    @staticmethod
    def split_instance_name(instance_name):
        '''将instance_name拆分为host 和role'''                                 
        index = instance_name.find("(") 
        le = len(instance_name) 
        if index != -1 and instance_name[le-1] == ')' and index+1 != le-1 and index != 0: 
           return (instance_name[0:index],instance_name[index+1:le-1]) 
        return (None,None) 
            
    @staticmethod    
    def get_instance_name(host, role):
        '''将host和role组合为instance name'''
        return "%s(%s)" % (host, role)   

    @staticmethod
    def split_instance_name(instance_name):
        '''将instance_name拆分为host 和role'''
        index = instance_name.find("(")
        le = len(instance_name)
        if index != -1 and instance_name[le-1] == ')' and index+1 != le-1 and index != 0:
           return (instance_name[0:index],instance_name[index+1:le-1])
        return (None,None)


