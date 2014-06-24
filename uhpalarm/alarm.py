#!/usr/bin/env python
# coding=utf-8

import os.path, logging, sys
import time

import daemon
import lockfile
import lockfile.pidlockfile

commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir)

import config
import database
import mail_center
from model.instance import Instance
from lib.logger import log
from alarm_rule import AlarmRuleManager
from alarm_data import AlarmDataManager
from alarm_expression import AlarmExpManager
from alarm_callback import AlarmCallbackManager



class Alarm:
    '''
        定期进行告警检查
    '''
   
    def __init__(self):
        self.manager_list = []
        
        self.rule_manager = AlarmRuleManager()
        self.manager_list.append(self.rule_manager)
        
        self.data_manager = AlarmDataManager()
        self.manager_list.append(self.data_manager)
        
        self.exp_manager = AlarmExpManager()
        self.manager_list.append(self.exp_manager)
        
        self.cb_manager = AlarmCallbackManager()
        self.manager_list.append(self.cb_manager)
        
        self.stop = False
        
    def run(self):
        while not self.stop:
            begin = time.time()
            log.info("BEGIN TO CHECK")
            self.pre_check_manager_list()
            self.judge_host_rule()
               
            self.post_check_manager_list()
            end = time.time()
            log.info("END CHECK using %.3fs" % (end-begin) )
            
            self.interval()
            

    def judge_specify_rule(self, host, rule, data_set ):
        try:
            #exp_result = self.exp_manager.judge(host, rule, data_set)
            return self.exp_manager.judge(host, rule, data_set)
            #self.cb_manager.callback(host, rule, exp_result)
        except:
            log.exception("get exception with h:%s r:%s" % (host,rule) )
        return []

    def judge_host_rule(self):
        '''
        为每个host的规则进行判断
        '''
        try:
            alarm_list = []
            host_list = self.get_host_list()
            #添加集群规则
            host_list.append("cluster")
            for host in host_list:
                rule_list = self.rule_manager.get_rule_by_host(host)
                data_set = self.data_manager.get_data_by_host(host)
                for rule in rule_list:
                    temp = self.judge_specify_rule(host, rule, data_set)
                    alarm_list.extend(temp)
            self.cb_manager.deal_alarm_list(alarm_list)
        except:
            log.exception("get exeception judge_host_rule")

    def get_host_list(self):
        #TODO
        host_list = []
        session = database.getSession()
        for instance in session.query(Instance).filter(Instance.role == "gmond"):
            host_list.append(instance.host)
        session.close()
        return host_list
            
    def pre_check_manager_list(self):
        for manager in self.manager_list:
            manager.pre_check()
        
    def post_check_manager_list(self):
        for manager in self.manager_list:
            manager.post_check()
            
    def interval(self):
        time.sleep(config.alarm_interval)
        
os.chdir(config.uhphome)
APP = "alarm"

if __name__ == "__main__":
    log.info("start...")
    try:
        pidfile = "pids/%s/%s.pid" % (APP, APP)
        pidfile = lockfile.pidlockfile.PIDLockFile(pidfile)
        files_preserve=[logging.root.handlers[1].stream.fileno()]
        dmn = daemon.DaemonContext(None, os.getcwd(), pidfile=pidfile, files_preserve=files_preserve)
        dmn.open()
        #start mail loop
        mail_center.start_mail_center()
        #start alarm loop
        alarm = Alarm()
        alarm.run()
    except Exception as e:
        log.exception(e)
    log.info("end!")
    
