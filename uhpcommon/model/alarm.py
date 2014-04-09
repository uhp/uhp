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
    expression= Column(String(250), nullable=False)
    callback= Column(String(250), nullable=False)
    host = Column(String(30),nullable=False)

    HOST_ALL = "*"
    
class AlarmAssist(BASE, UHPBase):
    
    __tablename__ = 'alarm_assist'

    id= Column(Integer, primary_key=True)
    name= Column(String(30), nullable=False, unique=True)
    value= Column(Text, nullable=False)
