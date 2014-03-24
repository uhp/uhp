#!python
#coding=utf8

import os
import sys

commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir)
import database
from model.callback import CallBack

engine = database.getEngine()
CallBack.metadata.drop_all(engine) 
CallBack.metadata.create_all(engine)