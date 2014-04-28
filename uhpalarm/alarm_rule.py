#!/usr/bin/env python
# coding=utf-8

import database
from model.alarm import Alarm
from lib.manager import Manager
from lib.logger import log


class AlarmRuleManager(Manager):
    def __init__(self):
        self.alarm_rule_map = {}
        
    def pre_check(self):
        '''
        覆盖manager的pre_check
        每次检查之前都获取判断规则
        '''
        self.alarm_rule_map = {}
        session = database.getSession()
        for alarm in session.query(Alarm):
            host = alarm.host
            if not self.alarm_rule_map.has_key(host):
                self.alarm_rule_map[host] = []
            self.alarm_rule_map[host].append( Rule(alarm.name,alarm.expression,alarm.callback) )


    def get_rule_by_host(self, host):
        if host == "cluster":
            if self.alarm_rule_map.has_key("cluster") :
                return self.alarm_rule_map["cluster"];
            else:
                return []
        
        combine = {}
        #combine the * rule
        if self.alarm_rule_map.has_key("*") :
            for rule in self.alarm_rule_map["*"] :
                combine[rule.name] = rule
        #combine the own host
        if self.alarm_rule_map.has_key(host) :
            for rule in self.alarm_rule_map[host] :
                combine[rule.name] = rule
        
        rule_list = []
        for (name,rule) in combine.items():
            rule_list.append(rule)
        return rule_list
        
class Rule:
    def __init__(self, name, expression, callback):
        self.name = name
        self.expression = expression
        self.callback = callback
        self.exp_func = None
        self.exp_args = None
        self.callback_func = None
        

    def __str__(self):
        return "Rule : %s %s %s" % (self.name, self.expression, self.callback)
        
