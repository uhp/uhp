#!/usr/bin/env python
#coding=utf8

import os.path, logging, sys

#for main run
#commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
#sys.path.append(commondir)

import util
import database
from model.instance import Instance

def check_instance_state():
    is_checker = InstanceStateChecker()
    return is_checker.check_instance_state()

class InstanceStateChecker:
    def __init__(self):
        self.state = "OK"
        self.msg = u""
        self.msg_count = 1

    def update_msg(self,msg):
        self.msg += "%d: %s" % (self.msg_count, msg)
        self.msg_count = self.msg_count + 1

    def update_result(self, state, msg):
        if state == "ERROR" :
            self.state = state
            self.update_msg(msg)
        elif state == "WARN" :
            self.update_msg(msg)
            if self.state != "ERROR" :
                self.state = state

    def check_instance_state(self):
        '''
        获取所有的instance状态,报告哪些有问题
        '''
        service_role_map = {}
        #get all instance
        session = database.getSession()
        for instance in session.query(Instance):
            result,msg = self.check_instance(instance)
            self.update_result(result,msg)
            if not service_role_map.has_key(instance.service) :
                service_role_map[instance.service] = []
            service_role_map[instance.service].append(instance)

        for (service,roles) in service_role_map.items():
            if service == "zookeeper" :
                zk_leader_port = database.get_service_conf(session,"zookeeper","zookeeper_leader_port")   
                result,msg = self.check_zk_leader(zk_leader_port,roles)
                self.update_result(result,msg)
            elif service == "hbase" :
                #TODO
                hbase_master_info_port = database.get_service_conf(session,"hbase","hbase_master_info_port")
                result,msg = self.check_hbase_master(hbase_master_info_port,roles)
                self.update_result(result,msg)
                

        session.close()
        return (self.state,self.msg)

    def check_instance(self, instance):
        if instance.status == Instance.STATUS_START and instance.health == Instance.HEALTH_UNHEALTHY :  
            return ("ERROR", u"检测到实例 %s(%s) 在启动状态,但不健康,报告: %s。" % (instance.host, instance.role, instance.msg) )
        return ("OK","")

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
            
            if info != None and port in info["exist_port"]:
                masters.append( role.host )

        if start :
            if len(roles) > 1 and len(masters) == 0 :
                return ("ERROR", u"检测到zookeeper在分布式状态启动,但是找不到领导结点。")
            elif len(masters) > 1 :
                return ("ERROR", u"检测到有多个zookeeper的领导结点 %s。" % (",".join(masters)) )

        return ("OK","")

    def check_hbase_master(self,port,roles):
        
        start = False
        masters = []
        for role in roles:
            if role.status == Instance.STATUS_START :
                start = True
            try:
                info = json.loads(role.msg)
            except:
                info = None
            
            if info != None and port in info["exist_port"]:
                masters.append( role.host )
        if start :
            if len(masters) == 0 :
                return ("ERROR", u"检测到hbase没有主hbasemaster。")
            elif len(masters) > 1:
                return ("ERROR", u"检测到有多个主hbasemaster %s。" % (",".join(masters)))
        return ("OK","")
        
if __name__ == "__main__":
    print check_instance_state()

