# -*- coding: UTF-8 -*-
import re
from sqlalchemy import Column, Integer, String, Text, schema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, func, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from models import UHPBase

BASE = declarative_base()

__all__ =  ['Alarm','AlarmAutofix', 'AlarmAssist', 'AlarmList']

class Alarm(BASE, UHPBase):
    
    __tablename__ = 'alarm'
    __table_args__ =  (UniqueConstraint('name', 'host', name='_name_host_ui'), UHPBase.__table_args__)
    
    id= Column(Integer, primary_key=True)
    name= Column(String(30), nullable=False)
    #判断函数,可设定传入的参数。传入的参数是 ganglia收集的指标名称
    #例如  max( load_one , 10 ) 则用这两个作为参数进行调用 
    #返回一个二元组  二元组第一项是报警等级 OK WARN ERROR 第二项是报警信息
    expression= Column(String(250), nullable=False)
    #回调函数  sendmail 调用参数是 expression的返回的二元组
    callback= Column(String(250), nullable=False)
    #拓展host字段的规则如下:
    #want1,want2...:except1,except2...
    #为all 或者为 机器名 或者为 cluster
    host = Column(String(256,collation='latin1_swedish_ci'),nullable=False)

    HOST_ALL = "all"
    
    def __init__(self, name, expression, callback, host=HOST_ALL ):
        self.name = name
        self.expression = expression
        self.callback = callback
        self.host = host
    
    def get_host_tuple(self):
        '''
        解析want1,want2...:except1,except2...的格式
        返回最终要检查的主机列表和例外的主机列表
        [all,cluster,hadoop1],[hadoop2]
        '''
        if self.host != None and len(self.host) > 0 :
            host_lists = self.host.split(":")
            if len(host_lists) == 2 :
                return (host_lists[0].split(","),host_lists[1].split(","))
            else :
                return (host_lists[0].split(","),[])

        return ([],[])

class AlarmAutofix(BASE, UHPBase):

    __tablename__ = 'alarm_autofix'

    id = Column(Integer, primary_key=True)
    pattern = Column(String(32), nullable=False, unique=True)
    count = Column(Integer, nullable=False)
    service = Column(String(32), nullable=False)
    role = Column(String(32), nullable=False)
    task = Column(String(32), nullable=False)
    
    def __init__(self, pattern, count, service, role, task):
        self.pattern = pattern
        self.count = count
        self.service = service
        self.role = role
        self.task = task

    def format(self):
        result = {}
        result['pattern'] = re.compile(self.pattern)
        result['count'] = self.count
        result['service'] = self.service
        result['role'] = self.role
        result['task'] = self.task
        return result
    
class AlarmAssist(BASE, UHPBase):
    
    __tablename__ = 'alarm_assist'

    id= Column(Integer, primary_key=True)
    name= Column(String(30), nullable=False, unique=True)
    value= Column(Text, nullable=False)

    def __init__(self, name, value ):
        self.name = name
        self.value = value
        
class AlarmList(BASE, UHPBase):
    """报警信息列表，用于页面浏览"""

    __tablename__ = 'alarm_list'

    id    = Column(Integer, primary_key  = True)
    level = Column(String(10), nullable  = False)
    title = Column(String(255), nullable = False)
    host  = Column(String(32), nullable = False)
    msg   = Column(Text, nullable        = False)
    ctime = Column(Integer)
    
    LEVEL_WARN     = "WARN"
    LEVEL_ERROR    = "ERROR"

    def __init__(self, title, host, msg, level, ctime):
        self.title = title
        self.host  = host
        self.msg   = msg
        self.level = level
        self.ctime = ctime
