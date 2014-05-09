#!python
# coding=utf8

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String , SmallInteger,BigInteger,Index
from models import UHPBase

Base = declarative_base()

class ApplicationRecord(Base, UHPBase):
    __tablename__ = 'app'
    __table_args__ = ( Index('idx_finishedTime' , 'finishedTime'), UHPBase.__table_args__ )
    appid = Column(String(35), primary_key=True)
    user = Column(String(10))
    name = Column(String(20))
    queue = Column(String(20))
    startedTime = Column(Integer)
    finishedTime = Column(Integer)
    state = Column(String(20))
    finalStatus = Column(String(20))
    attemptNumber = Column(SmallInteger)
     
    mapsTotal = Column(SmallInteger)
    mapsCompleted = Column(SmallInteger)
    successfulMapAttempts = Column(SmallInteger)
    killedMapAttempts = Column(SmallInteger)
    failedMapAttempts =  Column(SmallInteger)
    avgMapTime = Column(Integer)
    
    localMap = Column(SmallInteger)
    rackMap = Column(SmallInteger)
    
    reducesTotal = Column(SmallInteger)
    reducesCompleted = Column(SmallInteger)
    successfulReduceAttempts = Column(SmallInteger)
    killedReduceAttempts = Column(SmallInteger)
    failedReduceAttempts = Column(SmallInteger)
    avgReduceTime = Column(Integer)
     
    fileRead = Column(BigInteger)
    fileWrite = Column(BigInteger)
    hdfsRead = Column(BigInteger)
    hdfsWrite = Column(BigInteger)
    
    def __init__(self,appid):
        self.appid = appid
    
    def inc(self,key,value):
        temp = getattr(self,key)
        if not temp:
            temp = 0
        temp = temp + value
        setattr(self,key,value)
        
    def set(self,key,value):
        setattr(self,key,value)
        
    def __repr__(self):
        return "appid:"+self.appid
        
