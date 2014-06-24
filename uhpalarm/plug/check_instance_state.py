#!/usr/bin/env python
#coding=utf8

import os.path, logging, sys
import json
import time

#for main run
#commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
#sys.path.append(commondir)

import util
import database
import config
from model.instance import Instance

def check_instance_state():
    is_checker = InstanceStateChecker()
    return is_checker.check_instance_state()

class InstanceStateChecker:
    def __init__(self):
        self.alarm_list = []

    def update_result(self, key_word, msg):
        self.alarm_list.append({"key_word":key_word,"msg":msg})

    def check_instance_state(self):
        '''
        获取所有的instance状态,报告哪些有问题
        '''
        service_role_map = {}
        #get all instance
        session = database.getSession()
        for instance in session.query(Instance):
            #检查实例
            result,msg = self.check_instance(instance)
            if not result:
                key_word = "%s(%s error)" % (instance.host,instance.role)
                self.update_result(key_word, msg)
            #采集服务
            if not service_role_map.has_key(instance.service) :
                service_role_map[instance.service] = []
            service_role_map[instance.service].append(instance)

        for (service,roles) in service_role_map.items():
            if service == "zookeeper" :
                zk_leader_port = database.get_service_conf(session,"zookeeper","zookeeper_leader_port")   
                result,msg = self.check_zk_leader(zk_leader_port,roles)
                if not result:
                    key_word = "cluster(zk no leader)"
                    self.update_result(key_word, msg)
            elif service == "hbase" :
                #TODO
                hbase_master_info_port = database.get_service_conf(session,"hbase","hbase_master_info_port")
                result,msg = self.check_hbase_master(hbase_master_info_port,roles)
                if not result:
                    key_word = "cluster(hbase no leader)"
                    self.update_result(key_word, msg)

        session.close()
        return self.alarm_list

    def check_instance(self, instance):
        if instance.status == Instance.STATUS_START :
            if instance.health == Instance.HEALTH_UNHEALTHY :  
                return (False, u"检测到实例 %s(%s) 在启动状态,但不健康,报告: %s。" % (instance.host, instance.role, instance.msg) )
            if instance.health == Instance.HEALTH_DOWN :  
                return (False, u"检测到实例 %s(%s) 在启动状态,但找不到对应的pid,报告: %s。" % (instance.host, instance.role, instance.msg) )
            if instance.monitor_time == None or instance.monitor_time == 0  :
                return (False, u"检测到实例 %s(%s) 在启动状态,但未找到检测信息。 " % (instance.host, instance.role) )
            else:
                dis = int(time.time()) - instance.monitor_time
                if dis > config.max_unknow_time :
                    return (False, u"检测到实例 %s(%s) 在启动状态,但检测超时%ds。" % (instance.host, instance.role, dis) )
        return (True,"")

    def check_zk_leader(self,port,roles):
        start = False
        masters = []
        for role in roles:
            if role.status == Instance.STATUS_START :
                start = True
            try:
                info = json.loads(role.msg)
            except:
                info = None
            
            if info != None and int(port) in info["exist_port"]:
                masters.append( role.host )

        if start :
            if len(roles) > 1 and len(masters) == 0 :
                return (Flase, u"检测到zookeeper在分布式状态启动,但是找不到领导结点。" )
            elif len(masters) > 1 :
                return (False, u"检测到有多个zookeeper的领导结点 %s。" % (",".join(masters)) )

        return (True,"")

    def check_hbase_master(self,port,roles):
        
        start = False
        masters = []
        debug_msg = ""
        for role in roles:
            if role.role != "hbasemaster" :
                continue
            if role.status == Instance.STATUS_START :
                start = True
            try:
                info = json.loads(role.msg)
            except:
                info = None
            debug_msg += json.dumps(info["exist_port"])

            if info != None and int(port) in info["exist_port"]:
                masters.append( role.host )

        if start :
            if len(masters) == 0 :
                return (False, u"检测到hbase没有主hbasemaster。%s " % debug_msg )
            elif len(masters) > 1:
                return (False, u"检测到有多个主hbasemaster %s。" % (",".join(masters)))
        return (True,"")
        
if __name__ == "__main__":
    print check_instance_state()

