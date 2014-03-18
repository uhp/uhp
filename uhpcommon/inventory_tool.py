#!python
# coding=utf8

import os
import database
from model.host_group_var import GroupHost,Host,GroupVar,HostVar
from model.instance import Instance
import yaml
import static_config
import config

##将数据库的数据转换为ansible的配置
#def dbToConf(dir=config.default_ansible_dir):
#    group_var_dir=os.path.join(dir,"group_vars")
#    host_var_dir=os.path.join(dir,"host_vars")
#    
#    ensureDir(dir)
#    ensureDir(group_var_dir)
#    ensureDir(host_var_dir)
#
#    session=database.getSession()
#    #写hosts文件
#    hosts=[]
#    for host in session.query(Host):
#        hosts.append(host.hostname)
#    groups={}
#    for gh in session.query(GroupHost):
#        if not groups.has_key(gh.group):
#            groups[gh.group]=[]
#        groups[gh.group].append(gh.hostname)
#
#    roles={}
#    for ser in static_config.services:
#        for role in ser['role']:
#            roles[role]=[]
#
#    #查询instance表的数据
#    for instance in session.query(Instance):
#        roles[instance.role].append(instance.host)
#
#    writeHostFile(hosts,roles,groups,dir+"/"+"hosts")
#    #写组变量
#    groupVars={}
#    for var in session.query(GroupVar):
#        group = var.group
#        service = var.service
#        name = var.name
#        value = var.value
#        type = var.type
#        if not groupVars.has_key(group):
#            groupVars[group]={}
#
#        if service != None and len(service) > 0 :
#            name=service+"__"+name
#
#        if type == 0 :
#            groupVars[group][name]=value
#        else:
#            groupVars[group][name]=value.split(",")
#    
#    for group in groupVars:
#        stream = open(os.path.join(dir,"group_vars",group), 'w')
#        yaml.safe_dump(groupVars[group],stream)
#
#    #写机器变量
#    hostVars={}
#    for var in session.query(HostVar):
#        host = var.host
#        service = var.service
#        name = var.name
#        value = var.value
#        type = var.type
#        if not hostVars.has_key(host):
#            hostVars[host]={}
#        if service != None and len(service) > 0 :
#            name=service+"__"+name
#        if type == 0 :
#            hostVars[host][name]=value
#        else:
#            hostVars[host][name]=value.split(",")
#    
#    for host in hostVars:
#        stream = open(os.path.join(dir,"host_vars",host), 'w')
#        yaml.safe_dump(hostVars[host],stream)
#

#将ansible的变量转换为数据库的变量和组关系
def conf_to_db(dir):
    group_var_dir=os.path.join(dir,"group_vars")
    host_var_dir=os.path.join(dir,"host_vars")
    
    session=database.getSession()
    #将机器和组的关系写入数据库
    #TODO
    
    #读取组变量
    for group in os.listdir(group_var_dir):
        if group.startswith("."):
           continue
        stream=open(os.path.join(group_var_dir,group),"r")
        vars=yaml.load(stream)
        for name in vars:
            value = vars[name]
            
            if name.find("__") > 0:
                (service,new_name) = name.split("__")
            else:
                service=""
                new_name=name

            if isinstance(value,list):
                gv = GroupVar(group,service,new_name,",".join(value),1,"") 
            else:
                gv = GroupVar(group,service,new_name,value,0,"")

            session.merge(gv)

    #添加特殊变量
    gv = GroupVar("all","","UHP_HOME",config.uhphome,0,"")
    session.merge(gv)
    gv = GroupVar("all","","TEMPLATE_DIR",config.template_dir,0,"")
    session.merge(gv)
    gv = GroupVar("all","","JAR_DIR",config.jar_dir,0,"")
    session.merge(gv)
    session.commit()

    #读取机器变量
    if os.path.exists(host_var_dir):
        for host in os.listdir(host_var_dir):
            if host.startswith("."):
                continue
            stream=open(os.path.join(host_var_dir,host),"r")
            vars=yaml.load(stream)
            for name in vars:
                value = vars[name]
    
                if name.find("__") > 0:
                    (service,new_name) = name.split("__")  
                else:
                    service=""
                    new_name=name
    
                if isinstance(value,list):
                    hv = HostVar(host,service,new_name,",".join(value),1,"")
                else:
                    hv = HostVar(host,service,new_name,value,0,"")
                session.merge(hv)
    session.commit()

#对于host文件约定不使用组继承和设置变量
#仅用于列出所有的机器和分组
def readHostFile(file="/etc/ansible/hosts"):
    lines = []
    if os.path.exists(file):
        fh = open(file,"r")
        lines = fh.readlines()
        fh.close()
    active_group_name="host"
    hosts=[]
    groups={}
    for line in lines:
        line = line.strip("\n")
        if len(line) == 0 or line=="\n" or line.startswith("#"):
            continue
        elif line.startswith("[") and line.endswith("]"):
            active_group_name = line.replace("[","").replace("]","")
            groups[active_group_name]=[]
        else:
            if active_group_name=="host":
                hosts.append(line)
            else:
                groups[active_group_name].append(line)

    return (hosts,groups)

def writeHostFile(hosts,roles,groups,file="/etc/ansible/hosts"):
    fh = open (file, 'w' ) 
    seq = []
    for host in hosts:
        seq.append(host+"\n")
    seq.append("\n")
    fh.writelines(seq)
    
    for role in roles:
        #if len(role) > 0 :
        seq=[]
        seq.append("["+role.upper()+"]\n")
        for mem in roles[role]:
            seq.append(mem+"\n")
        seq.append("\n")
        fh.writelines(seq)

    for name in  groups:
        seq=[]
        seq.append("["+name+"]\n")
        for mem in groups[name]:
            seq.append(mem+"\n");
        seq.append("\n")
        fh.writelines(seq)
    fh.close()

def ensureDir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

if __name__ == "__main__":

    #writeHostFile(["hadoop1","hadoop2","hadoop3"],{"g1":["hadoop1"],"g2":["hadoop2"]},"/home/qiujw/temp/temphost")
    #(hosts,g)=readHostFile("/home/qiujw/temp/temphost")

    #dbToConf("/home/qiujw/temp/ansible")
    ansible_back_dir=os.path.join(config.uhphome,"conf","ansible_back")
    conf_to_db(ansible_back_dir)



