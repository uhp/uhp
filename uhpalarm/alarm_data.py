#!/usr/bin/env python
# coding=utf-8

import os,sys
commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir)


import config
import database
import time
from rrd import RrdWrapper
from lib.manager import Manager
from lib import contants
from lib.logger import log

class AlarmDataManager(Manager):
    def __init__(self):
        self.data_set = None
        self.rrd_wrapper = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)
        self.cluster_name = contants.get_cluster_name()
 
    def pre_check(self):
        '''
        每次检查开始前获取数据
        '''
        begin = time.time()
        if os.path.exists( config.ganglia_rrd_dir ):
            self.data_set = self.get_last_rrd( config.ganglia_rrd_dir )
        end = time.time()
        log.info("refresh data using %.3f s" % (end - begin) )
    
    def get_last_rrd(self, dir):
        re = {}
        for child in os.listdir(dir):
            child_path = os.path.join(dir,child)
            if os.path.isfile(child_path) :
                point_name = child[0:len(child)-4]
                (ts,value) = self.rrd_wrapper.get_last( child_path )
                re[point_name] = value
            elif os.path.isdir(child_path) :
                re[child] = self.get_last_rrd( child_path )
        return re

    def get_data_by_host(self, host):
        '''
        根据指定的host获取对应的指标数据
        返回结果类似
        {'load_one':0.9,'load_five':0.6}
        '''
        if host == "cluster" :
            if  self.data_set.has_key(self.cluster_name) :
                return  self.data_set[self.cluster_name]
            else:
                return {}
        for (cluster_name,data) in self.data_set.items():
            
            if cluster_name == "__SummaryInfo__" :
                continue
            else:
                if data.has_key(host) :
                    return data[host].copy()
        return {}

        
if __name__ == '__main__':
    
    dm = AlarmDataManager()
    #print dm.data_set
    print dm.get_data_by_host("hadoop2")
