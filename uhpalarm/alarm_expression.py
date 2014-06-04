#!/usr/bin/env python
# coding=utf-8

import re
import string
import time

import database
from lib import contants
from lib.manager import Manager
from lib.logger import log
from lib.exp_parser import ExpParser
from model.instance import Instance
from plug import namenode_web,resourcemanager_web,check_instance_state

class AlarmExpManager(Manager):
    def __init__(self):
        self.exp_map = AlarmExpMap()
        self.exp_parser = ExpParser()
        #self.exp_pattern = re.compile('^([a-zA-Z0-9_\\-]+)\\((.*)\\)$')
        #self.double_pattern = re.compile('^[0-9]+(\\.[0-9]*)?$') 
        #self.var_pattern = re.compile('^[0-9a-zA-Z\\._-]+$')
    
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
        
        #如果host是cluster的就进行数组过滤进行提示, 感觉无用先去掉
        #filter_result = self.exp_map.filter_cluster()
        #if filter_result != None :
        #    return filter_result

        real_args = self._get_args_from_ds(data_set,rule.exp_args)
        begin = time.time()
        exp_result = apply(rule.exp_func,real_args)
        end = time.time()
        log.info("apply rule_name %s host %s func %s with args %s using %.3lf S" % (rule.name, host, rule.exp_func, str(real_args), end-begin ))
        return exp_result

    def _parse_expression(self, expression):
        '''
        使用语法解析工具解析,解析
        '''
        func_name,exp_list = self.exp_parser.parse_exp(expression)
        #log.info("parse the %s : %s %s" % expression,func_name," ".join(exp_list))
        if func_name != None :
            if hasattr(self.exp_map, func_name) :
                return (func_name, getattr(self.exp_map, func_name), exp_list )
            else:
                raise Exception("ExpError","can't find %s in map" % func_name)
        else:
            raise Exception("ExpError", "pattern can't match %s" % expression)
        
        
    def _get_args_from_ds(self, data_set, args):
        real_args = []
        for arg in args:
            (value,msg) = self.exp_parser.get_exp_value(arg,data_set)
            real_args.append(value)
        return real_args
    
class AlarmExpMap:
    '''
    表达式的判断方式集合类
    每个判断函数可以随意地指定调用参数
    此外还可以使用
    self.rule 获取当前的判断的规则
    self.host 获取当前的判断的host
    self.data_set 获取当前的判断集合

    对于cluster的函数,请在cluster_func加入对应的函数

    '''
    def __init__(self):
        pass
        #self.cluster_func = ["sum_and_equal"]

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
            return (contants.ALARM_ERROR, u"%s 检查到错误状态  %.2f 大于  %.2f" % (self.rule.name, value, error) )
        elif value > warn:
            return (contants.ALARM_WARN, u"%s 检查到警告状态  %.2f 大于  %.2f" % (self.rule.name, value, warn) )
        else:
            return (contants.ALARM_OK, "")

    def min(self, value, warn, error):
        if value < error :
            return (contants.ALARM_ERROR, u"%s 检查到错误状态  %.2f 小于  %.2f" % (self.rule.name, value, error) )
        elif value < warn:
            return (contants.ALARM_WARN, u"%s 检查到警告状态  %.2f 小于  %.2f" % (self.rule.name, value, warn) )
        else:
            return (contants.ALARM_OK, "")

    def disk_use(self, warn, error):
        '''
        判断硬盘的使用量，结合ganglia的拓展模块multidisk.py一起使用
        默认判断所有dev-xxxx-disk_used.rrd
        '''
        key_pattern = re.compile('^dev_[a-zA-Z0-9]*?_disk_used$')  
        level = 0 
        msg = u""
        found = False
        for (k,v) in self.data_set.items():
            m = key_pattern.match(k)
            if m :
                found = True
                if v >= error :
                    level = level | 2
                    msg = msg + (u"指标%s %.2f 大于 %.2f. " % (k,v,error))
                elif v >= warn :
                    level = level | 1
                    msg = msg + (u"指标%s %.2f 大于 %.2f. " % (k,v,warn))
        if found == False :
            return (contants.ALARM_ERROR, u"找不到磁盘统计数据.")
        elif ( level & 2 ) > 0 :
            return (contants.ALARM_ERROR, msg)
        elif ( level & 1 ) > 0 :
            return (contants.ALARM_WARN, msg)
        else :
            return (contants.ALARM_OK, "")

    def resourcemanager_web(self):
        session = database.getSession()
        rm_port = database.get_service_conf(session,"yarn","yarn_nm_webapp_port")
        rms = []
        for inst in session.query(Instance).filter(Instance.role == "resourcemanager"):
            rms.append(inst.host)
        session.close()
        if len(rms) == 0 :
            return  (contants.ALARM_ERROR, u"%s 检查不到有resourcemanager" % self.rule.name )
        if len(rms) != 1 :
            return  (contants.ALARM_ERROR, u"%s 检查到有多个resourcemanager %s" % (self.rule.name, ",".join(rms) ) )
        return resourcemanager_web.resourcemanager_web(rms[0],rm_port)

    def namenode_web(self):
        session = database.getSession()
        nm_web_port = database.get_service_conf(session,"hdfs","dfs_namenode_http_address_port")
        nms = []
        for inst in session.query(Instance).filter(Instance.role == "namenode"):
            nms.append(inst.host)
        session.close()
        return namenode_web.namenode_web(nms, nm_web_port)

    #below is cluster function
    def check_instance_state(self):
        return check_instance_state.check_instance_state()

    def sum_and_equal(self, point_name, want):
        return (contants.ALARM_OK, "")  

