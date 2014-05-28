#!/usr/bin/env python
# coding=utf-8

import database
from model.alarm import Alarm
from model.instance import Instance
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
        #获取instance列表,得到所有机器和角色的对应关系
        self.alarm_rule_map = {}
        self.host_role_map = {}
        session = database.getSession()

        for alarm in session.query(Alarm):
            host = alarm.host
            if not self.alarm_rule_map.has_key(host):
                self.alarm_rule_map[host] = []
            self.alarm_rule_map[host].append( Rule(alarm.name,alarm.expression,alarm.callback) )

        for instance in session.query(Instance):
            host = instance.host
            role = instance.role
            if not self.host_role_map.has_key(host) :
                self.host_role_map[host] = []
            self.host_role_map[host].append(role)

        session.close()

    def combine_host_rule(self, combine, host):
        if self.alarm_rule_map.has_key(host) :
            for rule in self.alarm_rule_map[host] :
                combine[rule.name] = rule

    def get_rule_by_host(self, host):
        if host == "cluster":
            if self.alarm_rule_map.has_key("cluster") :
                return self.alarm_rule_map["cluster"];
            else:
                return []
        
        combine = {}
        #combine the * rule
        self.combine_host_rule(combine,"*")

        #combine the role rule
        if self.host_role_map.has_key(host):
            for role in self.host_role_map[host] :
                self.combine_host_rule(combine,role)

        #combine the own host
        self.combine_host_rule(combine,host)
        
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
        
