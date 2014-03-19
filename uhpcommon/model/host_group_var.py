# -*- coding: UTF-8 -*-
from sqlalchemy import Column, Integer, String, Text, schema,SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship, backref
from models import UHPBase

BASE = declarative_base()


class Host(BASE, UHPBase):

    __tablename__ = 'host'

    hostname = Column(String(32), primary_key=True)
    status = Column(String(16),nullable=False)
    ip = Column(String(36), nullable=False)
    cpu = Column(String(16))
    mem = Column(String(16))
    disk = Column(String(16))
    rack = Column(String(16))

    STATUS_CONNECTED = "connected"
    STATUS_READY = "ready"
    
    def __init__(self, hostname,status=STATUS_CONNECTED):
        self.hostname = hostname
        self.status = status
        self.ip = "0.0.0.0"
        self.cpu = "unknow"
        self.mem = "unknow"
        self.disk = "unknow"
        self.rack = "default"
    
    def format(self):
        ret={}
        ret["status"]=self.status
        ret["ip"]=self.ip;
        ret["cpu"]=self.cpu;
        ret["mem"]=self.mem;
        ret["disk"]=self.disk;
        ret["rack"]=self.rack;
        return ret;

class Group(BASE, UHPBase):
    
    __tablename__ = 'group'    
    group = Column(String(32), primary_key=True)
    text = Column(String(128))
    def __init__(self, group , text="" ):
        self.group = group
        self.text = text
    
class GroupHost(BASE, UHPBase):
    
    __tablename__ = 'grouphost'
    group = Column(String(32), primary_key=True)
    hostname = Column(String(32), primary_key=True)
    def __init__(self, group, hostname ):
        self.group = group
        self.hostname = hostname
        
class GroupVar(BASE, UHPBase):
    
    __tablename__ = 'groupvar'
    group = Column(String(32), primary_key=True)
    #如果服务是空 就是属于第一层的配置
    service = Column(String(32), primary_key=True)
    name = Column(String(64), primary_key=True)
    value = Column(String(1024))
    #0-string 1-list
    type = Column(SmallInteger,nullable=False)
    text = Column(Text)
    
    def __init__(self, group,service, name,value,type=0 ,text=""):
        self.group = group
        self.service = service
        self.name = name
        self.value = value
        if isinstance(type, basestring) :
            if type=="string":
                self.type = 0 ;
            else:
                self.type = 1;
        else:
            self.type = type
        self.text = text
        
    def format(self):
        ret={}
        ret["group"] = self.group
        ret["name"] = self.name
        ret["value"] = self.value
        if self.type==0 :
            ret["type"] = "string"
        else:
            ret["type"] = "list"
        ret['text'] = self.text
        return ret

class HostVar(BASE, UHPBase):
    
    __tablename__ = 'hostvar'
    host = Column(String(32), primary_key=True)
    #如果服务是空 就是属于第一层的配置
    service = Column(String(32), primary_key=True)
    name = Column(String(64), primary_key=True)
    value = Column(String(1024))
    #0-string 1-list
    type = Column(SmallInteger,nullable=False)
    text = Column(Text)
    
    def __init__(self, host,service, name,value,type=0,text="" ):
        self.host = host
        self.service = service
        self.name = name
        self.value = value
        if isinstance(type, basestring) :
            if type=="string":
                self.type = 0 ;
            else:
                self.type = 1;
        else:
            self.type = type
        self.text = ""
    
    def format(self):
        ret={}
        ret["group"] = self.host
        ret["name"] = self.name
        ret["value"] = self.value
        if self.type==0 :
            ret["type"] = "string"
        else:
            ret["type"] = "list"
        ret['text'] = self.text
        return ret  
