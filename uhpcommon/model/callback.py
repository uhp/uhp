#!python
# -*- coding: UTF-8 -*-

from sqlalchemy import Column, Integer, String, Text, schema,SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship, backref
from models import UHPBase
import json,time

BASE = declarative_base()

class CallBack(BASE, UHPBase):

    __tablename__ = 'callback'
    #mysql自增id
    id= Column(Integer, primary_key=True)
    #需要检查回调的taskid
    taskid = Column(Integer, primary_key=True)
    #回调的function名称
    func = Column(String(64),nullable=False)
    #参数
    params = Column(String(256), nullable=False)
    
    def __init__(self, taskid, func, params):
        self.taskid = taskid
        self.func = func
        self.params = params
        

        
 
        
        