#!/usr/bin/env python
# coding=utf-8

from alarm import Manager

class AlarmRuleManager(Manager):
    def __init__(self):
        pass
        
    def get_rule_by_host(self):
        rule_list = []
        rule_list.append(Rule("max(a,10)","sendmail"))
        return rule_list
        
class Rule:
    def __init__(self, name, expression, callback):
        self.name = name
        self.expression = expression
        self.callback = callback
        self.exp_func = None
        self.exp_args = None
        self.cb_func = None
        
        