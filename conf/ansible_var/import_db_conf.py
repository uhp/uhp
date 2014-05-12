#!/usr/bin/env python
# coding=utf8

import os
import sys
import yaml

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
    return
    
    session=database.getSession()
    stream=open(file,"r")
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

    session.close()

def load_special_conf():
    print "import special var"
    session=database.getSession()
    
    #添加特殊变量
    gv = GroupVar("all","","UHP_HOME",config.uhphome,0,"")
    session.merge(gv)
    gv = GroupVar("all","","TEMPLATE_DIR",config.template_dir,0,"")
    session.merge(gv)
    gv = GroupVar("all","","JAR_DIR",config.jar_dir,0,"")
    session.merge(gv)
    session.commit()

    session.close()

def ensureDir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print "usage: import_db_conf.py filename|all"
        sys.exit(1)

    ansible_var_dir=os.path.join(config.uhphome,"conf","ansible_var")
    if sys.argv[1] == "all" :
        print "load all var into db:"
        load_special_conf()
        for file in os.listdir(ansible_var_dir):
            if file.endswith("py") or file.endswith('.') :
                continue
            file_path=os.path.join(ansible_var_dir,file) 
            conf_to_db(file_path)
    else:
        file=sys.argv[1]
        if file.startswith('/'):
            if os.path.exists(file) :
                conf_to_db(file)
                sys.exit(0)
        else:
            may_file=os.path.join(ansible_var_dir,file)      
            if os.path.exists(may_file) :
                conf_to_db(may_file)
                sys.exit(0)
        print "ERROR: couldn't find the file"





