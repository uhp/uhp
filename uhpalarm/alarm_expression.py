#!/usr/bin/env python
# coding=utf-8

import re
import string

from lib import contants
from lib.manager import Manager
from lib.logger import log

class AlarmExpManager(Manager):
    def __init__(self):
        self.exp_map = AlarmExpMap()
        self.exp_pattern = re.compile('^([a-zA-Z0-9_\\-]+)\\((.*)\\)$')
        self.double_pattern = re.compile('^[0-9]+(\\.[0-9]*)?$') 
        self.var_pattern = re.compile('^[0-9a-zA-Z\\._-]+$')
    
    def judge(self, host, rule, data_set):
        
        #节省重复解析计划的时间
        if rule.exp_func == None or rule.exp_func == None :
            (func_name, func, args) = self._parse_expression(rule.expression)
            rule.exp_func_name = func_name
            rule.exp_func = func
            rule.exp_args = args
        
        #为expression的上下文准备rule
        self.exp_map.host = host
        self.exp_map.rule = rule
        self.exp_map.data_set = data_set
        
        #如果host是cluster的就进行数组过滤
        filter_result = self.exp_map.filter_cluster()
        if filter_result != None :
            return filter_result

        real_args = self._get_args_from_ds(data_set,rule.exp_args)
        exp_result = apply(rule.exp_func,real_args)
        log.info("apply rule_name %s host %s func %s with args %s" % (rule.name, host, rule.exp_func, str(real_args) ))
        return exp_result

    def _parse_expression(self, expression):
        '''
        翻译表达式  返回调用的函数和参数的变量列表
        正则表达式如下：'^([a-zA-Z0-9_\\-]+)\\((.*)\\)$'
        '''
        m = self.exp_pattern.match(expression)
        if m and len( m.groups() ) == 2:
            gs = m.groups()
            func_name = gs[0]
            args_str = gs[1]
            args = args_str.split(',')
            if hasattr(self.exp_map, func_name) :
                return (func_name, getattr(self.exp_map, func_name), args )
            else:
                raise Exception("ExpError","can't find %s in map" % func_name)
        else:
            raise Exception("ExpError", "pattern can't match %s" % expression)
        
        
    def _get_args_from_ds(self, data_set, args):
        real_args = []
        for arg in args:
            arg = arg.strip()
            if len(arg) == 0 :
                continue
            
            #is string
            if len(arg) >= 3 and (
            ( arg.startswith("\"") and arg.endswith("\"") ) or
            ( arg.startswith("'") and arg.endswith("'" ) )
            ):
                str_arg = arg[1:len(arg)-1]
                real_args.append(str_arg)
                #log.debug("find string args %s",str_arg)
            #is int or double    
            elif self.double_pattern.match( arg ):
                dou_arg = string.atof(arg)
                real_args.append(dou_arg)
                #log.debug("find double args %s",dou_arg)  
            #is var
            elif self.var_pattern.match( arg ):
                if data_set.has_key( arg ):
                    var_arg = data_set[arg]
                    #log.debug("find var args %s",var_arg)
                    real_args.append(var_arg)
                else:
                    real_args.append(None)
        return real_args
    
class AlarmExpMap:
    '''
    表达式的判断方式集合类
    每个判断函数可以随意地指定调用参数
    此外还可以使用
    self.rule 获取当前的判断的规则
    self.host 获取当前的判断的host
    self.data_set 获取当前的判断集合

    对于cluster的函数,请在cluster_func加入对于的函数

    '''
    def __init__(self):
        self.cluster_func = ["sum_and_equal"]

    def filter_cluster(self):
        func_name = self.rule.exp_func_name
        if self.host == 'cluster' :
            if func_name in self.cluster_func :
                return None 
            else:
                return (contants.ALARM_CONFIG_ERROR, u"检查集群规则使用了非集群的判断函数 规则名称:%s 判断函数:%s " % (self.rule.name, func_name ) )
        else:
            if func_name in self.cluster_func :
                return (contants.ALARM_CONFIG_ERROR, u"检查非集群规则使用了集群的判断函数 规则名称:%s 判断函数:%s " % (self.rule.name, func_name ) )
            else:
                return None

    def max(self, value, warn, error):
        if value > error :
            return (contants.ALARM_ERROR, u"%s 检查到错误状态  %f 大于  %f" % (self.rule.name, value, error) )
        elif value > warn:
            return (contants.ALARM_WARN, u"%s 检查到警告状态  %f 大于  %f" % (self.rule.name, value, warn) )
        else:
            return (contants.ALARM_OK, "")

    def sum_and_equal(self, point_name, want):
        return (contants.ALARM_OK, "")  
