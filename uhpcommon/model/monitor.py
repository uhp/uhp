# -*- coding: UTF-8 -*-
from sqlalchemy import Column, Integer, Float, String, Text, schema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean, func, Index, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from models import UHPBase

BASE = declarative_base()

__all__ =  ['MonitorAssist', 'MonitorMetric', 'MonitorGroup', 'MonitorHost']

class MonitorAssist(BASE, UHPBase):
    """
            公共配置信息，例如ganglia的共用配置项
    """
    __tablename__ = 'monitor_assist'

    id= Column(Integer, primary_key=True)
    name= Column(String(30), nullable=False, unique=True)
    value= Column(String(65535), nullable=False)

    
class MonitorMetric(BASE, UHPBase):
    """
            监控项
    """
    __tablename__ = 'monitor_metric'

    id= Column(Integer, primary_key=True)
    gid= Column(Integer, nullable=False)
    name= Column(String(30), nullable=False, unique=True)
    value_threshold=Column(Float, nullable=False)
    title= Column(String(30), nullable=False)
    chart_type= Column(String(30), nullable=False)

class MonitorGroup(BASE, UHPBase):
    """
            监控项组
    """
    __tablename__ = 'monitor_group'

    id= Column(Integer, primary_key=True)
    name= Column(String(30), nullable=False, unique=True)
    params= Column(String(256), nullable=False)
    collect_once=Column(Boolean, nullable=False)
    collect_every=Column(Integer, nullable=False)
    time_threshold= Column(Integer, nullable=False)
    
class MonitorHost(BASE, UHPBase):
    """
            监控部署表
    """
    __tablename__ = 'monitor_host'
    #__table_args__ = ( Index('uniqe_idx_%s' % __tablename__, 'service', 'host','role'), )
    __table_args__ =  (UniqueConstraint('host', 'gid', name='_host_gid_ui'), UHPBase.__table_args__)
    
    id= Column(Integer, primary_key=True)
    host= Column(String(30), nullable=False)
    gid= Column(Integer, nullable=False)
    
