#!/usr/bin/env python
# coding=utf8

import json
import urllib2
import re
import logging
import os
import sys

import daemon
import lockfile
import lockfile.pidlockfile
import threadpool

commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon")
sys.path.append(commondir)

import config
import database
import util
import time
from lib.logger import log
from model.instance import Instance
from model.applicationRecord import ApplicationRecord
from model.nmRecord import NmRecord
from model.rmRecord import RmRecord
from model.metricsRecord import MetricsRecord

# 采集数据
# 获取最近10分钟完成的任务

def getIntervalTime(ts):
    if ts > 1000000000000L:
        ts /= 1000
    return (int(ts)/config.collect_interval)*config.collect_interval

#转化为10为的长度,且转化为开头的整10分钟
def getSecondTime(time):
    if time > 1000000000000L:
        time /= 1000
    return time

def jobidToAppid(jobid):
        return "application" + jobid[3:]
    
def appidToJobid(appid):
    return "job" + appid[11:]

class Collector:
    #默认运行上个10分钟的数据
    def init_all(self, recordTime):
        self.interval = config.collect_interval
        self.recordTime = recordTime
        self.rmList = {}
        self.nmList = {}
        self.appList = {} 
        self.init_config()

    def init_config(self):
        '''
        初始化关于获取端口等的内容
        默认从数据库中获取,由于可能只使用监控
        所以本函数可以直接修改为固定值
        '''
        session = database.getSession()
        insts = session.query(Instance).filter(Instance.role=="resourcemanager")
        for inst in insts:
            self.rmhost = inst.host;

        self.rmport=database.get_service_conf(session,"yarn","yarn_nm_webapp_port")
        insts = session.query(Instance).filter(Instance.role=="historyserver")
        for inst in insts:
            self.hshost = inst.host;

        self.hsport = database.get_service_conf(session,"yarn","mapreduce_jobhistory_webapp_port")

        session.close()
        #self.rmhost="hadoop5"
        #self.rmport="50088"
        #self.hshost="hadoop5"
        #self.hsport="50888"

    def collect(self, recordTime):
        try:
            log.info("begin to collect recordTime:%d" % recordTime) 
            self.init_all(recordTime)
            self.collectMetrics()
            self.collectApp()
        except:
            log.exception("collect catch exception recordTime:%d" % recordTime)

    def collectMetrics(self):
        #获取当前集群的状态
        metrics = self.getMetrics()
        #recordTime指向上个10分钟的开头时间，所以要往后移动一个10分钟
        meRecord =  MetricsRecord(self.recordTime + config.collect_interval);
        recordKey=["appsCompleted","appsPending","appsRunning",
                   "appsFailed","appsKilled",
                   "totalMB","availableMB",
                   "allocatedMB","containersAllocated",
                   "totalNodes","activeNodes"]
        #totalMB=availableMB+allocatedMB
        temp = metrics['clusterMetrics'];
        temp["totalMB"] = int(temp["availableMB"]) + int (temp["allocatedMB"])
        for key in recordKey:
            meRecord.set(key,temp[key])
        session = database.getSession()
        session.merge(meRecord)
        session.commit()
         
    def collectApp(self):
                
        #获取所有的过去时段完成的app的列表
        apps = self.getAppList()
        if not apps or not apps["apps"]:
            log.info("no appid match")
            return
        
        startCollectTime = time.time()
        #轮询app列表，获取每个app的详细信息
        for app in apps["apps"]["app"]:
            startTime = time.time()
            appid =  app["id"]
            if app['state'] == 'FINISHED':
                try:                
                    jobid = appidToJobid(appid)
                    jobHistory = self.getJobHistory(jobid)
                    if jobHistory: 
                        jobCounter = self.getJobCounter(jobid)
                        jobTasks = self.getJobAllTask(jobid)
                        self.updateWithAppid(app,jobHistory,jobCounter)
                    else:
                        log.info("find some app run success but no history file:"+appid)
                except:
                    log.exception("get error while doing app "+appid)
                endTime = time.time()
            else:
                self.updateWithNotSuccAppid(app)
                
            log.info("getting appid: %s using %d ms" % (appid, (endTime - startTime)*1000))
            
        endCollectTime = time.time()
        log.info("using %d ms to collect the data" % ((endCollectTime - startCollectTime)*1000) )
        
        startFlushTime = time.time()
        
        #提交数据
        session = database.getSession()
        for (appid,appRecordValue) in self.appList.items():
            session.merge(appRecordValue)
        session.commit()
        log.info("push %d appRecord into table" % (len(self.appList)))
        
        for (key,NmRecordValue) in self.nmList.items():
            session.merge(NmRecordValue)
        session.commit()
        log.info("push %d NmRecord into table" % (len(self.nmList)))
        
        for (key,RmRecordValue) in self.rmList.items():
            session.merge(RmRecordValue)
        session.commit()
        log.info("push %d RmRecord into table" % (len(self.rmList)))
        endFlushTime = time.time()
        
        log.info("using %d ms to push to the db" % ((endFlushTime - startFlushTime)*1000))
            
        
    def getJobHistory(self,jobid):
        url = ("http://%s:%s/ws/v1/history/mapreduce/jobs/%s" 
               % (self.hshost,self.hsport,jobid))
        return util.get_http_json(url)
    
    def getJobAllTask(self,jobid):
        url = ("http://%s:%s/ws/v1/history/mapreduce/jobs/%s/tasks"
               % (self.hshost,self.hsport,jobid))
        tasks = util.get_http_json(url)
        if not tasks or not tasks.has_key('tasks') or not tasks['tasks'].has_key('task') :
            return
        for task in tasks['tasks']['task']:
            taskId = task['id']
            url = ("http://%s:%s/ws/v1/history/mapreduce/jobs/%s/tasks/%s/attempts"
               % (self.hshost,self.hsport,jobid,taskId))
            attempts = util.get_http_json(url)
            if not attempts or not attempts.has_key('taskAttempts') \
                or not attempts['taskAttempts'].has_key('taskAttempt') :
                return
            for attempt in attempts['taskAttempts']['taskAttempt']:
                attemptId = attempt['id']
                url = ("http://%s:%s/ws/v1/history/mapreduce/jobs/%s/tasks/%s/attempts/%s/counters"
                   % (self.hshost,self.hsport,jobid,taskId,attemptId))
                attemptCounter = util.get_http_json(url)
                self.updateWithAttempt(attempt,attemptCounter)

                    
    def getNodeFromAddress(self,address):
        split = address.find(":")
        return address[0:split]
    
    def getJobCounter(self,jobid):
        """
        从appid的对应的counter的网页上截取信息.从restapi获取的不全,缺少data-local等的信息
        """
        url = ("http://%s:%s/jobhistory/jobcounters/%s" 
               % (self.hshost,self.hsport,jobid))
        html = util.get_http(url)
        if not html:
            return None
        keys = ["DATA_LOCAL_MAPS","RACK_LOCAL_MAPS",
                "FILE_BYTES_READ","FILE_BYTES_WRITTEN",
                "HDFS_BYTES_READ","HDFS_BYTES_WRITTEN"]
        counters = {}
        for key in keys:
            counters[key] = self.getCounterFromHtml(html,key)
        return counters
    
    def getCounterFromHtml(self,html,key):
        pattern = re.compile('<td title="'+key+'">.*?<td>.*?(\d+).*?<td>.*?(\d+).*?<td>.*?(\d+).*?<tr>',re.S)
        match = pattern.search(html)
        if match:
            # 使用Match获得分组信息
            return {"map":match.group(1),"reduce":match.group(2),"total": match.group(3) }
        else:
            return {"map":0,"reduce":0,"total":0}
    
    def getMetrics(self):    
        url = ("http://%s:%s/ws/v1/cluster/metrics" % (self.rmhost,self.rmport))
        return util.get_http_json(url)
    
    def getAppList(self):
        url = ("http://%s:%s/ws/v1/cluster/apps?finishedTimeBegin=%d&finishedTimeEnd=%d" 
            % (self.rmhost,self.rmport,(self.recordTime*1000),(self.recordTime+self.interval)*1000))
        return util.get_http_json(url)
        
    #以下是用于程序内计数的函数
    def updateWithAttempt(self,attempt,attemptCounter):
        #update nm's containerNum , mapNum , reduceNum
        node = self.getNodeFromAddress(attempt['nodeHttpAddress'])
        happenTime = getIntervalTime(attempt['startTime'])
        rm = self.getRm(self.recordTime,happenTime)
         
        nm = self.getNm(node,self.recordTime, happenTime)
        #*********************************
        nm.inc("containerNum",1)
        
        if attempt['type'] == 'MAP':
            rm.inc("mapNum",1)
            nm.inc("mapNum",1)
            rm.inc("mapTime",attempt['elapsedTime'])
            nm.inc("mapTime",attempt['elapsedTime'])
            if attempt['state'] != "SUCCEEDED":
                rm.inc("failMap",1)
                nm.inc("failMap",1)
        elif attempt['type'] == 'REDUCE':
            rm.inc("reduceNum",1)
            nm.inc("reduceNum",1)
            rm.inc("reduceTime",attempt['elapsedTime'])
            nm.inc("reduceTime",attempt['elapsedTime'])
            if attempt['state'] != "SUCCEEDED":
                rm.inc("failReduce",1)
                nm.inc("failReduce",1)
        #*********************************
        if not attemptCounter or not attemptCounter.has_key('jobTaskAttemptCounters') \
            or not attemptCounter['jobTaskAttemptCounters'].has_key('taskAttemptCounterGroup'):
            return 
        for taskAttemptCounterGroup in attemptCounter['jobTaskAttemptCounters']['taskAttemptCounterGroup']:
            if taskAttemptCounterGroup['counterGroupName'] == "org.apache.hadoop.mapreduce.FileSystemCounter":
                for counter in taskAttemptCounterGroup['counter']:
                    if counter['name'] == 'FILE_BYTES_READ':
                        rm.inc("fileRead",counter["value"])
                        nm.inc("fileRead",counter["value"])
                    elif counter['name'] == 'FILE_BYTES_WRITTEN':
                        rm.inc("fileWrite",counter["value"])
                        nm.inc("fileWrite",counter["value"])
                    elif counter['name'] == 'HDFS_BYTES_READ':
                        rm.inc("hdfsRead",counter["value"])
                        nm.inc("hdfsRead",counter["value"])
                    elif counter['name'] == 'HDFS_BYTES_WRITTEN':
                        rm.inc("hdfsWrite",counter["value"])
                        nm.inc("hdfsWrite",counter["value"])
            else:
                continue
    def updateWithNotSuccAppid(self,app):
        appHappenTime = getIntervalTime(app['startedTime'])
        rm = self.getRm(self.recordTime,appHappenTime)
        
        rm.inc("appNum",1)
        if app['stats'] == 'KILLED':
            rm.inc("killedApp",1)
        elif app['stats'] == 'FAILED':
            rm.inc("failedApp",1)
        
    def updateWithAppid(self,app,jobHistory,jobCounter):
        #update nm and rm
        amNode = self.getNodeFromAddress(app['amHostHttpAddress'])
        appHappenTime = getIntervalTime(app['startedTime'])
        nm = self.getNm(amNode,self.recordTime, appHappenTime)
        rm = self.getRm(self.recordTime,appHappenTime)
        
        nm.inc("containerNum",1);
        nm.inc("amNum",1);

        rm.inc("appNum",1)
        rm.inc("finishedApp",1)
        
        if app['finalStatus'] != "SUCCEEDED":
            rm.inc("notSuccApp",1)
        #end update
        appid =  app["id"]
        appRecord = self.getAppidRecord(appid)
        keyFromApp = ["user","name","queue","startedTime","finishedTime","state","finalStatus"]
        for key in keyFromApp:
            if key == "startedTime" or key == "finishedTime":
                appRecord.set(key,getSecondTime(app[key]))
            else:    
                appRecord.set(key,app[key])
        #todo
        appRecord.set("attemptNumber",1)
        keyFromHistory = ["mapsTotal","mapsCompleted","successfulMapAttempts",
                          "killedMapAttempts","failedMapAttempts","avgMapTime",
                          "reducesTotal","reducesCompleted","successfulReduceAttempts",
                          "killedReduceAttempts","failedReduceAttempts","avgReduceTime"]
        if jobHistory.has_key('job'):
            for key in keyFromHistory:
                appRecord.set(key,jobHistory['job'][key])
        #TODO "localMap","rackMap"
        keyMapFromCounters = {"DATA_LOCAL_MAPS":"localMap","RACK_LOCAL_MAPS":"rackMap",
                "FILE_BYTES_READ":"fileRead","FILE_BYTES_WRITTEN":"fileWrite",
                "HDFS_BYTES_READ":"hdfsRead","HDFS_BYTES_WRITTEN":"hdfsWrite"}
        if jobCounter:
            for (key,value) in keyMapFromCounters.items():
                appRecord.set(value,jobCounter[key]['total'])

    def getNm(self,node,recordTime,happenTime):
        key = node + str(recordTime) +str(happenTime)
        if not self.nmList.has_key(key):
            self.nmList[key] =  NmRecord(node,recordTime,happenTime)
        return self.nmList[key]
    
    def getAppidRecord(self,appid):
        if not self.appList.has_key(appid):
            self.appList[appid] = ApplicationRecord(appid)
        return self.appList[appid]

    def getRm(self,recordTime,happenTime):
        key = str(recordTime) +str(happenTime)
        if not self.rmList.has_key(key):
            self.rmList[key] =  RmRecord(recordTime,happenTime)
        return self.rmList[key]

    def upateNmData(self,node,recordTime,key,value):
        self.nm[node][recordTime][key]+=value
    
class CollectorMain:
    def __init__(self):
        self.delay_time = 120;
        self.pool = threadpool.ThreadPool(5) 
        self.stop = False;

    def run(self):
        now = int(time.time())
        record_time = getIntervalTime(now)
        between = now - record_time
        if between > self.delay_time:
            self.sumbit(record_time - config.collect_interval)
            self.sleep_sumbit_period(config.collect_interval - between + self.delay_time, record_time , config.collect_interval )
        else:
            self.sleep_sumbit_period(self.delay_time - between, record_time - config.collect_interval, config.collect_interval )

    def sleep_sumbit_period(self, sleep, record_time, period):
        log.info("sleep for %d "  % sleep)
        time.sleep(sleep)
        while not self.stop :
            self.sumbit(record_time)
            record_time += period
            time.sleep(period)

    def print_result(request, result): 
        log.info("the result is %s %r" % (request.requestID, result))


    def sumbit(self,record_time):
        log.info( "i did at %s %d" % (util.get_local_time(), record_time)  )
        coll = Collector()
        requests = threadpool.makeRequests(coll.collect, [(record_time)], self.print_result) 
        for req in requests:
            log.info("get request")
            self.pool.putRequest(req)

        

os.chdir(config.uhphome)
APP = "collect"

if __name__ == "__main__":
    log.info("start...")
    try:
        pidfile = "pids/%s/%s.pid" % (APP, APP)
        pidfile = lockfile.pidlockfile.PIDLockFile(pidfile)
        files_preserve=[logging.root.handlers[1].stream.fileno()]
        dmn = daemon.DaemonContext(None, os.getcwd(), pidfile=pidfile, files_preserve=files_preserve)
        dmn.open()
        try:
            #start collect loop
            main = CollectorMain()
            main.run()
        finally:
            dmn.close()
    except Exception as e:
        log.exception(e)
    log.info("end!")
 
