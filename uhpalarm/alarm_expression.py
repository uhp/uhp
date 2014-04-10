#!/usr/bin/env python
# coding=utf-8

from alarm import Manager
from alarm import Alarm

class AlarmExpManager(Manager):
    def __init__(self):
        self.exp_map = AlarmExpMap()
    
    def judge(self,data_set,rule):
        
        #节省重复解析计划的时间
        if rule.exp_func == None or rule.exp_func == None :
            (func,args) = self._parse_expression(rule.expression)
            rule.exp_func = func
            rule.exp_args = args
        
        #为expression的上下文准备rule
        self.exp_map.rule = rule
        
        real_args = self._get_args_from_ds(data_set,rule.exp_args)
        exp_result = apply(rule.exp_func,real_args)
        return exp_result

    def _parse_expression(self, expression):
        '''
                  翻译表达式  返回调用的函数和参数的变量列表
        '''
        return ( self.exp_map.max, ("load_one", 10, 20) )
        
        
    def _get_args_from_ds(self, data_set, args):
        pass
    
class AlarmExpMap:
    '''
    表达式的判断方式集合类
    每个判断函数可以随意地指定调用参数
    此外还可以使用self.rule 获取当前的判断的规则
    '''
    def __init__(self):
        pass
    
    def max(self, value, warn, error):
        if value > error :
            return (Alarm.ALARM_ERROR, "%s 检查到错误状态  %f 大于  %f" % (self.rule.name, value, error) )
        elif value > warn:
            return (Alarm.ALARM_WARN, "%s 检查到警告状态  %f 大于  %f" % (self.rule.name, value, warn) )
        else:
            return (Alarm.ALARM_OK, "")
    