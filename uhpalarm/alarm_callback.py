#!/usr/bin/env python
# coding=utf-8

import time

import mail_center
import database
from lib.manager import Manager
from lib.logger import log
from lib import contants
from model.alarm import AlarmList

class AlarmCallbackManager(Manager):
    def __init__(self):
        self.cb_map = AlarmCallbackMap()
    
    def pre_check(self):
        self.cb_map.pre_check()
    
    def post_check(self):
        self.cb_map.post_check()

    def callback(self, host, rule, exp_result):
        #节省重复反射时间
        if rule.callback_func == None :
            rule.callback_func = self._parse_callback(rule.callback)

        self.cb_map.rule = rule
        self.cb_map.host = host
        #调用base callback
        apply(self.cb_map.base_callback, exp_result)
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

    def pre_check(self):
        self.session = database.getSession()

    def post_check(self):
        self.session.close()

    def base_callback(self, state, msg):
        if state != contants.ALARM_OK :
            self.session.add( AlarmList(self.rule.name, self.host, msg, state, int(time.time()) ))
        self.session.commit()

    def print_log(self, state, msg):
        log.info("%s %s %s" % (self.rule.name, state, msg))

    def send_mail(self, state, msg):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        if state != contants.ALARM_OK:
            mail_center.add_alarm_info({"ts": now,"name":self.rule.name,"host":self.host,"state":state,"msg":msg})
            log.error("send mail %s %s %s" % (self.rule.name, state, msg) )
