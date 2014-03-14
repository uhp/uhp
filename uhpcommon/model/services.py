# -*- coding: UTF-8 -*-
from sqlalchemy import Column, Integer, String, Text, schema,SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship, backref
from models import UHPBase
import json,time

BASE = declarative_base()

class Service(BASE, UHPBase):
    """ services tables for uvpkeeper """

    __tablename__ = 'services'
    #服务名称
    service = Column(String(16),primary_key=True)
    #安装状态
    # 0 未安装 1 安装
    status = Column(Integer, nullable=False)
    
    STATUS_INIT = 0
    STATUS_ACTIVE = 1
    
    def __init__(self,service,status = STATUS_INIT):
        self.service = service
        self.status = status
        
        
