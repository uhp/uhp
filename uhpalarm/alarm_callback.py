#!/usr/bin/env python
# coding=utf-8

import time

import mail_center
from lib.manager import Manager
from lib.logger import log
from lib import contants

class AlarmCallbackManager(Manager):
    def __init__(self):
        self.cb_map = AlarmCallbackMap()
    
    def callback(self, host, rule, exp_result):
        #节省重复反射时间
        if rule.callback_func == None :
            rule.callback_func = self._parse_callback(rule.callback)

        self.cb_map.rule = rule
        self.cb_map.host = host
        #调用callback
        apply(rule.callback_func, exp_result)
        
    def _parse_callback(self, func_name):
       if hasattr(self.cb_map, func_name) :
           return getattr(self.cb_map, func_name)
       else:
           raise Exception("CallBackError","can't find %s in callback map" % func_name)

class AlarmCallbackMap:
    '''
    回调的方式集合类
    回调会接收expression返回的元祖作为输入
    当前共有两个输入:  判断状态  判断信息
    此外,回调函数还可以使用self.rule获取当前判断的rule
    self.host 获取当前的判断的host
    '''
    
    def __init__(self):
        pass

    def print_log(self, state, msg):
        log.info("%s %s %s" % (self.rule.name, state, msg))

    def send_mail(self, state, msg):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        if state != contants.ALARM_OK:
            mail_center.add_alarm_info({"ts": now,"name":self.rule.name,"host":self.host,"state":state,"msg":msg})
            log.info("send mail %s %s %s" % (self.rule.name, state, msg) )
