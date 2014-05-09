from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String , SmallInteger,BigInteger,Index
from models import UHPBase

Base = declarative_base()
class RmRecord(Base):
    __tablename__ = 'rm'
    __table_args__ = ( Index('idx_happenTime', 'happenTime'), UHPBase.__table_args__ ) 
    recordTime = Column(Integer, primary_key=True)
    happenTime = Column(Integer, primary_key=True)
    
    appNum = Column(SmallInteger)
    finishedApp = Column(SmallInteger)
    failedApp = Column(SmallInteger)
    killedApp = Column(SmallInteger)
    notSuccApp = Column(SmallInteger)
    
    mapNum = Column(SmallInteger)
    mapTime = Column(Integer)
    failMap = Column(Integer)
    
    reduceNum = Column(SmallInteger)
    reduceTime = Column(Integer)
    failReduce = Column(Integer)
    
    fileRead = Column(BigInteger)
    fileWrite = Column(BigInteger)
    hdfsRead = Column(BigInteger)
    hdfsWrite = Column(BigInteger)
    
    def __init__(self,recordTime,happenTime):
        self.recordTime = recordTime
        self.happenTime = happenTime
    
    def inc(self,key,value):
        temp = getattr(self,key)
        if not temp:
            temp = 0
        temp = temp + value
        setattr(self,key,temp)
        
    def set(self,key,value):
        setattr(self,key,value)
    
