#!/usr/bin/env python
# coding=utf8

import os
import sys
import yaml
import json

commondir=os.path.join( os.getenv('UHP_HOME'),"uhpcommon")
sys.path.append(commondir) 

import config
import database
import static_config
from model.host_group_var import GroupHost,Host,GroupVar,HostVar
from model.instance import Instance


#将ansible的变量转换为数据库的变量和组关系
def conf_to_db(file):
    print "import %s into db" % file
    
    session=database.getSession()
    stream=open(file,"r")
    vars=yaml.load(stream)
    group="all"
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
    session.commit()

    session.close()

def load_special_conf():
    print "import special var"
    #session=database.getSession()
    #session.close()

def ensureDir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

def get_diff_result(default_file):
    '''
    分别从数据库和文件中获取两套配置，并计算之间的相差选项并返回。
    '''
    diff_result = {"db_only":[],"file_only":[],"same":[],"value_diff":[]}
    db_conf = load_db_conf()
    file_conf = load_file_conf(default_file) 
    for db_index in db_conf:
        if file_conf.has_key(db_index):
            v1 = db_conf[db_index]
            v2 = file_conf[db_index]
            if v1 == v2 :
                diff_result["same"].append({"name":db_index,"value":v1})
            else:
                diff_result["value_diff"].append({"name":db_index,"value_db":v1,"value_file":v2})
        else:
            v1 = db_conf[db_index]
            diff_result["db_only"].append({"name":db_index,"value":v1})
    for file_index in file_conf:
        if db_conf.has_key(file_index):
            continue
            #v1 = file_conf[file_index]
            #v2 = db_conf[file_index]
            #if v1 == v2 :
            #    diff_result["same"].append({"name":file_index,"value":v1})
            #else:
            #    diff_result["value_diff"].append({"name":file_index,"value_file":v1,"value_db":v2})
        else:
            v1 = file_conf[file_index]
            diff_result["file_only"].append({"name":file_index,"value":v1})
    return diff_result

def load_db_conf():
    conf = {}
    session=database.getSession()
    for gv in session.query(GroupVar):
        if gv.group == "all" :
            if gv.service !=None and len(gv.service) > 0 :
                name = "%s__%s" % (gv.service,gv.name)
            else:
                name = gv.name
            conf[name] = gv.value

    session.close()
    return conf

def load_file_conf(file):
    conf = {}
    stream=open(file,"r")
    vars=yaml.load(stream)
    for name in vars:
        value = vars[name]
        
        if isinstance(value,list):
            conf[name] = ",".join(value)
        else:
            conf[name] = str(value)
    return conf

def print_diff_result(diff_result):
    print "same conf 's number: %d" % len(diff_result["same"])
    print " db only:"
    print json.dumps(diff_result["db_only"], indent=2)
    print " file only:"
    print json.dumps(diff_result["file_only"], indent=2)
    print " value is diff:"
    print json.dumps(diff_result["value_diff"], indent=2)

def update_db(diff_result):
    session = database.getSession()
    group="all"
    file_only = diff_result["file_only"]
    for temp in file_only:
        name = temp["name"]
        value = temp["value"]
        print "import name:%s value: %s" % (name,value)       
        if name.find("__") > 0:
            (service,new_name) = name.split("__")
        else:
            service=""
            new_name=name

        if isinstance(value,list):
            gv = GroupVar(group,service,new_name,",".join(value),1,"") 
        else:
            gv = GroupVar(group,service,new_name,value,0,"")

        session.add(gv)
    session.commit()
    session.close()

if __name__ == "__main__":

    
    if len(sys.argv) <= 1:
        action = "diff"
    else:
        action = sys.argv[1]


    ansible_var_dir=os.path.join(config.uhphome,"conf","ansible_var")
    default_file = os.path.join(ansible_var_dir,"default")
    if action == "diff" :
        #查询当前的设置和原来的设置进行对比
        print "diff var between db and default file:"
        diff_result =  get_diff_result(default_file)
        print_diff_result(diff_result)
    elif action == "import" :
        #导入增量配置
        print "import conf that only file exist"
        diff_result =  get_diff_result(default_file)
        update_db(diff_result)
    else:
        print "usage: update_db_conf.py diff|import"




