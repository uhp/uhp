#!python
#coding=utf8

import os
import sys

commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir)
import database
from model.alarm import AlarmList

engine = database.getEngine()
AlarmList.metadata.drop_all(engine) 
AlarmList.metadata.create_all(engine)
