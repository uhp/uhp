#!/usr/bin/env python
# coding=utf8

import os
import os.path
import sys
import json
import yaml
from optparse import OptionParser

sys.path.append(os.path.join(os.getenv('UHP_HOME'), "uhpcommon"))
import database
from model.host_group_var import GroupHost, Host, GroupVar, HostVar
from model.instance import Instance

# see: http://docs.ansible.com/developing_inventory.html

class MysqlInventory(object):

    META  = '_meta'
    ALL   = 'all'
    HOSTS = 'hosts'
    HVARS = 'hostvars'
    VARS  = 'vars'

    def __init__(self):
        self.groups = {} 
        
        self._parse_cli_args()
        
        if self.opts.list:
            self._load_conf_from_db()
            data_to_print = self._json_format_dict(self.groups, True)
            print data_to_print
        elif self.opts.savedir:
            print "save conf to", self.opts.savedir
            self._load_conf_from_db()
            self._save_to_dir(self.opts.savedir)
        elif self.opts.recoverdir:
            print "recover conf from", self.opts.recoverdir
            self._load_conf_from_dir(self.opts.recoverdir)
            self._save_to_db()
        else:
            raise Exception("unsuport action")

    def _parse_cli_args(self):
        """ Command line argument processing """
        
        parser = OptionParser()
        parser.add_option("-l", "--list", action="store_true", dest="list", help="list all host")
        parser.add_option("-s", "--save-dir", dest="savedir", help="write conf file to dir")
        parser.add_option("-r", "--recover-dir", dest="recoverdir", help="load from dir to db")
        
        (self.opts, self.args) = parser.parse_args()

    #将数据库的数据转换为ansible的配置
    def _load_conf_from_db(self):
        session = database.getSession(False)

        hosts = []
        for host in session.query(Host):
            hosts.append(host.hostname)
        
        self.groups[self.ALL] = {self.HOSTS: hosts}

        groups = self.groups
    
        #查询instance表的数据
        for instance in session.query(Instance):
            gname = instance.role.upper()
            if not groups.has_key(gname):
                groups[gname] = {}
                groups[gname][self.HOSTS] = []
            groups[gname][self.HOSTS].append(instance.host)

        for gh in session.query(GroupHost):
            if not groups.has_key(gh.group):
                groups[gh.group] = {}
            if not groups[gh.group].has_key(self.HOSTS):
                groups[gh.group][self.HOSTS] = []
            groups[gh.group][self.HOSTS].append(gh.hostname)
       
        # 组变量
        for var in session.query(GroupVar):
            group = var.group
            service = var.service
            name = var.name
            value = var.value
            type = var.type

            if not groups[group].has_key(self.VARS):
                groups[group][self.VARS] = {}
            group_vars = groups[group][self.VARS]
    
            if service != None and len(service) > 0 :
                name = service + "__" + name
    
            if type == 0 : # 值
                group_vars[name] = value
            else: # 数组
                group_vars[name] = value.split(",")

        #特别添加的特殊变量 hdfs__net_topology_map
        net_topology_map = []
        for host in session.query(Host):
            net_topology_map.append( "%s %s %s" % (host.ip,host.hostname,host.rack) )
        groups['all']['vars']['hdfs__net_topology_map'] = net_topology_map


        
        #写机器变量
        # _meta:hostvars
        groups[self.META] = {}
        groups[self.META][self.HVARS] = {}
        host_vars = groups[self.META][self.HVARS] # host:{k:v}
        for var in session.query(HostVar):
            host = var.host
            service = var.service
            name = var.name
            value = var.value
            type = var.type

            if not host_vars.has_key(host):
                host_vars[host] = {}

            if service != None and len(service) > 0 :
                name = service + "__" + name

            if type == 0 :
                host_vars[host][name] = value
            else:
                host_vars[host][name] = value.split(",")

        session.close()

    def _json_format_dict(self, data, pretty=False):
        if not pretty: return json.dumps(data)
        return json.dumps(self.groups, sort_keys=True, indent=2)

    #将数据库的数据转换为ansible的配置
    def _save_to_dir(self, dir):
        group_var_dir = os.path.join(dir, "group_vars")
        host_var_dir = os.path.join(dir, "host_vars")
        
        self.ensure_dir(dir)
        self.ensure_dir(group_var_dir)
        self.ensure_dir(host_var_dir)
        
        groups = self.groups
        self.write_host_file(os.path.join(dir, "hosts"))

        # write group vars
        for (gname, group) in groups.items():
            if not group.has_key(self.VARS): continue
            stream = open(os.path.join(dir, "group_vars", gname), 'w')
            yaml.safe_dump(group[self.VARS], stream)
    
        # write host vars
        host_vars = {}
        if self.META in groups and self.HVARS in groups[self.META]:
            host_vars = groups[self.META][self.HVARS]
        for (host, vars) in host_vars.items():
            stream = open(os.path.join(dir, "host_vars", host), 'w')
            yaml.safe_dump(vars, stream)
    
    def _load_conf_from_dir(self, dir):
        host_file = os.path.join(dir, "hosts")
        group_var_dir = os.path.join(dir, "group_vars")
        host_var_dir = os.path.join(dir, "host_vars")
       
        groups = self.groups
        #机器和组的关系
        self.read_host_file(groups, host_file)
        
        #读取组变量
        for gname in os.listdir(group_var_dir):
            if gname.startswith("."): continue
            
            if gname not in groups: groups[gname] = {}
            groups[gname][self.VARS] = {}
            stream = open(os.path.join(group_var_dir, gname), "r")
            vars = yaml.load(stream)
            for (k, v) in vars.items():
                groups[gname][self.VARS][k] = v 
    
        #读取机器变量
        host_vars = {}
        for host in os.listdir(host_var_dir):
            if host.startswith("."): continue

            host_vars[host] = {} 
            stream=open(os.path.join(host_var_dir,host),"r")
            vars=yaml.load(stream)
            for (k, v) in vars.items():
                host_vars[host][k] = v
   
        if host_vars:
            groups[self.META] = {}
            groups[self.META][self.HVARS] = host_vars

    # 将ansible的变量转换为数据库的变量和组关系
    def _save_to_db(self):
        session = database.getSession()
        groups = self.groups
        
        # 组变量
        for (gname, group) in groups.items():
            if gname == self.META: continue
            if self.VARS not in group: continue
            gname = gname.lower()
            for (name, value) in group[self.VARS].items():
                if name.find("__") > 0:
                    (service, new_name) = name.split("__")
                else:
                    service=""
                    new_name=name
    
                if isinstance(value, list):
                    gv = GroupVar(gname, service, new_name, ",".join(value), 1, "") 
                else:
                    gv = GroupVar(gname, service, new_name, value, 0, "")
    
                session.merge(gv)
        session.commit()
    
        #读取机器变量
        host_vars = {}
        if self.META in groups and self.HVARS in groups[self.META]: 
            host_vars = groups[self.META][self.HVARS]
        for (host, vars) in host_vars.items():
            for (name, value) in vars.items():
                if name.find("__") > 0:
                    (service, new_name) = name.split("__")  
                else:
                    service=""
                    new_name=name
    
                if isinstance(value,list):
                    hv = HostVar(host,service,new_name,",".join(value),1,"")
                else:
                    hv = HostVar(host,service,new_name,value,0,"")
                session.merge(hv)
        session.commit()
        session.close()
    
    # 对于host文件约定不使用组继承和设置变量
    # 仅用于列出所有的机器和分组
    def read_host_file(self, groups, file = "/etc/ansible/hosts"):
        if not os.path.exists(file): 
            raise RuntimeException("file[%s] is not exists" % file)
        
        active_gname = self.ALL 
        groups[active_gname] = {}
        groups[active_gname][self.HOSTS] = []
        for line in open(file, "r"):
            line = line.strip()
            if not line or line.startswith("#"): continue
            
            if line.startswith("[") and line.endswith("]"):
                active_gname = line.replace("[","").replace("]","")
                groups[active_gname] = {}
                groups[active_gname][self.HOSTS] = []
                continue
            
            groups[active_gname][self.HOSTS].append(line)
    
    def write_host_file(self, file="/etc/ansible/hosts"):
        groups = self.groups
        fh = open(file, 'w') 
       
        for (gname, group) in groups.items():
            if gname == self.META: continue
            fh.write("[%s]\n" % gname)
            hosts = group[self.HOSTS]
            [fh.write(host + "\n") for host in hosts]
            fh.write("\n")
    
        fh.close()
    
    def ensure_dir(self, dir):
        if not os.path.exists(dir):
            os.mkdir(dir)
    
if __name__ == "__main__":
    MysqlInventory()
