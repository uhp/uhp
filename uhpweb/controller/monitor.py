# -*- coding: UTF-8 -*-
import os
import json
import logging
import time
import copy
import math

import tornado
from sqlalchemy.orm import query,aliased
from sqlalchemy import and_,or_,desc,asc
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

import async
import static_config
import rrd
import database
import config
from rrd import RrdWrapper
import util
import callback_lib
import mm
from controller import BaseHandler
from controller import shell_lib
from model.instance import Instance
from model.host_group_var import Host,Group,GroupHost,HostVar,GroupVar
from model.task import Task
from model.services import Service
from model.callback import CallBack

app_log = logging.getLogger("tornado.application")
        
class MonitorBackHandler(BaseHandler):
    
    @tornado.web.authenticated
    def get(self , path):
        user = self.get_current_user();
        if user['type'] != 0 :
            self.ret("error","this user is not monitor")
            return
        if hasattr(self, path) :
            fun = getattr(self, path);
            if callable(fun):
                apply(fun)
        else:
            self.ret("error","unsupport action")
            
    @tornado.web.authenticated
    def post(self , path):
        self.get(path)
        
    def user(self):
        user = self.get_current_user();
        ret = {"user":user,"menus":static_config.monitormenus}
        self.ret("ok", "", ret);
    
    # unuse 
    def submenu(self):
        ret = {"submenu":static_config.monitormenus}
        self.ret("ok", "", ret);
   
    def _query_var(self, group, name):
        session = database.getSession()
        try:
            groupVars = session.query(GroupVar).filter(and_( GroupVar.name == name , GroupVar.group == group ) )
            for groupVar in groupVars:
                if groupVar.type == 0:
                    return groupVar.value
                return groupVar.value.split(',')
        finally:
            session.close()

    def _checkout_groups_metrics(self, group_names):
        all_metric_groups = static_config.monitor_show_info['metrics']

        # 指定组的指标
        # { name:,metrics:{} }
        groups_metrics = {} 
        for group_name in group_names:
            group_name = self._sure_str(group_name)
            if group_name in all_metric_groups:
                group_metrics = all_metric_groups[group_name]
                group_metrics_map = dict([(m['name'],m) for m in group_metrics])
                groups_metrics.update(group_metrics_map)
        return groups_metrics

    def show_info(self):
        group_names = self.get_arguments("groups")
        show_info = {}
        rras = self._query_var('all', 'gmetad_rras')
        precisions = rrd.parse_precision(rras)

        show_info['precisions']=[]
        for sec in precisions:
            if sec < 86400:
                h = int(math.ceil(sec/3600))
                precision='%d小时' % h
            else:
                d = int(math.ceil(sec/86400))
                if d == 7:
                    precision='1周'
                elif d >=28 and d <=31:
                    precision='1月'
                elif d > 360 and d <= 366:
                    precision='1年'
                else: 
                    precision='%d天' % d
            show_info['precisions'].append({'name':'p%d'%sec, 'display':precision})
        show_info['precision'] = show_info['precisions'][0]['name'] # default
        
        rrd_wrapper = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        all_rrd_metrics = rrd_wrapper.get_all_rrd_names(clusterName=cluster_name)

        # 指定组的指标
        # { name:,metrics:{} }
        groups_metrics = self._checkout_groups_metrics(group_names)

        show_info['metrics'] = [] 
        #metric_name_map = dict([ (m['name'], m['display']) for m in static_config.monitor_show_info['metrics'] ])
        for metric in all_rrd_metrics:
            if metric not in groups_metrics: 
                app_log.debug("metric %s not in groups_metrics" % metric)
                continue
            app_log.debug("metric %s ok" % metric)
            m = groups_metrics[metric] 
            show_info['metrics'].append(m)
        
        show_info['metric'] = show_info['metrics'][0]['name']
        show_info['hosts'] = self._host_list()
        show_info['host'] = show_info['hosts'][0]

        ret = {"data":show_info}
        self.ret("ok", "", ret);
   
    # 获取所有的机器
    def _host_list(self):
        session = database.getSession()
        hosts = session.query(Host)
        temp = [host.hostname for host in hosts]
        session.close()
        return temp

    def _sure_str(self, str):
        if isinstance(str, unicode): 
            str = str.encode('ascii', 'ignore')
        return str

    def show_hosts_metric(self):
        precision = self.get_argument("precision")
        precision = self._sure_str(precision)
        metric = self.get_argument("metric")
        metric = self._sure_str(metric)
        hosts = self.get_arguments("hosts")
        rrd_wrapper = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)

        sec = int(precision[1:])
        start = "-%ds" % sec
        end = "now" 

        data = []
        
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        for host in hosts:
            host = self._sure_str(host)
            try:
                rrd_metric = rrd_wrapper.query(metric, start, end, hostname=host, clusterName=cluster_name)
            except Exception, e:
                if 'RRD File not exists' in str(e): continue
                raise e
            xy = rrd.convert_to_xy(rrd_metric)
            data.append({'host':host, 'x':xy[0], 'y':xy[1]})
        ret = {"data":data}
        self.ret("ok", "", ret);

    # 显示单机的全部指标
    def show_host_metrics(self):
        precision = self.get_argument("precision")
        precision = self._sure_str(precision)
        host = self.get_argument("host")
        host = self._sure_str(host)
        group_names = self.get_arguments("groups")
        
        
        rrd_wrapper = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)

        sec = int(precision[1:])
        start = "-%ds" % sec
        end = "now" 

        data = []
        
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        metrics = rrd_wrapper.get_all_rrd_names(clusterName=cluster_name)
        
        groups_metrics = self._checkout_groups_metrics(group_names)

        for metric in metrics:
            if metric not in groups_metrics: continue
            metric = self._sure_str(metric)
            try:
                rrd_metric = rrd_wrapper.query(metric, start, end, hostname=host, clusterName=cluster_name)
            except Exception, e:
                if 'RRD File not exists' in str(e): continue
                raise e
            xy = rrd.convert_to_xy(rrd_metric)
            data.append({'metric':metric, 'x':xy[0], 'y':xy[1]})
        ret = {"data":data}
        self.ret("ok", "", ret);
