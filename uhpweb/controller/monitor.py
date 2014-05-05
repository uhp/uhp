# -*- coding: UTF-8 -*-
import os
import json
import logging
import time
import copy

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
        
    def submenu(self):
        ret = {"submenu":static_config.monitormenus}
        self.ret("ok", "", ret);
    
    def show_info(self):
        ret = {"data":static_config.monitor_show_info}
        self.ret("ok", "", ret);
   
    #获取所有的机器
    def _host_list(self):
        session = database.getSession()
        hosts = session.query(Host)
        temp = [host.hostname for host in hosts]
        session.close()
        return temp

    def show_metric(self):
        precision = self.get_argument("precision")
        metric = self.get_argument("metric")
        if isinstance(precision, unicode): 
            precision = precision.encode('ascii', 'ignore')
        if isinstance(metric, unicode): 
            metric = metric.encode('ascii', 'ignore')
        rrd_wrapper = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)
        start = '-1d'
        end = 'now'

        if precision == 'p1':
            start = '-2h' 
        elif precision == 'p2':
            start = '-7d'
        elif precision == 'p3':
            start = '-30d'
        elif precision == 'p4':
            start = '-365d'
       
        hosts = self._host_list()
        data = []
        for host in hosts:
            if isinstance(host, unicode): 
                host = host.encode('ascii', 'ignore')
            app_log.debug('rrd_wrapper.query(%s, %s, %s, hostname=%s, clusterName=%s)' % (metric,start,end,host,'test_hadoop'))
            rrd_metric = rrd_wrapper.query(metric, start, end, hostname=host, clusterName='test_hadoop')
            xy = rrd.convert_to_xy(rrd_metric)
            data.append({'host':host, 'x':xy[0], 'y':xy[1]})
        ret = {"data":data}
        self.ret("ok", "", ret);

