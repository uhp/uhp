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
    
    def show_metric(self):
        precision = self.get_argument("precision")
        metric = self.get_argument("metric")
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
       
        hosts = ['hadoop5', 'hadoop6', 'hadoop7']
        for host in hosts:
            rrd_metric = rrd_wrapper.query(metric, start, end, hostname=host, clusterName='test_hadoop')

        ret = {"data":static_config.monitor_show_info}
        self.ret("ok", "", ret);

    #获取所有服务的静态信息
    def services_info(self):
        session = database.getSession()
        active = []
        for service in session.query(Service):
            if service.status == Service.STATUS_ACTIVE :
                active.append(service.service)
        
        services_copy = copy.deepcopy(static_config.services)
        
        for temp in services_copy:
            if temp['name'] in active:
                temp['active'] = True;
            else:
                temp['active'] = False;
            #计算url
            if temp.has_key('web') :
                urls = []
                for web in temp['web'] :
                    port = ""
                    for gv in session.query(GroupVar).filter(GroupVar.name == web['port']) :
                        port = gv.value
                    for instance in session.query(Instance).filter(Instance.role == web['role']) :
                        url = {"role":web['role'],"host":instance.host,"port":port}
                        urls.append(url)
                temp['urls'] = urls;
            else:
                temp['urls'] = []
            #特殊规则
            #根据dfs_namenode_support_allow_format 配置 控制是否放出format参数
            if temp['name'] == 'hdfs' :
                should_format = database.get_service_conf(session,'hdfs','dfs_namenode_support_allow_format')
                if should_format != None and should_format != 'true' :
                    wi = 0
                    find = False;
                    for action in temp['actions']:
                        if action['name'] == 'format':
                            find = True
                            break;
                        wi = wi +1
                    if find:
                        del temp['actions'][wi]
                    

        ret = { "services" : services_copy , "role_check_map" : static_config.role_check_map }
        session.close()
        self.ret("ok", "", ret);
        
    def service_info(self):
        service = self.get_argument("service")
        ret = { "name": service,"instances" : self.get_instance(service),"summary":self.get_service_summary(service) }
        self.ret("ok", "", ret);
        
    def get_instance(self,service):
        session = database.getSession()
        instances = session.query(Instance).filter(Instance.service == service )
        ret = [];
        for instance in instances:
            ret.append(instance.format());
        session.close()
        return ret;
        
        
