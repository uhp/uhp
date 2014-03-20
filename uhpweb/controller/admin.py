# -*- coding: UTF-8 -*-
import os
import json
import logging
import time
import copy

import tornado
from sqlalchemy.orm import query,aliased
from sqlalchemy import and_,or_,desc,asc

import async
import static_config
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

app_log = logging.getLogger("tornado.application")

class AdminHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user();
        if user['type'] != 0 :
            self.ret("error","this user is not admin")
            return
        self.render("admin.html")
        
class AdminBackHandler(BaseHandler):
    
    @tornado.web.authenticated
    def get(self , path):
        user = self.get_current_user();
        if user['type'] != 0 :
            self.ret("error","this user is not admin")
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
        ret = {"user":user,"menus":static_config.adminmenus}
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
                    

        ret = { "services" : services_copy }
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
        
    def get_service_summary(self,service):
        session = database.getSession()
        ret = {}
        for role in static_config.get_role_from_service(service):
            ret[role] = {}
   
        for instance in session.query(Instance).filter(Instance.service==service):
            if not ret[instance.role].has_key(instance.health) :
                ret[instance.role][instance.health] = 0;
            ret[instance.role][instance.health] = ret[instance.role][instance.health] + 1;
        
        session.close()
        return ret;
    
    #获取所有的机器和组
    def group_host_list(self):
        session = database.getSession()
        groups = session.query(Group)
        ret={};
        temp=[];
        for group in groups:
            temp.append( {"name" : group.group});
        ret["groups"]=temp
        hosts = session.query(Host).filter(Host.status==Host.STATUS_READY)
        temp=[];
        for host in hosts:
            temp.append( {"name" : host.hostname});
        ret["hosts"]=temp
        session.close()
        self.ret("ok", "", ret);
    
    #获取配置变量的接口 兼容组变量和机器变量，机器变量不过滤机器名称
    def conf_var(self):
        service = self.get_argument("service")
        group = self.get_argument("group","all")
        showType = self.get_argument("showType")
        temp = []
        session = database.getSession()
        if  showType=="group":
            groupVars = session.query(GroupVar).filter(and_( GroupVar.service == service , GroupVar.group == group ) )
            for groupVar in groupVars:
                temp.append( groupVar.format() );
        else:
            hostVars = session.query(HostVar).filter( HostVar.service == service )
            for hostVar in hostVars:
                temp.append( hostVar.format() );
        session.close()       
        self.ret("ok", "", {"conf":temp})
        
    #保存 修改 删除  分组变量或者机器变量
    #TODO增加区分是否第一次插入
    def save_conf_var(self):
        service = self.get_argument("service")
        showType = self.get_argument("showType")
        group = self.get_argument("group","")
        host = self.get_argument("host","")
        name = self.get_argument("name")
        value = self.get_argument("value")
        type = self.get_argument("type")
        text = self.get_argument("text","")
        showdel = self.get_argument("del","")
        self.save_var_todb(service,showType,group,host,name,value,type,text,showdel)
        self.ret("ok", "", {})

    def save_var_todb(self,service,showType,group,host,name,value,type,text,showdel=""):
        value = str(value)
        session = database.getSession()
        if  showType=="group":
            groupVar = GroupVar(group,service,name,value,type,text)
            if showdel=="del":
                for groupVar in session.query(GroupVar).filter( and_( GroupVar.service == service , GroupVar.group == group , GroupVar.name == name )) :
                    session.delete(groupVar)
                session.commit()
            else:
                session.merge(groupVar)
                session.commit()
           
        else:
            hostVar = HostVar(host,service,name,value,type,text)
            if showdel=="del":
                for hostVar in session.query(HostVar).filter( and_( HostVar.service == service , HostVar.host == host , HostVar.name == name )) :
                    session.delete(hostVar)
                session.commit()
            else:
                session.merge(hostVar)
                session.commit()
        session.close()
    
    
    # 提交一个执行任务 
    # 当前直接把收到start的instance，标记为start状态
    # 当前直接把收到stop的instance，标记为stop状态
    # TODO 加入starting stopping 状态进行检查
    #
    def send_action(self):
        taskType = self.get_argument("taskType","ansible")
        service = self.get_argument("service")
        actionType = self.get_argument("actionType")
        instances = self.get_argument("instances","")
        taskName = self.get_argument("taskName")
        runningId = []
        session = database.getSession()
        if actionType=="service":
            #针对服务的操作
            self.update_with_service_action(session,service,taskName)
            
            task = Task(taskType,service,"","",taskName);
            session.add(task)
            session.flush()
            runningId.append(task.id)
            
        elif actionType=="instance":
            for instance in instances.split(","):
                temp = instance.split("-")
                app_log.info(instance)
                if len(temp) == 2 :
                    host = temp[0]
                    role = temp[1]
                    task = Task(taskType,service,host,role,taskName);    
                    session.add(task)
                    
                    self.update_with_instance_action(session,service,host,role,taskName)
                    
                    session.flush()
                    runningId.append(task.id)
        else:
            self.ret("error", "unsport actionType")
        session.commit()
        session.close()
        #发送消息到MQ
        retMsg = ""
        msg = ','.join([str(id) for id in runningId])
        if not mm.send(msg):
            retMsg = "send message to worker error"
        
        self.ret("ok", retMsg, {"runningid": runningId})
    
    #对某个task发送kill命令
    def kill_task(self):
        taskid = self.get_argument("taskid")
        
        #发送消息到MQ
        if not mm.kill_task(int(taskid)):
            self.ret("error", "killing task failed")
        else:
            self.ret("ok", "")
        
    #尝试重跑某个失败的task
    def rerun_task(self):
        taskid = self.get_argument("taskid")
        session = database.getSession()
        for task in session.query(Task).filter(Task.id==taskid):
            newTaskid = database.build_task(session,task.taskType,task.service,task.host,task.role,task.task)
            
        #发送消息到MQ
        retMsg = ""
        msg = str(newTaskid)
        if not mm.send(msg):
            retMsg = "send message to worker error"
        
        app_log.info("send msg to mq")
        session.close()    
        self.ret("ok", retMsg, {"taskid":newTaskid} )
    
    #进行状态管理
    #接收一个action，进行状态更新
    def update_with_service_action(self,session,service,taskName):
        if taskName == "start" :
            session.query(Instance).filter(Instance.service==service) \
                    .update({Instance.status:Instance.STATUS_START,\
                             Instance.uptime:int(time.time())})
            session.commit();
        elif taskName == "stop" :
            session.query(Instance).filter(Instance.service==service) \
                    .update({Instance.status:Instance.STATUS_STOP,
                             Instance.uptime:0})
            session.commit();
            
    def update_with_instance_action(self,session,service,host,role,taskName):
        if taskName == "start" :
            session.query(Instance).filter(and_(Instance.service==service, \
                     Instance.host == host, Instance.role == role )) \
                    .update({Instance.status:Instance.STATUS_START,
                             Instance.uptime:int(time.time())})
            session.commit();
        elif taskName == "stop" :
            session.query(Instance).filter(and_(Instance.service==service, \
                     Instance.host == host, Instance.role == role )) \
                    .update({Instance.status:Instance.STATUS_STOP,
                             Instance.uptime:0})
            session.commit();
    
    #添加一个机器
    #端口 用户名 密码 等都是空的 在异步连接的时候会补充这个
    def add_host(self):  
        hosts = self.get_argument("hosts")
        port = self.get_argument("port","")
        user = self.get_argument("user","")
        passwd = self.get_argument("passwd","")
        sudopasswd = self.get_argument("sudopasswd","")
        
        host_array = hosts.split(",")
        (check,msg) = self.check_add_host(host_array)
        if not check:
            self.ret("error", msg)
            return
        
        id = async.async_setup()
        async.async_run(async.add_host,(id,host_array,(user,port,passwd,sudopasswd)))
        self.ret("ok", "", {"runningId": [id]})
    
    def check_add_host(self,hostArray):
        session = database.getSession()
        for host in hostArray:
            num = session.query(Host).filter(Host.hostname==host).count()
            if util.look_like_ip(host) :
                return (False,host+" look like ip, please check")
            if num != 0 :
                return (False,host+" is already in host table")
        session.close()
        return (True,"")
    
    #查询进度
    def query_progress(self):
        idList = self.get_argument("id")
        ids = json.loads(idList)
        progress = 0;
        progress_msg = "";
        session = database.getSession()
        for nid in ids:
            (pg,msg) = self.query_id_process(session,nid)
            if nid < 0:
                progress_msg += "SyncTask  taskid: (%d) %s \n" % (-nid,msg);
            else:
                progress_msg += "Task  taskid:(%d) %s \n" % (nid,msg);
            progress += int(pg)
        session.close()
        progress /= len(ids)
        self.ret("ok", "", {"id": ids,"progress":progress,"progressMsg":progress_msg } )
    
    def query_id_process(self,session,nid):
        if nid <0 :
            #同步任务
            return (async.async_get(nid,"progress","0"),async.async_pop(nid,"progressMsg",""))
        else:
            #worker 任务
            queryTask = session.query(Task).filter(Task.id==nid)
            if queryTask.count() == 0:
                return (0,str(id)+" isn't exist")
            else:
                nowTask = queryTask[0]
                return (nowTask.getProcess(),nowTask.msg)
    
    #获取机器列表
    def hosts(self):
        session = database.getSession()
        hosts = session.query(Host)
        ret={}
        for host in hosts:
            ret[host.hostname]={"info":host.format()}
        session.close()
        self.ret("ok", "", {"hosts":ret})
         
    def del_host(self):
        hosts = self.get_argument("hosts")
        session = database.getSession()
        (check,msg)=self.check_del_host(session,hosts)
        if not check:
            self.ret("error", msg)
            return
        
        #删除机器
        queryHosts = session.query(Host).filter(Host.hostname.in_(hosts.split(",")))
        for host in queryHosts:
            session.delete(host)
        #删除分组信息
        queryGH = session.query(GroupHost).filter(GroupHost.hostname.in_(hosts.split(",")))
        for gh in queryGH:
            session.delete(gh)
        session.commit()
        session.close()
        self.ret("ok", "")
    
    def check_del_host(self,session,hosts):
        num = session.query(Instance).filter(Instance.host.in_(hosts.split(","))).count()
        if num != 0 :
            return (False,"some host find in instance.please remove them first")
        return (True,""+str(num))
    
    #查询机器和角色的关系
    def host_role(self):
        
        session= database.getSession()
        active=[]
        for service in session.query(Service):
            if service.status == Service.STATUS_ACTIVE :
                active.append(service.service)
                
        roles = {};
        for service in static_config.services:
            if service["name"] in active:
                roles[service["name"]] = service["role"]

        hostroles = {}
        doing=[]
        #补充所有的host列表
        hosts = session.query(Host).filter(Host.status == Host.STATUS_READY)
        for host in hosts:
            hostname = host.hostname;
            hostroles[hostname]={};
            hostroles[hostname]['role']=[]
            
        instances = session.query(Instance)
        for instance in instances:
            role = instance.role
            host = instance.host
            hostroles[host]['role'].append(role)
            if instance.status == Instance.STATUS_SETUP or instance.status == Instance.STATUS_REMOVING :
                doing.append({"host":host,"role":role,"status":instance.status})
            
        session.close()
        self.ret("ok", "",{"roles":roles,"hostroles":hostroles,"doing":doing})
    
    #查询正在进行的服务
    def doing(self):
        doing = []
        session = database.getSession()
        instances = session.query(Instance)
        for instance in instances:
            role = instance.role
            host = instance.host
            if instance.status == Instance.STATUS_SETUP or instance.status == Instance.STATUS_REMOVING :
                doing.append({"host":host,"role":role,"status":instance.status})
        session.close()
        self.ret("ok", "",{"doing":doing})
        
    #添加一个服务
    def add_service(self):
        service = self.get_argument("service")
        add_args = self.get_argument("add")
        var_args = self.get_argument("vars","[]")
         
        add_instance = json.loads(add_args)
       
        #设定一些必要的变量
        varArgs = json.loads(var_args)
        for var in varArgs:
            self.save_var_todb(var['service'],var['showType'],var['group'], 
                           var['host'],var['name'],var['value'],var['type'], 
                           var['text'])
        
        #开启服务
        new_ser = Service(service,Service.STATUS_ACTIVE)
        session = database.getSession()
        session.merge(new_ser)
        session.commit()
        session.close()
        
        self.inner_add_del_instance(add_instance, [])
       
    def can_del_service(self):
        service = self.get_argument("service")
        session = database.getSession()
        instances = [];
        for instance in session.query(Instance).filter(Instance.service == service):
            instances.append(instance.host+"-"+instance.role)
        session.close()
        if len(instances) == 0:
            self.ret("ok", "")
        else:
            self.ret("error","some instance is exist please remove then first. instances:"+(",".join(instances)))
        
    def del_service(self):
        service = self.get_argument("service")
         
        #关闭服务
        new_ser = Service(service,Service.STATUS_INIT)
        session = database.getSession()
        session.merge(new_ser)
        session.commit()
        session.close()
        self.ret("ok", "")
        
    #添加删除实例instance
    #删除提交任务，并且轮询任务是否执行完成
    #如果任务执行完成，就删除
    def add_del_instance(self):
        add_args = self.get_argument("add","[]")
        del_args = self.get_argument("del","[]")
        var_args = self.get_argument("vars","[]")
        
        #设定一些必要的变量
        var_args = json.loads(var_args)
        for var in var_args:
            self.save_var_todb(var['service'],var['showType'],var['group'], 
                           var['host'],var['name'],var['value'],var['type'], 
                           var['text'])
        
        add_instance = json.loads(add_args)
        del_instance = json.loads(del_args)
        self.inner_add_del_instance(add_instance,del_instance)

    def inner_add_del_instance(self,add_instance,del_instance):
        session = database.getSession()
        (check,msg)=self.check_add_instance( session, add_instance)
        if not check:
            self.ret("error", msg);
            return;
        
        (check,msg)=self.check_del_instance( session, del_instance)
        if not check:
            self.ret("error", msg);   
            return;
        
        if len(add_instance) == 0 and len(del_instance) == 0:
            self.ret("error", "no instance need to add or del");   
            return;
        
        add_running_id = self.add_instance(add_instance)
        del_running_id = self.del_instance(del_instance)
       
#         async.async_run(async.add_del_service,(addRunningId,delRunningId))
        for taskid in add_running_id:
            callback_lib.add_callback(session,taskid,"dealAddInstance")
            
        for taskid in del_running_id:
            callback_lib.add_callback(session,taskid,"dealDelInstance")
        session.close()  
        if config.fade_add_del:
            async.async_run(async.fade_add_del_service,(add_running_id,del_running_id))
        
        #发送消息到MQ
        ret_msg = ""
        msg = ','.join([str(id) for id in (add_running_id + del_running_id)])
        if not mm.send(msg):
            ret_msg = "send message to worker error"
        
        self.ret("ok", ret_msg, {"addRunningId":add_running_id,"delRunningId":del_running_id})
        
        
    def add_instance(self,addInstance):
        #将add插入到instance表    
        session = database.getSession()
        for add_inst in addInstance:
            temp_service = static_config.get_service_from_role(add_inst["role"])
            new_in = Instance(temp_service,add_inst["host"],add_inst["role"])
            new_in.status = Instance.STATUS_SETUP
            session.merge(new_in)
        session.commit()
        
        #提交活动
        running_id=[]
        for add_inst in addInstance:
            temp_service = static_config.get_service_from_role(add_inst["role"])
            taskid = database.build_task(session,"ansible",temp_service,add_inst["host"],add_inst["role"],"setup")
            running_id.append(taskid)
            
        session.commit()
        session.close()
        return running_id
    
    def del_instance(self,delInstance):
        #更新instance表的对应状态为removing
        session = database.getSession()
        for delInst in delInstance:
            tempService = static_config.get_service_from_role(delInst["role"])
            newIn = Instance(tempService,delInst["host"],delInst["role"])
            newIn.status = Instance.STATUS_REMOVING
            session.merge(newIn)
        session.commit()
        #提交卸载活动
        running_id=[]
        for delInst in delInstance:
            tempService = static_config.get_service_from_role(delInst["role"])
            newTask = Task("ansible",tempService,delInst["host"],delInst["role"],"remove")
            session.add(newTask)
            session.flush();
            running_id.append(newTask.id)
            
        session.commit()
        session.close()
        return running_id
    
    def check_add_instance(self,session,addInstance):   
        for addInst in addInstance:
            num = session.query(Instance).filter(and_(Instance.host == addInst["host"], \
                                                       Instance.role == addInst["role"])).count()
            if num == 1:
                return (False,"instance is exist (%s,%s) " % (addInst["host"],addInst["role"]) )
        return (True,"" )
    
    def check_del_instance(self,session,delInstance):   
        for delInst in delInstance:
            query = session.query(Instance).filter(and_(Instance.host == delInst["host"], \
                                                        Instance.role == delInst["role"]))
            num = query.count();
            if num == 0 or num > 1:
                return (False,"instance is not exist ( %s,%s) " % (delInst["host"],delInst["role"]))
            else:
                for instance in query:
                    if instance.status != "stop":
                        return (False,"instance's status is not stop (%s,%s) " % (delInst["host"],delInst["role"]) )
        return (True,"")
    
    
    #查询任务
    #dir=desc&limit=50&offset=0&orderby=id&search=aaa
    def tasks(self):
        search = self.get_argument("search","")
        orderby = self.get_argument("orderby","")
        dir = self.get_argument("dir","")
        offset = self.get_argument("offset","")
        limit = self.get_argument("limit","")
        
        session = database.getSession()
        query = session.query(Task)
        if search != "" :
            search='%'+search+'%'
            query = query.filter(or_(Task.id.like(search),Task.taskType.like(search),Task.service.like(search), \
                                     Task.host.like(search),Task.role.like(search),Task.status.like(search), \
                                     Task.result.like(search)))
        total_task = query.count();
        
        if dir=="asc":
            query = query.order_by(asc(orderby))[int(offset):int(offset)+int(limit)]
        else :
            query = query.order_by(desc(orderby))[int(offset):int(offset)+int(limit)]
        
        task_list=[]
        for task in query:
            task_list.append(task.format())
            
        session.close()
        self.ret("ok", "", {"tasks":task_list,"totalTask":total_task})
    
    #查询单个任务的详细
    def task_detail(self):
        taskid = self.get_argument("taskid")
        session = database.getSession()
        task = session.query(Task).filter(Task.id==taskid).first()
        tf = task.format()
        tf['msg'] = task.msg
        session.close()
        self.ret("ok", "", {"task":tf})
        
    #查询机器和组的对应关系
    def host_group(self):
        session = database.getSession()
        groups = {}
        hostgroups = {}
        for host in  session.query(Host).filter(Host.status ==  Host.STATUS_READY ):
            hostgroups[host.hostname]={}
            hostgroups[host.hostname]["group"]=['all']
        for group in  session.query(Group):
            groups[group.group]=group.text
        for gh in session.query(GroupHost):
            hostgroups[gh.hostname]["group"].append(gh.group)
        session.close()
        self.ret("ok","",{"groups":groups,"hostgroups":hostgroups})
        
    #保存组
    def save_group(self):
        name = self.get_argument("group")
        text = self.get_argument("text","")
        toDel = self.get_argument("del","")
        
        nowGroup = Group(name,text)
        session = database.getSession()
        if toDel=="del":
            for group in session.query(Group).filter(Group.group==name):
                session.delete(group)
            session.commit()
        else:
            session.merge(nowGroup)
            session.commit()
        session.close()
        self.ret("ok","")
        
    #修改机器和分组的关系
    def setup_group(self):
        add_args = self.get_argument("add")
        del_args = self.get_argument("del")
        
        add_groups = json.loads(add_args)
        del_groups = json.loads(del_args)
        
        session = database.getSession()
        for addGroup in add_groups:
            gh = GroupHost(addGroup['group'],addGroup['host'])
            session.merge(gh)
        session.commit
        
        for delGroup in del_groups:
            query = session.query(GroupHost).filter(and_(GroupHost.hostname==delGroup['host'],GroupHost.group==delGroup['group']))
            for gh in query:
                session.delete(gh)
        session.commit()
        session.close()
        self.ret("ok","")
        
    #******************************************************    
    #获取所有的template文件
    def template_list(self):
        templates={}
        for dir in os.listdir(config.template_dir):
            if dir.startswith('.') :
                continue;
            dirPath = os.path.join(config.template_dir,dir)
            if os.path.exists(dirPath) and os.path.isdir(dirPath):
                templates[dir] = []
                for file in os.listdir(dirPath):
                    filePath = os.path.join(dirPath,file)
                    app_log.info(filePath)
                    if os.path.exists(filePath) and os.path.isfile(filePath):
                        file = file.replace(".j2","")
                        templates[dir].append(file);
                templates[dir].sort()
        self.ret("ok","",{"templates":templates})
    
    #获取指定的文件内容
    def template_file(self):
        dir = self.get_argument("dir")
        file = self.get_argument("file")
        file = file+".j2"
        filePath = os.path.join(config.template_dir,dir,file)
        if os.path.exists(filePath) and os.path.isfile(filePath):
            content = open(filePath, "r").read()
            self.ret("ok","",{"content":content,"row":self.get_content_row(content)})
        else:
            self.ret("error","file not exist")     
            
            
    #获取生成的配置文件
    def template_build_file(self):
        dir = self.get_argument("dir")
        file = self.get_argument("file")
        file = file+".j2"
        host = self.get_argument("host")
        (content,output) = shell_lib.get_template_file(host,dir,file);
        if content != "":
            self.ret("ok","",{"content":content,"row":self.get_content_row(content) })
        else:
            self.ret("error",output)
            
    def get_content_row(self,content):
        count = 0 ;
        for c in content:
            if c == "\n" :
                count = count+1
        return count;
    
    def save_template_file(self):
        dir = self.get_argument("dir")
        file = self.get_argument("file")
        file = file+".j2"
        content = self.get_argument("content")
        filePath = os.path.join(config.template_dir,dir,file)
        fd = open(filePath,"w")
        fd.write(content);
        time.sleep(2)
        self.ret("ok","")
                
                
    #****************************************************************************************
    #manual获取数据库的表
    def manual_metadata(self):
        table={}
        models = database.get_all_models()
        temp = {}
        for model in models:
            temp = {}
            temp['column']=[]
            temp['primary']=[]
            for col in model.__table__.columns:
                if col.primary_key:
                    temp['primary'].append(col.name)
                else:
                    temp['column'].append(col.name)
            table[model.__tablename__]=temp       
        self.ret("ok","",{"table":table})
        
    def manual_query(self):
        sql = self.get_argument("sql")
        
        session = database.getSession()
        result = session.execute(sql)
        data = []
        for record in result:
            temp = [];
            for value in record:
                temp.append(value)
            data.append(temp);
        session.close()
        self.ret("ok","",{"column":result.keys(),"data":data})
        
    #修改数据库 直接使用merge进行合并
    def manual_execute(self):
        sql = self.get_argument("sql")
        session = database.getSession()
        result = session.execute(sql)
        session.commit()
        session.flush()
        session.close()
        self.ret("ok","")
        
