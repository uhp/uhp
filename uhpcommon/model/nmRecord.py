from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String , SmallInteger,BigInteger,Index
from models import UHPBase
Base = declarative_base()

class NmRecord(Base, UHPBase):
    __tablename__ = 'nm'
    __table_args__ = ( Index('idx_happenedtime_host' , 'happenTime' ,'host'), UHPBase.__table_args__ ) 
    
    host = Column(String(20), primary_key=True)
    recordTime = Column(Integer, primary_key=True)
    happenTime = Column(Integer, primary_key=True)
    
    containerNum = Column(SmallInteger)
    amNum = Column(SmallInteger)
    
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

    
    def __init__(self,host,recordTime,happenTime):
        self.host = host
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
    
