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
        '''
        data_set={host1:{},host2:{}...}
        '''
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
        '''
        根据ganglia的目录获取数据
        先获取cluster_name,拼出集群目录
        再获取数据库中的hostname的列表
        逐一获取对应目录的数据
        '''
        host_list = contants.get_host_list()

        dict = {}
        for host in host_list:
            host_dir = os.path.join(dir,self.cluster_name,host)
            if os.path.exists(host_dir) :
                host_dict = {}
                for point in os.listdir(host_dir):
                    point_path = os.path.join(host_dir,point)
                    point_name = point[0:len(point)-4]
                    (pre,value) = self.rrd_wrapper.get_pre_last( str(point_path) )
                    host_dict[point_name] = value
                    host_dict["PRE_"+point_name] = pre 
                dict[host] = host_dict
        return dict
        #re = {}
        #for child in os.listdir(dir):
        #    child_path = os.path.join(dir,child)
        #    if os.path.isfile(child_path) :
        #        point_name = child[0:len(child)-4]
        #        #(ts,value) = self.rrd_wrapper.get_last( child_path )
        #        (pre,value) = self.rrd_wrapper.get_pre_last( child_path )
        #        re[point_name] = value
        #        re["PRE_"+point_name] = pre
        #    elif os.path.isdir(child_path) :
        #        re[child] = self.get_last_rrd( child_path )
        #return re

    def get_data_by_host(self, host):
        '''
        根据指定的host获取对应的指标数据
        返回结果类似
        {'load_one':0.9,'load_five':0.6}
        '''
        if host == "cluster" :
            return self.data_set

        if self.data_set.has_key(host) :
            return self.data_set[host]

        return {}
        
if __name__ == '__main__':
    
    dm = AlarmDataManager()
    #print dm.data_set
    dm.pre_check()
    print dm.get_data_by_host("hadoop2")
