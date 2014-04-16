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
from alarm_rule import AlarmRuleManager
from alarm_data import AlarmDataManager
from alarm_expression import AlarmExpManager
from alarm_callback import AlarmCallbackManager


class Manager:
    def init(self):
        pass
    
    def close(self):
        pass

class Alarm:
    '''
        定期进行告警检查
    '''
    
    ALARM_OK = "ok"
    ALARM_WARN = "warn"
    ALARM_ERROR = "error"
    
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
            
            self.init_manager_list()
            try:
                host_list = self.get_host_list()
                for host in host_list:
                    rule_list = self.rule_manager.get_rule_by_host(host)
                    data_set = self.data_manager.get_data_by_host(host)
                    for rule in rule_list:
                        exp_result = self.exp_manager.judge(data_set,rule)
                        self.cb_manager.callback(exp_result)
            except:
                log.exception("get exeception in alarm run")
                
            self.close_manager_list()
            
            self.interval()
            
            
    def get_host_list(self):
        #TODO
        return ['hadoop1']
            
    def init_manager_list(self):
        for manager in self.manager_list:
            manager.init()
        
    def close_manager_list(self):
        for manager in self.manager_list:
            manager.close()
            
    def interval(self):
        time.sleep(config.alarm_interval)
        
os.chdir(config.uhphome)
APP = os.path.splitext(os.path.basename(sys.argv[0]))[0]
logging.config.fileConfig("%s/uhp%s/conf/logging.conf" % (config.uhphome, APP))
log   = logging.getLogger(APP)

if __name__ == "__main__":
    log.info("start...")
    try:
        pidfile = "pids/%s/%s.pid" % (APP, APP)
        pidfile = lockfile.pidlockfile.PIDLockFile(pidfile)
        files_preserve=[logging.root.handlers[1].stream.fileno()]
        dmn = daemon.DaemonContext(None, os.getcwd(), pidfile=pidfile, files_preserve=files_preserve)
        dmn.open()
        alarm = Alarm()
        alarm.run()
    except Exception as e:
        log.exception(e)
    log.info("end!")
    