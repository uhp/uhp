#!/usr/bin/env python
# coding=utf-8


#for main run
import os,sys
commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon");
sys.path.append(commondir)

import database
from model.alarm import Alarm
from model.instance import Instance
from model.host_group_var import GroupHost
from lib.manager import Manager
from lib.logger import log


class AlarmRuleManager(Manager):
    def __init__(self):
        pass

    def pre_check(self):
        '''
        覆盖manager的pre_check
        每次检查之前都获取判断规则
        '''
        #获取instance列表,得到所有机器和角色的对应关系
        self.role_host_map = {}
        self.rule_lists = []
        self.group_host_map = {}
        session = database.getSession()

        for instance in session.query(Instance).filter(Instance.status==Instance.STATUS_START) :
            host = instance.host
            role = instance.role
            if not self.role_host_map.has_key(role) :
                self.role_host_map[role] = []
            self.role_host_map[role].append(host)

        for gh in session.query(GroupHost):
            group = gh.group
            host = gh.hostname
            if not self.group_host_map.has_key(group) :
                self.group_host_map[group] = []
            self.group_host_map[group].append(host)

        for alarm in session.query(Alarm):
            active_lists, except_lists = alarm.get_host_tuple()
            self.rule_lists.append( Rule(alarm.name,alarm.expression,alarm.callback,active_lists,except_lists) )

        session.close()

    def combine_host_rule(self, combine, level, rule):
        if not combine.has_key(rule.name) :
            combine[rule.name] = {}
            combine[rule.name]['level'] = -1

        now_level = combine[rule.name]['level']
        if level > now_level:
            combine[rule.name]['level'] = level
            combine[rule.name]['rule'] = rule

    def judge_rule(self, host, rule):
        level = -1
        
        for active_host in rule.active_lists:
            if active_host == host:
                level = 3
            elif self.belong_inst_group(active_host, host) :
                level = 2
            elif active_host == Alarm.HOST_ALL and host != "cluster" :
                level = 1

        for except_host in rule.except_lists:
            if except_host == host or self.belong_inst_group(except_host, host)  or  except_host == Alarm.HOST_ALL :
                level = -1

        return level

    def belong_inst_group(self, rule_host, host):
        '''
        判断某个rule_host是不是分组或者角色
        如果是，判断host是不是属于这个分组或者角色
        '''
        if self.role_host_map.has_key(rule_host) and \
            host in self.role_host_map[rule_host] :
            return True
        if self.group_host_map.has_key(rule_host) and \
            host in self.group_host_map[rule_host] :
            return True
        return False
        

    def get_rule_by_host(self, host):
        '''
        遍历所有的规则,判断该规则是否对这个host生效。
        host可能为一个指定的主机名称或者cluster
        如果生效，需要返回生效等级
        如果是all导致该host生效的，等级为1
        如果是角色或者分组导致该host生效的，等级为2
        如果是直接指定该host的，等级为3

        将所有通过的规则合并,相同名字的取等级较高的规则。最终返回。

        '''
        combine = {}
        for rule in self.rule_lists:
            level = self.judge_rule(host,rule)
            if level != -1 :
                self.combine_host_rule(combine, level, rule)

        rule_list = []
        for (name,rule_info) in combine.items():
            if rule_info['level'] != -1:
                rule_list.append(rule_info['rule'])
        return rule_list
        
class Rule:
    def __init__(self, name, expression, callback, active_lists, except_lists):
        self.name = name
        self.expression = expression
        self.callback = callback
        self.exp_func = None
        self.exp_args = None
        self.callback_func = None
        self.active_lists = active_lists
        self.except_lists = except_lists
        

    def __str__(self):
        return "Rule : %s %s %s" % (self.name, self.expression, self.callback)
        


if __name__ == "__main__" :
    print "test the rule manager"
    rule_manager = AlarmRuleManager()
    rule_manager.pre_check()
    print "rule for cluster"
    for rule in rule_manager.get_rule_by_host("cluster") :
        print rule.name
    print "rule for hadoop3"
    for rule in rule_manager.get_rule_by_host("hadoop3") :
        print rule.name
