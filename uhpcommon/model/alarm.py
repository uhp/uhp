# -*- coding: UTF-8 -*-
from sqlalchemy import Column, Integer, String, Text, schema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship, backref
from models import UHPBase

BASE = declarative_base()

__all__ =  ['Alarm', 'AlarmAssist']

class Alarm(BASE, UHPBase):
    
    __tablename__ = 'alarm'

    id= Column(Integer, primary_key=True)
    name= Column(String(30), nullable=False, unique=True)
    #判断函数,可设定传入的参数。传入的参数是 ganglia收集的指标名称
    #例如  max( load_one , 10 ) 则用这两个作为参数进行调用 
    #返回一个二元组  二元组第一项是报警等级 OK WARN ERROR 第二项是报警信息
    expression= Column(String(250), nullable=False)
    #回调函数  sendmail 调用参数是 expression的返回的二元组
    callback= Column(String(250), nullable=False)
    #为* 或者为 机器名
    host = Column(String(30),nullable=False)

    HOST_ALL = "*"
    
    def __init__(self, name, expression, callback, host=HOST_ALL ):
        self.name = name
        self.expression = expression
        self.callback = callback
        self.host = host
    
class AlarmAssist(BASE, UHPBase):
    
    __tablename__ = 'alarm_assist'

    id= Column(Integer, primary_key=True)
    name= Column(String(30), nullable=False, unique=True)
    value= Column(Text, nullable=False)

    def __init__(self, name, value ):
        self.name = name
        self.value = value
        