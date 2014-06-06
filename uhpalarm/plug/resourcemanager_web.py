#!/usr/bin/env python
#coding=utf8

import os.path, logging, sys
import time
import re
import StringIO
import string
from lxml import etree

#for main run
#commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
#sys.path.append(commondir)

import util

def resourcemanager_web(host,port):
    '''
    检查以下事项:
    1. 不健康的node 及其对应的report
    '''
    state = "OK"
    msg = u""

    #state list:DECOMMISSIONED,LOST,NEW,REBOOTED,RUNNING,UNHEALTHY,
    url = "http://%s:%s/ws/v1/cluster/nodes?state=unhealthy" % (host,port)
    nodes = util.get_http_json(url,5)
    if nodes != None :
        if nodes["nodes"] != None :
            for node in nodes["nodes"]["node"] :
                state = "ERROR"
                msg += u"检测到不健康机器 %s 健康报告 %s." % (node["nodeHostName"],node["healthReport"])
    else:
        return ("ERROR",u"不能连接到RM %s:%s" % (host,port) )

    url = "http://%s:%s/ws/v1/cluster/nodes?state=lost" % (host,port)
    nodes = util.get_http_json(url,5)
    if nodes != None :
        if nodes["nodes"] != None :
            for node in nodes["nodes"]["node"] :
                state = "ERROR"
                ts = time.localtime(node['lastHealthUpdate']/1000)
                date_time = time.strftime("%Y-%m-%d %H:%M:%S",ts)
                msg += u"检测到丢失的机器 %s 丢失时间 %s." % (node["nodeHostName"],date_time)
    else:
        return ("ERROR",u"不能连接到RM %s:%s" % (host,port) )
    
    return (state,msg)

if __name__ == "__main__":
    #print get_http("http://mob616:50088/ws/v1/cluster/apps?state=RUNNING")
    print resourcemanager_web("hadoop2","50088")
