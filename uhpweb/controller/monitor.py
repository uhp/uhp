# -*- coding: UTF-8 -*-
import os
import json
import logging
import time
import copy
import math
import re
from decimal import Decimal

import tornado
from sqlalchemy.orm import query,aliased,defer
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
import shell_lib
from controller import BaseHandler
from controller import shell_lib
from model.instance import Instance
from model.host_group_var import Host,Group,GroupHost,HostVar,GroupVar
from model.task import Task
from model.services import Service
from model.callback import CallBack
from model.alarm import *

__all__ =  ['MonitorBackHandler']

app_log = logging.getLogger("tornado.application")
        
class MonitorBackHandler(BaseHandler):

    def __init__(self, application, request, **kwargs):
        super(MonitorBackHandler, self).__init__(application, request, **kwargs)

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
    
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        rrd_wrapper  = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)

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
        

        # 指定组的指标
        # { name:,metrics:{} }
        groups_metrics = self._checkout_groups_metrics(group_names)
        all_rrd_metrics = [] 
        try:
            all_rrd_metrics = rrd_wrapper.get_all_rrd_names(clusterName=cluster_name)
        except:
            app_log.exception('')

        show_info['metrics'] = [] 
        #metric_name_map = dict([ (m['name'], m['display']) for m in static_config.monitor_show_info['metrics'] ])
        for metric in all_rrd_metrics:
            if metric not in groups_metrics: 
                #app_log.debug("metric %s not in groups_metrics" % metric)
                continue
            #app_log.debug("metric %s ok" % metric)
            m = groups_metrics[metric] 
            show_info['metrics'].append(m)
        
        if show_info['metrics']:
            show_info['metric'] = show_info['metrics'][0]['name']
        show_info['hosts'] = self._host_list()
        show_info['host'] = show_info['hosts'][0]

        ret = {"data":show_info}
        self.ret("ok", "", ret);
  
    # [{name:, roles:{role:[instance]}}]
    # ext==True: [{name:, roles:{role:[instance]}, instances:{role:[ins obj]}}]
    def _query_active_services(self, ext=False):
        session = database.getSession()
        try:
            active = []
            for service in session.query(Service):
                if service.status != Service.STATUS_ACTIVE : continue
                if service.service == 'client': continue
                instances = session.query(Instance).filter(Instance.service == service.service)
                service = {'name':service.service, 'roles':{}}
                if ext: service['instances'] = {}
                for ins in instances:
                    if ins.role not in service['roles']:
                        service['roles'][ins.role] = []
                    service['roles'][ins.role].append(ins.host)
                    if ext:
                        if ins.role not in service['instances']:
                            service['instances'][ins.role] = []
                        service['instances'][ins.role].append(ins)
                    
                active.append(service)
            return active
        finally:
            session.close()
    
    # services overview 简单列表信息
    def services_metrics2(self):
        # [{name:, roles:{role:[instance]}, instances:{role:[ins obj]}}]
        services         = self._query_active_services(ext=True)
        cluster_name     = self._query_var('all', 'cluster_name')
        cluster_name     = self._sure_str(cluster_name)
    
        rrd_wrapper = RrdWrapper(config.ganglia_rrd_dir, config.rrd_image_dir)
   
        # 获取多个host的metrics，分别封装
        # @return: {name:,hosts:[{host:$host, info:[{name:,value:,unit:}]}]}
        def _multi_host_metrics(name, hosts, ori_host_metrics):
            service_metrics = {'name':name, 'hosts':[]}
            for host in hosts:
                # host = self._sure_str(host)
                host_metrics = copy.deepcopy(ori_host_metrics)
                for host_metric in host_metrics:
                    value = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, host_metric['name'])
                    if 'func' in host_metric:
                        value = apply(host_metric['func'], (value,host_metric))
                        del host_metric['func']
                    else:
                        value = apply(_f_f2i, (value,host_metric))
                        #host_metric.update({'value':value})
                service_metrics['hosts'].append({'host':host, 'info':host_metrics})
            return service_metrics
       
        # [{name:,hosts:[{host:$host, state:'leader', info:[{name:,value:,unit:,}]}]}] 
        services_metrics = []

        # my_services = ['hdfs','yarn','hive','hbase']

        def _service(name, services):
            for service in services:
                if name == service['name']:
                    return service
            return None

        uptime_limit = int(time.time()) - (5 * 60)
        def _ext_state(service_metrics, inss, state1='leader', state2='follower'):
            for host in service_metrics['hosts']:
                # 补充state
                state = "unknown"
                host_ins = None
                for ins in inss:
                    if ins.host == host['host']:
                        host_ins = ins
                        break
                if host_ins and host_ins.monitor_time > uptime_limit and host_ins.msg:
                    msg = json.loads(host_ins.msg)
                    if 'leader' in msg and msg['leader']:
                        state = state1
                    else:
                        state = state2
                host['state'] = state

        def _f_b2m(v,m): 
            v = self._none_2_0(v)
            v = v / 1024 / 1024
            m['value'] = "%.2f" % v
            m['unit'] = 'MB'
        
        def _f_m2mg(v,m): 
            v = self._none_2_0(v)
            if v > 1024:
                v = v / 1024
                m['unit'] = 'GB'
            else:
                m['unit'] = 'MB'
            m['value'] = "%.2f" % v

        def _f_f2f(v,m): 
            v = self._none_2_0(v)
            m['value'] = "%.2f" % v
        
        def _f_f2i(v,m): 
            v = self._none_2_0(v)
            m['value'] = "%0.f" % v

        def _f_space(v,m):
            v = self._none_2_0(v)
            if v > 1024:
                v = v / 1024
                m['unit'] = 'TB'
            else:
                m['unit'] = 'GB'
            m['value'] = "%.2f" % v
        
        # zookeeper
        service = _service(u'zookeeper', services)
        if service:
            # zookeeper
            service_name = 'zookeeper'
            if service_name in service['roles']:
                hosts = service['roles'][service_name]
                ori_host_metrics = [
                    {'name' : 'zookeeper_memory_memHeapMax',          'display' : 'JVM最大堆内存',    'func' : _f_b2m},
                    {'name' : 'zookeeper_memory_memHeapCommitted',    'display' : 'JVM申请堆内存',    'func' : _f_b2m},
                    {'name' : 'zookeeper_memory_memHeapUsed',         'display' : 'JVM使用堆内存',    'func' : _f_b2m},
                    {'name' : 'zookeeper_memory_memNonHeapMax',       'display' : 'JVM最大非堆内存',  'func' : _f_b2m},
                    {'name' : 'zookeeper_memory_memNonHeapCommitted', 'display' : 'JVM使用非堆内存',  'func' : _f_b2m},
                    {'name' : 'zookeeper_memory_memNonHeapUsed',      'display' : 'JVM提交非堆内存',  'func' : _f_b2m},
                    {'name' : 'zookeeper_Threading_ThreadCount',      'display' : '线程数'},
                ]
                
                service_metrics = _multi_host_metrics('Zookeeper', hosts, ori_host_metrics)
                inss = service['instances']['zookeeper']
                _ext_state(service_metrics, inss, 'leader', 'follower')
                services_metrics.append(service_metrics)
            
        # hdfs
        service = _service(u'hdfs', services)
        if service:
            # nn
            service_name = 'namenode'
            if service_name in service['roles']:
                hosts = service['roles'][service_name]
                ori_host_metrics = [
                    {'name':'dfs.namenode.BlockReportAvgTime',                          'display' :'块汇报的平均时间', 'func':_f_f2f, 'unit':'MS'},
                    {'name':'dfs.namenode.SyncsAvgTime',                                'display' :'Syncs操作平均时间', 'func':_f_f2f, 'unit':'MS'},
                    {'name':'dfs.namenode.TransactionsAvgTime',                         'display' :'事务平均时间', 'func':_f_f2f, 'unit':'MS'},
                    {'name':'dfs.NameNode.QueuedEditsSize',                             'display' :'QueuedEditsSize'},
                    {'name':'dfs.namenode.transactionsBatchedInSync',                   'display' :'同步的事务数量'},
                    {'name':'dfs.FSNamesystem.BlockCapacity',                           'display' :'通过计算得到Block'},
                    {'name':'dfs.FSNamesystem.BlocksTotal',                             'display' :'总的块数量'},
                    {'name':'dfs.FSNamesystem.CapacityRemainingGB',                     'display' :'可用空间', 'func':_f_space},
                    {'name':'dfs.FSNamesystem.CapacityTotalGB',                         'display' :'总存储量', 'func':_f_space},
                    {'name':'dfs.FSNamesystem.CapacityUsedGB',                          'display' :'总使用量', 'func':_f_space},
                    {'name':'dfs.FSNamesystem.CorruptBlocks',                           'display' :'损坏的块数'},
                    {'name':'dfs.FSNamesystem.ExcessBlocks',                            'display' :'过量块数'},
                    {'name':'dfs.FSNamesystem.ExpiredHeartbeats',                       'display' :'超时心跳数'},
                    {'name':'dfs.FSNamesystem.FilesTotal',                              'display' :'总inode数'},
                    {'name':'dfs.FSNamesystem.MissingBlocks',                           'display' :'丢失块数'},
                    {'name':'dfs.FSNamesystem.PendingDataNodeMessageCount',             'display' :'待发送命令数'},
                    {'name':'dfs.FSNamesystem.PendingDeletionBlocks',                   'display' :'待删除块数'},
                    {'name':'dfs.FSNamesystem.PendingReplicationBlocks',                'display' :'待复制块数'},
                    {'name':'dfs.FSNamesystem.TotalFiles',                              'display' :'总文件数'},
                    {'name':'dfs.FSNamesystem.UnderReplicatedBlocks',                   'display' :'小于副本数的块数'},
                    {'name':'dfs.FSNamesystem.CorruptReplicaBlocks',                    'display' :'损坏的块数'},
                    {'name':'dfs.FSNamesystem.HAState',                                 'display' :'HA的状态'},
                    {'name':'jvm.JvmMetrics.ProcessName=NameNode.MemHeapCommittedM',    'display' :'JVM申请堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=NameNode.MemHeapUsedM',         'display' :'JVM使用堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=NameNode.MemNonHeapCommittedM', 'display' :'JVM申请堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=NameNode.MemNonHeapUsedM',      'display' :'JVM使用堆内存', 'func':_f_m2mg},
                ]
                
                service_metrics = _multi_host_metrics('HDFS/NameNode', hosts, ori_host_metrics)
                inss = service['instances']['namenode']
                _ext_state(service_metrics, inss, 'active', 'standby')
                services_metrics.append(service_metrics)

            # dn
            service_name = 'datanode'
            if service_name in service['roles']:
                hosts = service['roles'][service_name]
                ori_host_metrics= [
                    {'name':'dfs.datanode.BlockReportsAvgTime', 'display':'块报告平均时间','func':_f_f2f,'unit':'MS'},
                    {'name':'dfs.datanode.BlockReportsNumOps', 'display':'块报告次数'},
                    {'name':'dfs.datanode.HeartbeatsAvgTime', 'display':'向NameNode汇报平均时间','func':_f_f2f,'unit':'MS'},
                    {'name':'dfs.datanode.HeartbeatsNumOps', 'display':'向NameNode汇报总次数'},
                    {'name':'dfs.datanode.BlocksGetLocalPathInfo', 'display':'BlocksGetLocalPathInfo'},
                    {'name':'dfs.datanode.BlocksRemoved','display':'删除块数目'},
                    {'name':'dfs.datanode.BlocksVerified','display':'块验证总次数'},
                    {'name':'dfs.datanode.BlocksWritten','display':'向硬盘写块总次数'},
                    {'name':'dfs.datanode.BytesWritten','display':'写入总字节数'},
                    {'name':'dfs.datanode.FlushNanosAvgTime','display':'文件系统Flush平均时间','func':_f_f2f,'unit':'NS'},
                    {'name':'dfs.datanode.FlushNanosNumOps','display':'文件系统Flush次数'},
                    {'name':'dfs.datanode.PacketAckRoundTripTimeNanosAvgTime','display':'包确认平均时间','func':_f_f2f,'unit':'NS'},
                    {'name':'dfs.datanode.PacketAckRoundTripTimeNanosNumOps','display':'包确认次数'},
                    {'name':'dfs.datanode.WriteBlockOpAvgTime','display':'写块平均时间','func':_f_f2f,'unit':'NS'},
                    {'name':'dfs.datanode.WriteBlockOpNumOps','display':'写块总次数'},
                    {'name':'dfs.datanode.WritesFromLocalClient','display':'写本地次数'},
                    {'name':'dfs.datanode.WritesFromRemoteClient','display':'写远程次数'},
                    {'name':'jvm.JvmMetrics.ProcessName=DataNode.MemHeapCommittedM','display':'JVM申请堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=DataNode.MemHeapUsedM','display':'JVM堆内存使用', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=DataNode.MemNonHeapCommittedM','display':'JVM提交非堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=DataNode.MemNonHeapUsedM','display':'JVM非堆内存使用', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=DataNode.ThreadsTimedWaiting','display':'ThreadsTimedWaiting', 'func':_f_m2mg},
                ]

                service_metrics = _multi_host_metrics('HDFS/DataNode', hosts, ori_host_metrics)
                services_metrics.append(service_metrics)

        # yarn
        service = _service(u'yarn', services)
        if service:
            # rm
            service_name = 'resourcemanager'
            if service_name in service['roles']:
                hosts = service['roles'][service_name]
                ori_host_metrics = [
                    {'name':'yarn.ClusterMetrics.NumActiveNMs',                                'display' :'活跃的NodeManager'},
                    {'name':'yarn.ClusterMetrics.NumLostNMs',                                  'display' :'丢失的NodeManager'},
                    {'name':'yarn.QueueMetrics.Queue=root.AvailableMB',                        'display' :'可用内存', 'func':_f_m2mg},
                    {'name':'yarn.QueueMetrics.Queue=root.AllocatedMB',                        'display' :'分配内存', 'func':_f_m2mg},
                    {'name':'yarn.QueueMetrics.Queue=root.ActiveApplications',                 'display' :'活跃的App'},
                    {'name':'yarn.QueueMetrics.Queue=root.ActiveUsers',                        'display' :'活跃的用户'},
                    {'name':'yarn.QueueMetrics.Queue=root.AllocatedContainers',                'display' :'分配Container'},
                    {'name':'yarn.QueueMetrics.Queue=root.AppsCompleted',                      'display' :'完成的App'},
                    {'name':'yarn.QueueMetrics.Queue=root.AppsFailed',                         'display' :'失败的App'},
                    {'name':'yarn.QueueMetrics.Queue=root.AppsKilled',                         'display' :'Kill的App'},
                    {'name':'yarn.QueueMetrics.Queue=root.AppsPending',                        'display' :'挂起的APP'},
                    {'name':'yarn.QueueMetrics.Queue=root.AppsRunning',                        'display' :'运行的APP'},
                    {'name':'yarn.QueueMetrics.Queue=root.AppsSubmitted',                      'display' :'提交的APP'},
                    {'name':'yarn.QueueMetrics.Queue=root.AggregateContainersAllocated',       'display' :'总共申请的Container'},
                    {'name':'yarn.QueueMetrics.Queue=root.AggregateContainersReleased',        'display' :'总共释放的Container'},
                    {'name':'jvm.JvmMetrics.ProcessName=ResourceManager.MemHeapCommittedM',    'display' :'JVM申请堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=ResourceManager.MemHeapUsedM',         'display' :'JVM使用堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=ResourceManager.MemNonHeapCommittedM', 'display' :'JVM提交非堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=ResourceManager.MemNonHeapUsedM',      'display' :'JVM使用非堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=ResourceManager.ThreadsWaiting',       'display' :'ThreadsWaiting'},
                ]
        
                service_metrics = _multi_host_metrics('YARN/ResourceManager', hosts, ori_host_metrics)
                services_metrics.append(service_metrics)

            # nm
            service_name = 'nodemanager'
            if service_name in service['roles']:
                hosts = service['roles'][service_name]
                ori_host_metrics = [
                    {'name':'yarn.NodeManagerMetrics.AllocatedGB',                         'display' :'分配内存', 'func':_f_f2f, 'unit':'GB'},
                    {'name':'yarn.NodeManagerMetrics.AvailableGB',                         'display' :'剩下可用内存', 'func':_f_f2f, 'unit':'GB'},
                    {'name':'yarn.NodeManagerMetrics.AllocatedContainers',                 'display' :'分配Container'},
                    {'name':'yarn.NodeManagerMetrics.ContainersCompleted',                 'display' :'Container完成的数量'},
                    {'name':'yarn.NodeManagerMetrics.ContainersIniting',                   'display' :'正在Init的Container'},
                    {'name':'yarn.NodeManagerMetrics.ContainersKilled',                    'display' :'container终止的数量'},
                    {'name':'yarn.NodeManagerMetrics.ContainersLaunched',                  'display' :'登录的container数量'},
                    {'name':'yarn.NodeManagerMetrics.ContainersRunning',                   'display' :'正在运行的Container'},
                    {'name':'yarn.NodeManagerMetrics.ContainersFailed',                    'display' :'container失败的数量'},
                    {'name':'jvm.JvmMetrics.ProcessName=NodeManager.MemHeapCommittedM',    'display' :'JVM申请堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=NodeManager.MemHeapUsedM',         'display' :'JVM使用堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=NodeManager.MemNonHeapCommittedM', 'display' :'JVM提交非堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=NodeManager.MemNonHeapUsedM',      'display' :'JVM使用非堆内存', 'func':_f_m2mg},
                    {'name':'jvm.JvmMetrics.ProcessName=NodeManager.ThreadsTimedWaiting',  'display' :'ThreadsTimedWaiting'},
                    {'name':'mapred.ShuffleMetrics.ShuffleConnections',                    'display' :'Shuffle连接数'},
                    {'name':'mapred.ShuffleMetrics.ShuffleOutputBytes',                    'display' :'Shuffle输出Bytes'},
                    {'name':'mapred.ShuffleMetrics.ShuffleOutputsOK',                      'display' :'Shuffle输出成功数'},
                ]
        
                service_metrics = _multi_host_metrics('YARN/NodeManager', hosts, ori_host_metrics)
                services_metrics.append(service_metrics)
        
        
        # hive
        service = _service(u'hive', services)
        if service:
            # hivemetastore
            service_name = 'hivemetastore'
            if service_name in service['roles']:
                hosts = service['roles'][service_name]
                ori_host_metrics = [
                    {'name':'hivemetastore_memory_memHeapCommitted',    'display':'JVM申请堆内存',    'func' : _f_b2m},
                    {'name':'hivemetastore_memory_memHeapMax',          'display':'JVM最大堆内存',    'func' : _f_b2m},
                    {'name':'hivemetastore_memory_memHeapUsed',         'display':'JVM使用堆内存',    'func' : _f_b2m},
                    {'name':'hivemetastore_memory_memNonHeapCommitted', 'display':'JVM提交非堆内存',    'func' : _f_b2m},
                    {'name':'hivemetastore_memory_memNonHeapMax',       'display':'JVM最大非堆内存',    'func' : _f_b2m},
                    {'name':'hivemetastore_memory_memNonHeapUsed',      'display':'JVM使用非堆内存',    'func' : _f_b2m},
                    {'name':'hivemetastore_Threading_ThreadCount',      'display':'线程数'},
                ]
        
                service_metrics = _multi_host_metrics('Hive/HiveMetaStore', hosts, ori_host_metrics)
                services_metrics.append(service_metrics)
            
            # hiveserver
            service_name = 'hiveserver'
            if 'hiveserver' in service['roles']:
                hosts = service['roles'][service_name]
            	ori_host_metrics = [
            	    {'name' : 'hiveserver_memory_memHeapCommitted',       'display' : 'JVM申请堆内存',      'func' : _f_b2m},
            	    {'name' : 'hiveserver_memory_memHeapMax',             'display' : 'JVM最大堆内存',      'func' : _f_b2m},
            	    {'name' : 'hiveserver_memory_memHeapUsed',            'display' : 'JVM使用堆内存',      'func' : _f_b2m},
            	    {'name' : 'hiveserver_memory_memNonHeapCommitted',    'display' : 'JVM提交非堆内存',    'func' : _f_b2m},
            	    {'name' : 'hiveserver_memory_memNonHeapMax',          'display' : 'JVM最大非堆内存',    'func' : _f_b2m},
            	    {'name' : 'hiveserver_memory_memNonHeapUsed',         'display' : 'JVM使用非堆内存',    'func' : _f_b2m},
            	    {'name' : 'hiveserver_Threading_ThreadCount',         'display' : '线程数'},
            	]
        
            	service_metrics = _multi_host_metrics('Hive/HiveServer', hosts, ori_host_metrics)
            	services_metrics.append(service_metrics)
        
        # hbase
        service = _service(u'hbase', services)
        if service:
            # hbasemaster
            service_name = 'hbasemaster'
            if service_name in service['roles']:
                hosts = service['roles'][service_name]
                ori_host_metrics = [
                    {'name':'hbasemaster_master_cluster_requests',    'display':'当前机器整体request的个数'},
                    {'name':'hbasemaster_master_splitSizeAvgTime',    'display':'splitSizeAvgTime','unit':'MS'},
                    {'name':'hbasemaster_master_splitSizeMaxTime',    'display':'splitSizeMaxTime','unit':'MS'},
                    {'name':'hbasemaster_master_splitSizeMinTime',    'display':'splitSizeMinTime','unit':'MS'},
                    {'name':'hbasemaster_master_splitSizeNumOps',     'display':'splitlog次数'},
                    {'name':'hbasemaster_master_splitTimeAvgTime',    'display':'splitlog的时间平均值','unit':'MS'},
                    {'name':'hbasemaster_master_splitTimeMaxTime',    'display':'splitlog的时间最大值','unit':'MS'},
                    {'name':'hbasemaster_master_splitTimeMinTime',    'display':'splitlog的时间最小值','unit':'MS'},
                    {'name':'hbasemaster_master_splitTimeNumOps',     'display':'splitlog的次数'},
                    {'name':'hbasemaster_memory_memHeapMax',          'display':'JVM最大堆内存',  'func' : _f_b2m},
                    {'name':'hbasemaster_memory_memHeapCommitted',    'display':'JVM申请堆内存',  'func' : _f_b2m},
                    {'name':'hbasemaster_memory_memHeapUsed',         'display':'JVM使用堆内存',  'func' : _f_b2m},
                    {'name':'hbasemaster_memory_memNonHeapMax',       'display':'JVM最大非堆内存',  'func' : _f_b2m},
                    {'name':'hbasemaster_memory_memNonHeapUsed',      'display':'JVM使用非堆内存',  'func' : _f_b2m},
                    {'name':'hbasemaster_memory_memNonHeapCommitted', 'display':'JVM提交非堆内存',  'func' : _f_b2m},
                    {'name':'hbasemaster_Threading_ThreadCount',      'display':'线程数量'},
                ]
                
                service_metrics = _multi_host_metrics('HBase/HBaseMaster', hosts, ori_host_metrics)
                inss = service['instances']['hbasemaster']
                _ext_state(service_metrics, inss, 'active', 'standby')
                services_metrics.append(service_metrics)
            
            # regionserver
            service_name = 'regionserver'
            if service_name in service['roles']:
                hosts = service['roles'][service_name]
                ori_host_metrics = [
                    {'name':'regionserver_rs_blockCacheHitRatio',        'display':'BlockCache命中比例'},
                    {'name':'regionserver_rs_blockCacheSize',            'display':'BlockCache大小',  'func' : _f_b2m},
                    {'name':'regionserver_rs_compactionQueueSize',       'display':'Compaction Queue的大小'},
                    {'name':'regionserver_rs_flushQueueSize',            'display':'flush Queue的大小'},
                    {'name':'regionserver_rs_memstoreSizeMB',            'display':'memstore大小'},
                    {'name':'regionserver_rs_readRequestsCount',         'display':'读请求的数量'},
                    {'name':'regionserver_rs_regions',                   'display':'Region的个数'},
                    {'name':'regionserver_rs_requests',                  'display':'请求的数量'},
                    {'name':'regionserver_rs_storefiles',                'display':'所有的Storefiles的个数'},
                    {'name':'regionserver_rs_stores',                    'display':'Store的个数'},
                    {'name':'regionserver_rs_blockCacheFree',            'display':'BlockCache中空闲的内存大小',  'func' : _f_b2m},
                    {'name':'regionserver_rs_blockCacheCount',           'display':'BlockCache中缓存的block个数'},
                    {'name':'regionserver_rs_blockCacheHitCachingRatio', 'display':'cacheblock的cache比率'},
                    {'name':'regionserver_rs_writeRequestsCount',        'display':'写请求的数量'},
                    {'name':'regionserver_rs_compactionSizeAvgTime',     'display':'平均执行一次Compaction的数据大小',  'func' : _f_b2m},
                    {'name':'regionserver_rs_compactionSizeNumOps',      'display':'执行compaction的次数'},
                    {'name':'regionserver_rs_compactionTimeAvgTime',     'display':'平均执行一次Compaction的时间', 'unit':'S'},
                    {'name':'regionserver_rs_compactionTimeNumOps',      'display':'执行compaction的次数'},
                    {'name':'regionserver_rs_flushSizeAvgTime',          'display':'平均执行一次flush的数据大小'},
                    {'name':'regionserver_rs_flushSizeNumOps',           'display':'执行flush的次数'},
                    {'name':'regionserver_rs_flushTimeAvgTime',          'display':'平均执行一次flush的时间',  'func' : _f_b2m},
                    {'name':'regionserver_rs_flushTimeNumOps',           'display':'执行flush的次数'},
                    {'name':'regionserver_rs_slowHLogAppendCount',       'display':'慢HLog Append数'},
                    {'name':'regionserver_memory_memHeapMax',            'display':'JVM最大堆内存',  'func' : _f_b2m},
                    {'name':'regionserver_memory_memHeapCommitted',      'display':'JVM申请堆内存',  'func' : _f_b2m},
                    {'name':'regionserver_memory_memHeapUsed',           'display':'JVM使用堆内存',  'func' : _f_b2m},
                    {'name':'regionserver_memory_memNonHeapUsed',        'display':'JVM使用非堆内存',  'func' : _f_b2m},
                    {'name':'regionserver_memory_memNonHeapCommitted',   'display':'JVM提交非堆内存',  'func' : _f_b2m},
                    {'name':'regionserver_memory_memNonHeapMax',         'display':'JVM最大非堆内存',  'func' : _f_b2m},
                    {'name':'regionserver_Threading_ThreadCount',        'display':'线程数'},
                ]
                
                service_metrics = _multi_host_metrics('HBase/Regionserver', hosts, ori_host_metrics)
                services_metrics.append(service_metrics)

        ret = {"data":services_metrics}
        self.ret("ok", "", ret);


    # services overview
    def services_metrics(self):
        # [{name:, roles:{role:[instance]}}]
        services         = self._query_active_services()
        services_metrics = copy.deepcopy(static_config.services_metrics)
        cluster_name     = self._query_var('all', 'cluster_name')
        cluster_name     = self._sure_str(cluster_name)
    
        rrd_wrapper = RrdWrapper(config.ganglia_rrd_dir, config.rrd_image_dir)

        for service in services:
            service_shows = None
            for item in services_metrics:
                if item['name'] == service['name']:
                    service_shows = item['show']
            if  service_shows is None: continue

            for show in service_shows:
                hosts = service['roles'][show['role']]
                if show['type'] == 'instance-status':
                    instance_status =  []
                    #找到实体
                    metric = show['metric']
                    metric = self._sure_str(metric)
                    for host in hosts:
                        host = self._sure_str(host)
                        (ts, value) = (None, None)
                        try:
                            (ts, value) = rrd_wrapper.query_last(metric, hostname=host, clusterName=cluster_name)
                        except:
                            app_log.exception('')
                        if value is None: continue
                        instance_status.append([host,value])
                    if instance_status:
                        show['instance-status'] = instance_status
                    else:
                        show.clear()
                    continue

                if show['type'] == 'list':
                    show['list'] =  []
                    metrics = []
                    if 'metric-groups' in show:
                        for group in show['metric-groups']:
                            metrics.extend(static_config.monitor_show_info['metrics'][group])
                    for metric in metrics:
                        metric_name = self._sure_str(metric['name'])
                        for host in hosts: 
                            host = self._sure_str(host)
                            (ts, value) = (None, None)
                            try:
                                (ts, value) = rrd_wrapper.query_last(metric_name, hostname=host, clusterName=cluster_name)
                            except:
                                app_log.exception('')
                            if value is None: continue
                            show['list'].append([metric, value])
                            break
                    if not show['list']:
                        show.clear()
                    continue
            
            # 清理空值
            for i in range(len(service_shows) - 1, -1, -1):
                if not service_shows[i]:
                    service_shows.pop(i)

        # 清理空值
        for i in range(len(services_metrics) - 1, -1, -1):
            if not services_metrics[i]['show']:
                services_metrics.pop(i)
        
        ret = {"data":services_metrics}
        self.ret("ok", "", ret);

    # 获取所有的机器
    # 仅获取部署了gmond的机器
    # return [host]
    def _host_list(self):
        session = database.getSession()
	try:
            #hosts = session.query(Host)
            #temp = [host.hostname for host in hosts]
            hosts = session.query(Instance).filter(and_(Instance.role=='gmond'))
            temp = [host.host for host in hosts]
	finally:
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
        
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        rrd_wrapper  = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)

        sec = int(precision[1:])
        start = "-%ds" % sec
        end = "now" 

        data = []
        
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
        group_names  = self.get_arguments("groups")
        precision    = self.get_argument("precision")
        host         = self.get_argument("host")
        precision    = self._sure_str(precision)
        host         = self._sure_str(host)
        
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        rrd_wrapper     = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)

        sec = int(precision[1:])
        start = "-%ds" % sec
        end = "now" 

        data = []
       
        metrics = [] 
        try:
            metrics = rrd_wrapper.get_all_rrd_names(clusterName=cluster_name)
        except:
            app_log.exception('')
        
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
    
    # 显示单机的主要指标
    def show_host_main_metrics(self):
        precision    = self.get_argument("precision")
        host         = self.get_argument("host")

        precision    = self._sure_str(precision)
        host         = self._sure_str(host)
        
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        rrd_wrapper  = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)

        sec = int(precision[1:])
        start = "-%ds" % sec
        end = "now" 

      
        # 负载 3个 # CPU 3个 # 网络 # 磁盘 # 内存
        load_metric = {'metric':'负载','x':[],'series':[]}
        cpu_metric  = {'metric':'CPU', 'x':[],'series':[]}
        mem_metric  = {'metric':'内存','x':[],'series':[]}
        net_metric  = {'metric':'网络','x':[],'series':[]}
        disk_metric = {'metric':'磁盘','x':[],'series':[]}
      
        line_area_style = {'itemStyle':{'normal': {'areaStyle': {'type': 'default'}}}}
        line_stack_style ={'stack':'total'}

        def _fetch_m(metric, metrics, style=None):
            (x,ys) = self._fetch_host_metrics(rrd_wrapper, cluster_name, host, metrics, start, end)
            metric['x'] = x
            for m,y in zip(metrics,ys):
                item = {'name':m, 'type':'line', 'data':y}
                if style: item.update(style)
                metric['series'].append(item) 
            
        # 负载
        metrics = ['load_one', 'load_five', 'load_fifteen', 'proc_run', 'cpu_num']
        _fetch_m(load_metric, metrics, line_area_style)
        item = load_metric['series'][len(metrics)-1]
        del item['itemStyle']
       
        # CPU 
        metrics = ['cpu_user','cpu_system','cpu_wio']
        _fetch_m(cpu_metric, metrics, line_stack_style)

        # Mem
        metrics = ['mem_total', 'mem_free', 'swap_total', 'swap_free']
        (x,ys) = self._fetch_host_metrics(rrd_wrapper, cluster_name, host, metrics, start, end)
        mem_metric['x'] = x
        def _my_sub(a, b):
            a = self._none_2_0(a)
            b = self._none_2_0(b)
            a = int(a/1024)
            b = int(b/1024)
            return a - b  
        mem_used  = map(_my_sub, ys[0], ys[1]) 
        mem_free  = map(lambda x: int(self._none_2_0(x)/1024), ys[1])
        swap_used = map(_my_sub, ys[2], ys[3])
        
        mem_metric['series'].append({'name':'mem_used',  'type':'line', 'stack':'total', 'data':mem_used}) 
        mem_metric['series'].append({'name':'mem_free',  'type':'line', 'stack':'total', 'data':mem_free}) 
        mem_metric['series'].append({'name':'swap_used', 'type':'line', 'stack':'total', 'data':swap_used})
        for temp in mem_metric['series']: temp.update(line_area_style)

        # Net
        metrics = ['bytes_in', 'bytes_out']
        _fetch_m(net_metric, metrics, line_area_style)
        
        # Disk
        metrics = ['disk_total','disk_free']
        (x,ys) = self._fetch_host_metrics(rrd_wrapper, cluster_name, host, metrics, start, end)
        disk_metric['x'] = x
        disk_total = map(lambda x:self._none_2_0(x), ys[0])
        disk_free  = map(lambda x:self._none_2_0(x), ys[1])
        disk_used = []
        if disk_total is not None and disk_free is not None:
            disk_used  = map(lambda x,y:x is not None and y is not None and x-y or None, disk_total, disk_free)
        disk_metric['series'].append({'name':'disk_used',  'type':'line', 'stack':'total', 'data':disk_used}) 
        disk_metric['series'].append({'name':'disk_free',  'type':'line', 'stack':'total', 'data':disk_free}) 
        for temp in disk_metric['series']: temp.update(line_area_style)

        data = []
        data.append(load_metric)
        data.append(cpu_metric )
        data.append(mem_metric )
        data.append(net_metric )
        data.append(disk_metric)

        ret = {"data":data}

        self.ret("ok", "", ret);

    def _fetch_host_metrics(self, rrd_wrapper, cluster_name, host, metrics, start, end):
        """获取同一个机器上的多个指标。获取后根据时间合并
        @return (x, ys) 
        """
        
        ts = []
        values = []
        for metric in metrics:
            try:
                rrd_metric = rrd_wrapper.query(metric, start, end, hostname=host, clusterName=cluster_name)
                (x,y) = rrd.convert_to_xy(rrd_metric)
                if x is not None: ts = x
                values.append(y)
            except Exception, e:
                app_log.exception('')
                values.append([])
        
        return (ts, values)

    # None: 未获取
    def _fetch_host_last_metric(self, rrd_wrapper, cluster_name, host, metric):
        host   = self._sure_str(host)
        metric = self._sure_str(metric)
        (ts, value) = (None, None)
        try:
            (ts, value) = rrd_wrapper.query_last(metric, hostname=host, clusterName=cluster_name)
        except:
            pass
        return value
    
    # 计算表达式
    # -1: 未获取
    def _eval_rrd_expression(self, rrd_wrapper, cluster_name, host, expression):
        # total - free = use
        # use - buffer - cached
        # expression = "(mem_total - mem_free - mem_cached - mem_buffers)*100/mem_total" 
        p = re.compile(r'[a-zA-Z_][\w\.]*')
        expr_vars = p.findall(expression)
        # metrics = ['mem_total','mem_free','mem_cached','mem_buffers']
        i = 0;
        for metric in expr_vars:
            value = self._fetch_host_last_metric(rrd_wrapper,cluster_name, host, metric)
            if value is None: return -1
            # 为了变量安全，进行替换
            new_var = 'loc_pvar_%d' % i
            expression = re.sub(r'\b%s\b'%metric.replace('.',r'\.'), new_var, expression)
            locals()[new_var] = value
            i += 1
        value = eval(expression)
        return value
    
    # 指定机器的当前健康度
    def _host_current_health(self, rrd_wrapper, cluster_name, host):
        host_load_percent = self._eval_rrd_expression(rrd_wrapper, cluster_name, host, static_config.host_load_percent_expression)
        if host_load_percent < 0: return -1
        host_mem_percent = self._eval_rrd_expression(rrd_wrapper, cluster_name, host, static_config.host_mem_percent_expression)
        if host_mem_percent < 0: return -1
        host_net_percent = self._eval_rrd_expression(rrd_wrapper, cluster_name, host, static_config.host_net_percent_expression)
        if host_net_percent < 0: return -1
        host_disk_percent = self._eval_rrd_expression(rrd_wrapper, cluster_name, host, static_config.host_disk_percent_expression)
        if host_disk_percent < 0: return -1

        health = 100
        if host_disk_percent > 80:
            health -= 20 
        if host_net_percent > 80:
            health -= 20 
        if host_mem_percent > 80:
            health -= 20 
        if host_load_percent > 80:
            health -= 20

        if health < 0: health = 0
        return health
   
    # 服务单实例的健康度
    # 服务健康度：进程，端口，响应，性能
    def _service_instance_current_health(self, rrd_wrapper, cluster_name, service, role, host):
        session = database.getSession()
        for instance in session.query(Instance).filter(and_(Instance.service==service, Instance.role==role,
            Instance.host==host)):
            if instance.status != 'start':
                return 100
            if instance.health == Instance.HEALTH_HEALTHY:
                return 100
            if instance.health == Instance.HEALTH_UNKNOW:
                return -1
        return 0

    # 当前的监控指标
    # healths:[{type:,name:,display:,value:,
    #   x:[],y:[],
    #   group:[{name:,display:,value:,x:[],y:[]}]}]
    def fetch_current_healths(self):
        data = []
        
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        rrd_wrapper  = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)

        # host
        host_healths = {'type':'single','name':'host','display':'机器健康度'}
        hosts = self._host_list()
        
        y = []
        for host in hosts:
            y.append(self._host_current_health(rrd_wrapper, cluster_name, host))
        health = int(reduce(lambda x,y:x+y,y,0)/len(y))
        host_healths['value'] = health
        host_healths['x']     = hosts
        host_healths['y']     = y
       
        data.append(host_healths)

        # Service
        # [{name:, roles:{role:[instance]}}]
        services         = self._query_active_services()
        services_healths =  {'type':'multi', 'name':'service','display':'服务健康度', 'group':[]}
        for service in services:
            # group
            service_health = {'name':service['name'], 'display':service['name'],'roles':[]}
            service_health_value = 100 # 各个角色的乘积
            for role, hosts in service['roles'].items():
                role_health = {'name':role, 'display':role}
                y = []
                for host in hosts:
                    ins_health = self._service_instance_current_health(rrd_wrapper, cluster_name, service['name'], role, host)
                    if(ins_health < 0): ins_health = 0
                    y.append(ins_health)
                role_health['x'] = hosts
                role_health['y'] = y
                role_health_value = int(reduce(lambda x,y:x+y,y,0)/len(y)) # 平均值
                service_health_value *= role_health_value/100.0
                service_health['roles'].append(role_health)
            service_health['value'] = int(service_health_value)
            services_healths['group'].append(service_health)
       
        data.append(services_healths)
      
        # 作业健康度 : 最近失败比率
        # {'name':'yarn.QueueMetrics.Queue=root.AppsFailed',                         'display' :'失败的App'},
        # {'name':'yarn.QueueMetrics.Queue=root.AppsCompleted',                      'display' :'完成的App'},
        # {'name':'yarn.QueueMetrics.Queue=root.AppsRunning',                        'display' :'运行的APP'},
        # {'name':'yarn.QueueMetrics.Queue=root.AvailableMB',                        'display' :'可用内存MB'},
        # {'name':'yarn.QueueMetrics.Queue=root.AllocatedMB',                        'display' :'分配内存MB'},
        jobs_healths =  {'type':'multi', 'name':'job','display':'作业健康度', 'group':[]}
        rm_service = None
        for service in services:
            if u'yarn' == service['name']:
                rm_service = service
                break
        if rm_service: 
            hosts = service['roles']['resourcemanager']
            if hosts:
                host = hosts[0]
                apps_failed    = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'yarn.QueueMetrics.Queue=root.AppsFailed')
                apps_completed = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'yarn.QueueMetrics.Queue=root.AppsCompleted')
                apps_running   = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'yarn.QueueMetrics.Queue=root.AppsRunning')
                allocated_mb   = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'yarn.QueueMetrics.Queue=root.AllocatedMB')
                available_mb   = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'yarn.QueueMetrics.Queue=root.AvailableMB')

                if apps_failed is None: apps_failed = 0
                jobs_healths['group'].append({'name':'','display':'作业失败数',"value":"%.2f" % apps_failed})
                if apps_completed is None: apps_completed = 0
                jobs_healths['group'].append({'name':'','display':'作业完成数',"value":"%.2f" % apps_completed})
                if apps_running is None: apps_running = 0
                jobs_healths['group'].append({'name':'','display':'作业运行数',"value": "%.2f" % apps_running})
                if allocated_mb is not None:
                    allocated_mb = allocated_mb / 1024.0
                    jobs_healths['group'].append({'name':'','display':'分配内存',"value":"%.2fG" % allocated_mb})
                if available_mb is not None:
                    available_mb = available_mb / 1024.0
                    jobs_healths['group'].append({'name':'','display':'可用内存',"value":"%.2fG" % available_mb})
        
        data.append(jobs_healths)

        ret = {"data":data}
        self.ret("ok", "", ret);

    # 计算表达式，指定时间的一组值: 机器的合成指标
    # @return: [(ts,value)]
    # None: 未获取
    def _eval_host_rrd_history_expression(self, rrd_wrapper, cluster_name, host, start, end, expression):
        # total - free = use
        # use - buffer - cached
        # expression = "(mem_total - mem_free - mem_cached - mem_buffers)*100/mem_total" 
        p = re.compile(r'[a-zA-Z_][\w\.]*')
        # ['mem_total','mem_free','mem_cached','mem_buffers']
        expr_vars = p.findall(expression)
       
        data = {} # {ts:{metric:value}}

        i = 0;
        for metric in expr_vars:
            try:
                rrd_metric = rrd_wrapper.query(metric, start, end, hostname=host, clusterName=cluster_name)
            except:
                app_log.exception('')
                return None
            x,y = rrd.convert_to_xy(rrd_metric)
           
            for ts,value in zip(x,y):
                if ts not in data:
                    data[ts] = {}
                data[ts][metric] = value

            # 变量替换 
            new_var = 'loc_pvar_%d' % i
            expression = re.sub(r'\b%s\b'%metric.replace('.',r'\.'), new_var, expression)
            i += 1

        #app_log.debug(data)

        ts = data.keys()
        ts = sorted(ts)
        
        retu = []
        for t in ts:
            i = 0;
            for metric in expr_vars:
                # 重新赋值
                if metric not in data[t]: break
                value = data[t][metric]
                if value is None: break
                # 为了变量安全，进行替换
                new_var = 'loc_pvar_%d' % i
                locals()[new_var] = value
                i += 1
            value = None 
            if i == len(expr_vars):
                value = eval(expression)
            retu.append((t,value))
        return retu
    
    # 指定机器的当前健康度
    # @return: [(ts,value)]
    def _host_history_health(self, rrd_wrapper, cluster_name, host, start, end):
        host_load_percents = self._eval_host_rrd_history_expression(rrd_wrapper, cluster_name, host, start, end, static_config.host_load_percent_expression)
        #app_log.debug("host_load_percents")
        #app_log.debug(host_load_percents)
        if host_load_percents is None: return None 
        host_mem_percents = self._eval_host_rrd_history_expression(rrd_wrapper, cluster_name, host, start, end, static_config.host_mem_percent_expression)
        #app_log.debug("host_mem_percents")
        #app_log.debug(host_mem_percents)
        if host_mem_percents is None: return None 
        host_net_percents = self._eval_host_rrd_history_expression(rrd_wrapper, cluster_name, host, start, end, static_config.host_net_percent_expression)
        #app_log.debug("host_net_percents")
        #app_log.debug(host_net_percents)
        if host_net_percents is None: return None 
        host_disk_percents = self._eval_host_rrd_history_expression(rrd_wrapper, cluster_name, host, start, end, static_config.host_disk_percent_expression)
        #app_log.debug("host_disk_percents")
        #app_log.debug(host_disk_percents)
        if host_disk_percents is None: return None

        retu = []
        ilen = min(map(len,[host_load_percents,host_disk_percents,host_net_percents,host_mem_percents]))
        for i in xrange(ilen): 
            ts = host_load_percents[i][0]
           
            host_load_percent=host_load_percents[i][1]
            host_disk_percent=host_disk_percents[i][1]
            host_net_percent=host_net_percents[i][1]
            host_mem_percent=host_mem_percents[i][1]

            health = 100
            if host_disk_percent > 80:
                health -= 20 
            if host_net_percent > 80:
                health -= 20 
            if host_mem_percent > 80:
                health -= 20 
            if host_load_percent > 80:
                health -= 20

            if health < 0: health = 0
            retu.append((ts, health))
        
        return retu

    # 历史的健康指标
    # healths:[{type:,metric:,x:[],y:[],
    #   group:[{name:,display:,value:,x:[],y:[]}]}]
    def fetch_history_healths(self):
        precision = self.get_argument("precision")
        precision = self._sure_str(precision)
        
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        rrd_wrapper  = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)
        
        sec = int(precision[1:])
        start = "-%ds" % sec
        end = "now" 
        
        data = []

        # host
        host_healths = {'type':'single','metric':'机器健康度历史'}
        
        # 计算需要: 时间范围，机器，表达式
        hosts = self._host_list()
        
        healths = [] # [[(ts,health)]]
        for host in hosts:
            #app_log.debug(host)
            host = self._sure_str(host)
            health = self._host_history_health(rrd_wrapper, cluster_name, host, start, end)
            #app_log.debug(health)
            if health is None: continue
            healths.append(health)
        
        x = []
        y = []
        if healths:
            jlen = min(map(len,healths)) 
            for j in xrange(jlen): # for ts
                x.append(healths[0][j][0])
                health = int(reduce(lambda xx,yy:xx+yy[j][1],healths,0)/len(healths))
                y.append(health)
        
        host_healths['x'] = x 
        host_healths['y'] = y
        
        data.append(host_healths)

        ret = {"data":data}
        self.ret("ok", "", ret);

    # 获取最新报警列表数据
    def query_alarms(self):
        search  = self.get_argument("search", "")
        orderby = self.get_argument("orderby", "id")
        dir     = self.get_argument("dir", "desc")
        offset  = self.get_argument("offset", "0")
        limit   = self.get_argument("limit", "50")
        offset  = int(offset)
        limit   = int(limit)

        session = database.getSession()
        try:
            columns = []
            columns = [col.name for col in AlarmList.__table__.columns]
            data    = []

            query = session.query(AlarmList)
            if search:
                search = '%' + search + '%'
                qf = None 
                for col in columns:
                    qf = qf | Task.__dict__[col].like(search)
                query = query.filter(qf)
            total = query.count()

            if dir == "asc":
                query = query.order_by(asc(orderby))[offset:offset+limit]
            else:
                query = query.order_by(desc(orderby))[offset:offset+limit]
                
            for record in query:
                temp = []
                for col in columns:
                    v = getattr(record, col)
                    # 特别的，时间转化
                    if col == 'ctime':
                        t = time.localtime(int(v))
                        v = time.strftime("%Y-%m-%d %H:%M:%S", t)
                    temp.append(v)
                data.append(temp)

            # alarms
            alarms = {'columns':columns, 'rows':data, 'total': total, 'totalPage':int(total/limit)+1}
            self.ret("ok", "", {"data": alarms})
        finally:
            session.close()
   
    # 根据条件查询报警列表数据
    def fetch_last_alarm_list(self):
        session = database.getSession()
        try:
            query = session.query(AlarmList).order_by(desc(AlarmList.id)).limit(100)
            columns = []
            columns = [col.name for col in AlarmList.__table__.columns]
            data = []
            for record in query:
                temp = []
                for col in columns:
                    v = getattr(record,col)
                    # 特别的，时间转化
                    if col == 'ctime':
                        t = time.localtime(v)
                        v = time.strftime("%Y-%m-%d %H:%M:%S", t)
                    temp.append(v)
                data.append(temp);
            alarms = {'columns':columns, 'rows':data}
            self.ret("ok", "", {"data": alarms})
        finally:
            session.close()
   
    def _none_2_0(self, v):
        if v is None: return 0
        return v

    # 监控 机器 概览 当前 
    # data:[{name,x:[],series:[{name:,type:,data:[]}]}]
    def fetch_host_current_overview(self):

        host_overview = [] #机器概述
        data = [] # 分项数据
        
        cluster_name = self._query_var('all', 'cluster_name')
        cluster_name = self._sure_str(cluster_name)
        rrd_wrapper  = RrdWrapper(config.ganglia_rrd_dir , config.rrd_image_dir)

        # hosts: [host]
        hosts = self._host_list()

        # 机器概览
        total_hosts         = len(hosts)
        total_disk_numb     = 0
        total_disk_capacity = 0
        total_disk_used     = 0
        total_mem_capacity  = 0
        total_mem_used      = 0
        total_cpu_numb      = 0
        total_net_in        = 0
        total_net_out       = 0
        
        # 负载 load_one                       : proc_run                        : cpu_num
        # CPU  cpu_user                       : cpu_system                      : cpu_wio
        # 网络 bytes_in                       : bytes_out                       : 1G        : 2G
        # 内存 mem used(mem_total-mem_free)   : swap used(swap_total-swap_free) : mem_free
        # 存储 disk_use(disk_total-disk_free) : disk_free
        # 存储扩展 [ { name:hadoop1磁盘, x:[sda1,sdb1], series:[{ name:disk_used, type:bar, stack:disk, data:[1,2] }
        #                                                       { name:disk_free, type:bar, stack:disk, data:[2,1] }] } ]
        load_metric = {'metric':'负载','x':hosts,'series':[]}
        cpu_metric  = {'metric':'CPU', 'x':hosts,'series':[]}
        net_metric  = {'metric':'网络','x':hosts,'series':[]}
        mem_metric  = {'metric':'内存','x':hosts,'series':[]}
        disk_metric = {'metric':'磁盘','x':hosts,'series':[]}
        # 负载分布
        # {metric:,type:,data:[{value:,name:''}]}
        load_metric_dist = {'metric':'负载分布','series':[{'name':'负载分布','type':'pie','data':[]}]}

        load_metric_load_one     = []
        load_metric_load_five    = []
        load_metric_load_fifteen = []
        load_metric_proc_run     = []
        load_metric_cpu_num      = []
        cpu_metric_cpu_user      = []
        cpu_metric_cpu_system    = []
        cpu_metric_cpu_wio       = []
        net_metric_bytes_in      = []
        net_metric_bytes_out     = []
        net_metric_1g_mark       = []
        net_metric_2g_mark       = []
        mem_metric_mem_used      = []
        mem_metric_mem_free      = []
        mem_metric_swap_used     = []
        disk_metric_disk_used    = []
        disk_metric_disk_free    = []
        # 负载分布 百分比
        load_metric_load_percent = []

        for host in hosts:
            host = self._sure_str(host)
            load_one     = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'load_one')
            load_five    = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'load_five')
            load_fifteen = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'load_fifteen')
            proc_run     = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'proc_run')
            cpu_num      = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'cpu_num')
            cpu_user     = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'cpu_user')
            cpu_system   = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'cpu_system')
            cpu_wio      = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'cpu_wio')
            bytes_in     = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'bytes_in')
            bytes_out    = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'bytes_out')
            mem_total    = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'mem_total')
            mem_free     = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'mem_free')
            swap_total   = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'swap_total')
            swap_free    = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'swap_free')
            disk_total   = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'disk_total')
            disk_free    = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'disk_free')
            
            # 负载
            load_metric_load_one.append(load_one)
            load_metric_load_five.append(load_five)
            load_metric_load_fifteen.append(load_fifteen)
            load_metric_proc_run.append(proc_run)
            load_metric_cpu_num.append(cpu_num)
            load_percent = None
            if load_one is not None and cpu_num is not None:
                load_percent = int((load_one / cpu_num) * 100)
            load_metric_load_percent.append(load_percent)
          
            # overview
            total_cpu_numb += self._none_2_0(cpu_num)

            # CPU
            cpu_metric_cpu_user.append(cpu_user)
            cpu_metric_cpu_system.append(cpu_system)
            cpu_metric_cpu_wio.append(cpu_wio)

            # 网络
            if bytes_in  is not None: bytes_in  = int(bytes_in)/1024
            if bytes_out is not None: bytes_out = int(bytes_out)/1024
            net_metric_bytes_in.append(bytes_in)
            net_metric_bytes_out.append(bytes_out)
            net_metric_1g_mark.append(128*1024)
            net_metric_2g_mark.append(256*1024)
            
            # overview
            total_net_in  += self._none_2_0(bytes_in)
            total_net_out += self._none_2_0(bytes_out)

            # 内存
            if mem_total is not None: mem_total = int(mem_total)/1024
            if mem_free  is not None: mem_free  = int(mem_free)/1024
            mem_used = None
            if mem_total is not None and mem_free is not None:
                mem_used = mem_total - mem_free
            mem_metric_mem_used.append(mem_used)
            mem_metric_mem_free.append(mem_free)
            
            # overview
            total_mem_capacity  += self._none_2_0(mem_total)
            total_mem_used      += self._none_2_0(mem_used)
            
            if swap_total is not None: swap_total = int(swap_total)/1024
            if swap_free  is not None: swap_free  = int(swap_free)/1024
            swap_used = None
            if swap_total is not None and swap_free is not None:
                swap_used = swap_total - swap_free
            mem_metric_swap_used.append(swap_used)

            # 存储
            if disk_total is not None: disk_total = int(disk_total)
            if disk_free  is not None: disk_free  = int(disk_free)
            disk_used = None
            if disk_total is not None and disk_free is not None:
                disk_used = disk_total - disk_free
            disk_metric_disk_used.append(disk_used)
            disk_metric_disk_free.append(disk_free)
            
            # overview
            total_disk_capacity += self._none_2_0(disk_total)
            total_disk_used     += self._none_2_0(disk_used)

        # 负载
        load_metric['series'].append({'name':'load_one', 'type':'bar', 'data':load_metric_load_one})
        load_metric['series'].append({'name':'load_five', 'type':'bar', 'data':load_metric_load_five})
        load_metric['series'].append({'name':'load_fifteen', 'type':'bar', 'data':load_metric_load_fifteen})
        load_metric['series'].append({'name':'proc_run', 'type':'bar', 'data':load_metric_proc_run})
        load_metric['series'].append({'name':'cpu_num', 'type':'line', 'data':load_metric_cpu_num})

        # CPU
        cpu_metric['series'].append({'name':'cpu_user', 'type':'bar', 'stack':'cpu', 'data':cpu_metric_cpu_user})
        cpu_metric['series'].append({'name':'cpu_system', 'type':'bar', 'stack':'cpu', 'data':cpu_metric_cpu_system})
        cpu_metric['series'].append({'name':'cpu_wio', 'type':'bar', 'stack':'cpu', 'data':cpu_metric_cpu_wio})

        # 网络
        net_metric['series'].append({'name':'bytes_in', 'type':'bar', 'stack':'net', 'data':net_metric_bytes_in})
        net_metric['series'].append({'name':'bytes_out', 'type':'bar', 'stack':'net', 'data':net_metric_bytes_out})
        #net_metric['series'].append({'name':'1g_mark', 'type':'line', 'data':net_metric_1g_mark})
        #net_metric['series'].append({'name':'2g_mark', 'type':'line', 'data':net_metric_2g_mark})

        # 内存
        mem_metric['series'].append({'name':'mem_used', 'type':'bar', 'stack':'mem', 'data':mem_metric_mem_used})
        mem_metric['series'].append({'name':'mem_free', 'type':'bar', 'stack':'mem', 'data':mem_metric_mem_free})
        mem_metric['series'].append({'name':'swap_used', 'type':'bar', 'stack':'mem', 'data':mem_metric_swap_used})

        # 存储
        disk_metric['series'].append({'name':'disk_used', 'type':'bar', 'stack':'disk', 'data':disk_metric_disk_used})
        disk_metric['series'].append({'name':'disk_free', 'type':'bar', 'stack':'disk', 'data':disk_metric_disk_free})
        
        # 负载分布
        # load_metric_load_percent.append(load_percent)
        load_percent_group={"Down":0,"0-25%":0,"25-50%":0,"50-75%":0,"75-100%":0,"100%+":0}
        for load_percent in load_metric_load_percent:
            if load_percent is None:
                load_percent_group['Down'] += 1
            elif load_percent <= 25:
                load_percent_group['0-25%'] += 1
            elif load_percent <= 50:
                load_percent_group['25-50%'] += 1
            elif load_percent <= 75:
                load_percent_group['50-75%'] += 1
            elif load_percent <= 100:
                load_percent_group['75-100%'] += 1
            else:
                load_percent_group['100%+'] += 1
        # 过滤0值
        for name, numb in load_percent_group.items():
            if numb <= 0:
                del load_percent_group[name]
        load_metric_dist['series'][0]['data'] = [{'name':k, 'value':v} for k,v in load_percent_group.iteritems()]

        #data.append(load_metric_dist)
        data.append(load_metric)
        data.append(cpu_metric)
        data.append(net_metric)
        data.append(mem_metric)
        data.append(disk_metric)
        
        # 存储扩展 [ { name:hadoop1磁盘, x:[sda1,sdb1], xtype:'h', series:[{ name:disk_used, type:bar, stack:disk, data:[1,2] }
        #                                                       { name:disk_free, type:bar, stack:disk, data:[2,1] }] } ]
        disk_data = []
        regex = re.compile(r'dev_(\w+)_disk_total')
        for host in hosts:
            host = self._sure_str(host)
            names = []
            try:
                names = rrd_wrapper.match_rrd_names(regex, host, cluster_name)
            except:
                pass
            if not names: continue
            
            # overview
            total_disk_numb += len(names)

            info = {'overview':'本机包含%d个磁盘' % len(names), 'disks':{}}
            disks = {'metric':'%s磁盘状况'%host,'x':[], 'xtype':'horizontal', 'series':[], 'info':info}
            disk_useds = []
            disk_frees = []
            for name in names:
                matchObj = regex.match(name)
                # sda1
                dev = matchObj.group(1)
                # sda
                dev2 = dev.rstrip('0123456789')
                #path = "/dev/%s" % dev
                disks['x'].append(dev)

                disk_used = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'dev_%s_disk_used' % dev)
                disk_total = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'dev_%s_disk_total' % dev)
                
                disk_iostat_r = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'disk_iostat_%s_rkB_s' % dev)
                disk_iostat_w = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'disk_iostat_%s_wkB_s' % dev)
                # disk_smartctl_sda_Power_On_Hours
                disk_smartctl_power_on_hours = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'disk_smartctl_%s_Power_On_Hours' % dev2)
                # disk_smartctl_sda_Seek_Error_Rate
                disk_smartctl_seek_error_rate = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'disk_smartctl_%s_Seek_Error_Rate' % dev2)
                # disk_smartctl_sda_Raw_Read_Error_Rate
                disk_smartctl_raw_read_error_rate = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'disk_smartctl_%s_Raw_Read_Error_Rate' % dev2)
                # disk_smartctl_sda_UDMA_CRC_Error_Count
                disk_smartctl_udma_crc_error_count = self._fetch_host_last_metric(rrd_wrapper, cluster_name, host, 'disk_smartctl_%s_UDMA_CRC_Error_Count' % dev2)
                 
                if disk_total is not None: disk_total = int(disk_total)
                if disk_free  is not None: disk_free  = int(disk_free)
                disk_free = None
                if disk_total is not None and disk_used is not None:
                    disk_free = disk_total - disk_used

                disk_useds.append(disk_used)
                disk_frees.append(disk_free)

                info_disk = []
                info_disk.append({'name':'读速度','value':disk_iostat_r,'unit':'KB'})
                info_disk.append({'name':'写速度','value':disk_iostat_w,'unit':'KB'})
                info_disk.append({'name':'通电时间','value':disk_smartctl_power_on_hours,'unit':'小时'})
                info_disk.append({'name':'Seek_Error_Rate','value':disk_smartctl_seek_error_rate,'unit':''})
                info_disk.append({'name':'Raw_Read_Error_Rate','value':disk_smartctl_raw_read_error_rate,'unit':''})
                info_disk.append({'name':'UDMA CRC错误','value':disk_smartctl_udma_crc_error_count,'unit':'次'})
                info['disks'][dev] = info_disk
                
            disks['series'].append({'name':'disk_used','type':'bar','stack':'disk','data':disk_useds})
            disks['series'].append({'name':'disk_free','type':'bar','stack':'disk','data':disk_frees})
            disk_data.append(disks)
        
        # overview
        host_overview.append({'name':'总机器数量','value':total_hosts,'unit':'台'})
        host_overview.append({'name':'总磁盘数量','value':total_disk_numb,'unit':'个'})
        host_overview.append({'name':'总磁盘容量','value':total_disk_capacity,'unit':'G'})
        host_overview.append({'name':'总磁盘使用','value':total_disk_used,'unit':'G'})
        host_overview.append({'name':'总内存容量','value':total_mem_capacity,'unit':'M'})
        host_overview.append({'name':'总内存使用','value':total_mem_used,'unit':'M'})
        host_overview.append({'name':'总CPU数量','value':total_cpu_numb,'unit':'个'})
        host_overview.append({'name':'总网卡流入','value':total_net_in,'unit':'M'})
        host_overview.append({'name':'总网卡流出','value':total_net_out,'unit':'M'})

        ret = {"data":data, 'diskData':disk_data, "hostOverview":host_overview, 'loadDist':load_metric_dist}
        self.ret("ok", "", ret);

    def _query_special_hosts(self, service_name, role_name):
        # [{name:, roles:{role:[instance]}}]
        services = self._query_active_services()
        for service in services:
            if service['name'] == service_name:
                for role, instances in service['roles'].iteritems():
                    if role == role_name: 
                        return instances
        return []

    def _get_rmhost(self):
        instances = self._query_special_hosts('yarn', 'resourcemanager')
        if instances: return instances[0]
        raise Exception('can not get rm host')
    
    def _get_nmhosts(self):
        return self._query_special_hosts('yarn', 'nodemanager')

    def _get_rmport(self):
        rm_port = self._query_var('all', config.collect_yarn_rm_webapp_port_varname)
        return str(rm_port)

    def app_running_state(self):
        url = "http://%s:%s/ws/v1/cluster/metrics" % (self._get_rmhost(),self._get_rmport())
        metrics = util.get_http_json(url)
        if metrics is None: metrics = {}
        self.ret("ok","",metrics)
        #retu = {'data':{'url':url, 'metrics':metrics}}
        #self.ret("ok","",retu)

    def app_running(self):
        url = "http://%s:%s/ws/v1/cluster/apps?state=RUNNING" %(self._get_rmhost(),self._get_rmport())
        runningApp = util.get_http_json(url)
        queues = {}
        if runningApp != None and runningApp.has_key("apps") and runningApp["apps"]!=None and  runningApp["apps"].has_key("app"):
            for app in runningApp["apps"]["app"]:
                queue = app["queue"]
                appid = app['id']
                if not queues.has_key(queue):
                    queues[queue] = {}
                queues[queue][appid]=app
        result={"queues":queues,"rmhost":self._get_rmhost(),"rmport":self._get_rmport()}
        self.ret("ok","",result)

    def app_waitting(self):
        url = "http://%s:%s/ws/v1/cluster/apps?state=ACCEPTED" %(self._get_rmhost(),self._get_rmport() )
        waittingApp = util.get_http_json(url)
        
        apps = []
        if waittingApp is not None:
            if waittingApp.has_key("apps") and waittingApp["apps"] != None :
                apps = waittingApp["apps"]

        result={"waitting":apps,"rmhost":self._get_rmhost(),"rmport":self._get_rmport()}
        self.ret("ok","",result) 

    def app_proxy(self):
        appid = self.get_argument("appid") 
        url = ("http://%s:%s/proxy/%s/ws/v1/mapreduce/jobs/" %(self._get_rmhost(),self._get_rmport(),appid))
        jobInfo = util.get_http_json(url)
        keyList = ["mapsTotal","mapsPending","mapsRunning","failedMapAttempts","killedMapAttempts","successfulMapAttempts",
                   "reducesTotal","reducesPending","reducesRunning","failedReduceAttempts","killedReduceAttempts","successfulReduceAttempts"]
        if jobInfo:
            result = {}
            temp = jobInfo["jobs"]["job"][0]
            result["amTime"] = temp["elapsedTime"]
            for key in keyList:
                result[key] = temp[key]
            self.ret("ok","",result)
        else:
            result = {}
            result["amTime"] ="x"
            for key in keyList:
                result[key] = "x"
            self.ret("ok","",result)

    # 作业的查询初始化信息
    def job_query_init_info(self):
        nm_hosts = self._get_nmhosts()
        result = {}
        result['data'] = {'nm_hosts':nm_hosts}
        self.ret("ok","",result)

    #for rm query
    def rm_query(self):
        fields          = self.get_arguments("fields",[])
        happenTimeMax   = self.get_argument("happenTimeMax",0)
        happenTimeMin   = self.get_argument("happenTimeMin",0)
        happenTimeSplit = self.get_argument("happenTimeSplit",600)

        sql = ""
        queryResult = []

        if fields:
            where = "" 
            if happenTimeMax != 0:
                where += " happenTime < " + str(happenTimeMax)
            if happenTimeMin != 0:
                where += " and" if where else ""
                where += " happenTime > " + str(happenTimeMin)
        
            sqlFields=""
            for field in fields:
                sqlFields = sqlFields+" , sum("+field+") as " + field
        
            sql = ("select (happenTime/%s)*%s as printTime %s from rm where %s group by printTime" % (happenTimeSplit,happenTimeSplit,sqlFields,where) )

            session = database.getSession()
            cursor  = session.execute(sql)
            for record in cursor:
                temp = []
                for value in record:
                    app_log.info(type(value))
                    if isinstance(value,Decimal):
                        app_log.info("into deci")
                        temp.append(float(value))    
                    else:
                        temp.append(value)
                queryResult.append(temp)
            app_log.info(queryResult)
        
            #特殊处理mapTime和reduceTime
            #由于前面有一个printTime的查询，所以偏移一位
            fieldOffset = 1 
            if "mapTime" in fields and "mapNum" in fields :
                timeIndex = fields.index("mapTime") + fieldOffset
                numIndex = fields.index("mapNum") + fieldOffset
                for record in queryResult:
                    if record[numIndex] != None and record[numIndex] != 0:
                        record[timeIndex] = record[timeIndex] / record[numIndex] 
        
            if "reduceTime" in fields and "reduceNum"  in fields :
                timeIndex = fields.index("reduceTime") + fieldOffset
                numIndex = fields.index("reduceNum") + fieldOffset
                for record in queryResult:
                    if record[numIndex] != None and record[numIndex] != 0:
                        record[timeIndex] = record[timeIndex] / record[numIndex]

        result = {"result":queryResult, "sql":sql}
        self.ret("ok","",result)               
                    
    #for nm query
    def nm_query(self):
        hosts           = self.get_arguments("hosts",[])
        fields          = self.get_arguments("fields",[])
        happenTimeMax   = self.get_argument("happenTimeMax",0)
        happenTimeMin   = self.get_argument("happenTimeMin",0)
        happenTimeSplit = self.get_argument("happenTimeSplit",600)
        
        sql         = ""
        queryResult = []

        if hosts and fields:
            where = "" 
            if happenTimeMax != 0:
                where += " happenTime < " + str(happenTimeMax)
            if happenTimeMin != 0:
                where += " and" if where else ""
                where += " happenTime > " + str(happenTimeMin)
            
            hostWhere = ",".join(["'%s'" % h for h in hosts])
            where += " and" if where else ""
            where += ' host in (%s)' % hostWhere
            
            sqlFields=",".join(["sum(%s) as %s" % (f, f) for f in fields])
            
            sql = ("select (happenTime/%s)*%s as printTime, host, %s from nm \
                    where %s group by printTime, host" % 
                    (happenTimeSplit, happenTimeSplit, sqlFields, where)
                  )

            session = database.getSession()
            cursor  = session.execute(sql)
            
            for record in cursor:
                temp = []
                for value in record:
                    if isinstance(value,Decimal):
                        temp.append(float(value))    
                    else:
                        temp.append(value)
                queryResult.append(temp)
                
            #特殊处理mapTime和reduceTime
            #由于前面有printTime和host两个位置，所以偏移两位
            fieldOffset = 2
            if "mapTime" in fields and "mapNum"  in fields :
                timeIndex = fields.index("mapTime") + fieldOffset
                numIndex = fields.index("mapNum") + fieldOffset
                for record in queryResult:
                    if record[numIndex] != None and record[numIndex] != 0:
                        record[timeIndex] = record[timeIndex] / record[numIndex] 
            
            if "reduceTime" in fields and "reduceNum"  in fields :
                timeIndex = fields.index("reduceTime") + fieldOffset
                numIndex = fields.index("reduceNum") + fieldOffset
                for record in queryResult:
                    if record[numIndex] != None and record[numIndex] != 0:
                        record[timeIndex] = record[timeIndex] / record[numIndex]
            
        result = {"result":queryResult,"sql":sql}
        self.ret("ok","",result)               
    
    #for app query
    def app_sum(self):
        where = self.get_argument("where","1").replace("o|o","%")
        session = database.getSession()
        sumKey=["mapsTotal","mapsCompleted","successfulMapAttempts","killedMapAttempts","failedMapAttempts",
                "localMap","rackMap",
                "reducesTotal","reducesCompleted","successfulReduceAttempts","killedReduceAttempts",
                "failedReduceAttempts",
                "fileRead","fileWrite","hdfsRead","hdfsWrite"]
        select = "count(appid) as appidCount"
        for key in sumKey:
            select = select +" , sum("+key+") as "+key+"Sum "
        sql = (("select "+select+" from app where %s ") % (where))
        app_log.info(sql)
        cursor = session.execute(sql)
        resultRecord = {}
        temp = []
        for record in cursor:
            app_log.info(record)
            for value in record:
                temp.append(value)
                app_log.info(value)
        for (key,value) in zip(cursor.keys(),temp):
            if value != None:
                resultRecord[key]=int(value)
            else:
                resultRecord[key]=0
        session.close()
        result={"resultRecord":resultRecord}
        
        self.ret("ok","",result)

    def app_list(self):
        where = self.get_argument("where","1").replace("o|o","%")
        offset = self.get_argument("offset",0)
        limit = self.get_argument("limit",50)
        orderField = self.get_argument("orderField","appid")
        orderDirection = self.get_argument("orderDirection","desc")
        session = database.getSession()
        selectKeyArray=["appid","user","name","queue","startedTime","finishedTime","state","finalStatus",
                   "attemptNumber","mapsTotal","mapsCompleted","localMap","reducesTotal","reducesCompleted",
                   "fileRead","fileWrite","hdfsRead","hdfsWrite"]
        if orderField=="appid" :
            selectKeyArray.append("CAST(SUBSTR(appid,27 ) AS SIGNED) as appnum")
            orderby = "appnum "+orderDirection
        else:
            orderby = orderField+" "+orderDirection 
        selectKey = ",".join(selectKeyArray)
        sql = ("select "+selectKey+" from app where %s order by %s LIMIT %s OFFSET %s " % (where,orderby,limit,offset))
        cursor = session.execute(sql)
        queryResult = []
        for record in cursor:
            temp = []
            for v in record:
                temp.append(v)
            queryResult.append(temp)
        #queryResult = cursor.fetchall()
        session.close()
        result={"applist":queryResult,"rmhost":self._get_rmhost(),"rmport":self._get_rmport()}
        self.ret("ok","",result)

    def kill_app(self):
        needKillAppIds = self.get_arguments("needKillAppIds")
        result={}
        for appId in needKillAppIds:
            (status, output) = shell_lib.kill_app(appId)
            result[appId]=(status, output)
        result={"data":result}
        self.ret("ok","",result)
