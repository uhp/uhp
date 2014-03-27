# -*- coding: UTF-8 -*- 

import json
import os.path, logging, sys
import config
import random
import commands

app_log = logging.getLogger("tornado.application")

def get_template_file(host,dir,file):
    temp=str(int(random.uniform(1000, 9999)))
    shell_command = "sh %s/ansible/service/script/get_template_file.sh %s %s %s %s " % (config.uhphome,host,dir,file,temp )
    app_log.info(shell_command)
    (status,output)=commands.getstatusoutput( shell_command )
    if status == 0 :
        dest = "/tmp/%s_%s_%s_%s" % (host,dir,file,temp) 
        app_log.info(dest)
        if os.path.exists(dest) and os.path.isfile(dest) :
            content=open(dest,"r").read()
            return (content,output)
    return ("",output)
    
def download_template_file(host,dir):
    temp=str(int(random.uniform(1000, 9999)))
    shell_command = "sh %s/ansible/service/script/download_template_file.sh %s %s %s " % (config.uhphome,host,dir,temp )
    app_log.info(shell_command)
    (status,output)=commands.getstatusoutput( shell_command )
    if status == 0 :
        dest = "/tmp/%s_%s_%s_%s" % (host,dir,file,temp) 
        app_log.info(dest)
        if os.path.exists(dest) and os.path.isfile(dest) :
            content=open(dest,"r").read()
            return (content,output)
    return ("",output)

if __name__ == '__main__':
    print get_template_file("hadoop1","hbase","hbase-env.sh.j2")
